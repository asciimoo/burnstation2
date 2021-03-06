#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ----------------------------------------------------------------------------
# pyjama - python jamendo audioplayer
# Copyright (c) 2009 Daniel Nögel
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# ----------------------------------------------------------------------------

# This Script was inspired by:
# http://pytute.blogspot.com/2007/04/python-plugin-system.html
# Over the time I made several changes which bloat the code a bit
# but gives the opportunity to influence the order of the plugins

## @package clPlugin
# Classes related to the pyjama plugin system

import os
import sys
import imp
#import clEvent
import traceback

import functions

# for the dialog
import gtk
import gobject
#from clWidgets import StockButton

### This might become a plugin class sometime
## this'd fix a lot of issues with the actual
## plugin system
#class Plugin(object):
#    def __init__(self):
#        self.name = "Basic Plugin"
#        self.description = "This is where every plugin comes from"
#        self.version = "0.1"
#        self.author = "Plugin Developer"
#        self.license = "GPLv3"
#        self.order = 100
#        self.__preferences = None

#    def set_preferences(self, opt):
#        if isinstance(opt, object):
#            self.__preferences = opt
#        else:
#            print "No valid preferences Box given"
#            return
#    def get_preferences(self):
#        return self.__preferences
#    preferences = property(get_preferences, set_preferences)
    

## Main Plugin managment -
# reads a list of plugins, generates plugin infos
# and imports and loads plugins
class Plugins():
    ## The Constructor
    # @param self The Object pointer
    # @param pyjama Reference to pyjama
    def __init__(self, pyjama):
        ## Reference to the pyjama object
        self.pyjama = pyjama

        ## Dictionary holding loaded plugins
        self.loaded = {}
        ## List holding ignored plugins
        self.ignored = []
        ## Dictionary of all plugins by name
        self.plugins_by_name = {}
        ## Pyjama's plugin directory
        self.pluginpath = os.path.join(os.path.dirname(imp.find_module("pyjama")[1]), "plugins/")
        ## TRUE if pyhama crashed last run and browser where blacklisted for that reason
        self.blacklisted_browser = False
        print("%s %s %s" % (30*"-", " <Plugins> ", 30*"-"))
        print ("Found Plugins in folder: %s" % self.pluginpath)
        #self.plugins = [fname for fname in sorted(os.listdir(self.pluginpath)) if os.path.isdir(os.path.join (self.pluginpath, fname)) and os.path.exists(os.path.join(self.pluginpath, fname, "%s.info" % fname))]

        # list of plugins that are blacklisted
        hardcoded_blacklist = ["PMC", "torrent-peer", "lastplayed", "catchERR", "bookmarks", "playlists"]


        #
        # Listing plugins not supported anymore
        #
        try:
            files = os.listdir(self.pluginpath)
            if ".py" in "".join(files):
                print "############################################################"
                print "#                                                          #"
                print "#  Pyjama uses a new plugin system. For this reason, all   #"
                print "#  files in your plugin folder can be deleted. Please      #"
                print "#  delete the files listed below to save your disk space.  #"
                print "#                                                          #"
                print "# !!The folders in the plugin dir should NOT be deleted!!  #"
                print "#                                                          #"
                print "############################################################"
            for dat in files:
                dat_pos = os.path.join(self.pluginpath, dat)
                if not os.path.isdir(dat_pos) and dat != "README":
                    print ("Don't know what to do with file %s" % dat_pos) 
#            print "\n\n\n"
        except:
            pass

        # Sine you cannot import from filenames
        # with python, I put the plugin path
        # at the first place in the pathlist
        # after all modules are imported, this
        # entry is removed again. (last line in this methode)
        sys.path.insert(0, self.pluginpath[:-1])

        ## List of plugin informations
        self.plugininfos = []

#        for plugin in self.plugins:
        for plugin in sorted(os.listdir(self.pluginpath)):
            # FIX: if autoload=false an plugin should not appear in the blacklist
            bl = self.pyjama.settings.get_value("PLUGINS", "blacklist", "")
            if os.path.exists(os.path.join(self.pluginpath, plugin, "%s.info" % plugin)) :
                item_infos = self.get_infos(plugin)
                if plugin in bl and item_infos["autoload"] == "false":
                    bl = bl.replace(plugin, "")
                    self.pyjama.settings.set_value("PLUGINS", "blacklist", bl)
                    print ("Removed %s from blacklist - autoload=false" % plugin)

            #~ print self.pyjama.settings.get_value("PYJAMA", "crashed", False)
            #~ print self.pyjama.check_another_instance_running() 
            #~ raw_input()
            if self.pyjama.settings.get_value("PYJAMA", "crashed", False) and (plugin == "mozplug" or plugin == "webkit-plugin") and self.pyjama.check_another_instance_running() != True:
                whitelist = self.pyjama.settings.get_value("PLUGINS", "whitelist", "")
                if plugin in whitelist:
                    print ("Pyjama crashed on last start - removing '%s' from whitelist again" % plugin)
                    whitelist = whitelist.replace(plugin, "")
                    self.pyjama.settings.set_value("PLUGINS", 'whitelist', whitelist)
                    self.blacklisted_browser = True

            if plugin in hardcoded_blacklist:
                print("!!! %s found in 'hardcoded_blacklist'" % plugin)
            elif "noplugins" in sys.argv and not plugin+"+" in sys.argv:
                pass
            elif os.path.isdir(os.path.join(self.pluginpath, plugin)) and os.path.exists(os.path.join(self.pluginpath, plugin, "%s.info" % plugin)) and not plugin+"-" in sys.argv and not plugin in self.pyjama.settings.get_value("PLUGINS", 'blacklist', "") or plugin+"+" in sys.argv:
                if item_infos['autoload'] == "false":
                    if plugin in self.pyjama.settings.get_value("PLUGINS", 'whitelist', "") or plugin+"+" in sys.argv:
                        self.plugininfos.append(item_infos)
                        self.plugins_by_name[plugin]= item_infos
                    else:
                        self.ignored.append(item_infos)
                        self.plugins_by_name[plugin]= item_infos 
                else:
                    self.plugininfos.append(item_infos)
                    self.plugins_by_name[plugin]= item_infos
            elif plugin+"-" in sys.argv or plugin in self.pyjama.settings.get_value("PLUGINS", 'blacklist'):
                try:
                    self.ignored.append(item_infos)
                    self.plugins_by_name[plugin]= item_infos
                except Exception, inst:
                    print "Plugin '%s' does not meet the specification" % plugin

        #
        # Sorting Plugins by Order
        #
        for x in range(len(self.plugininfos)):
            for plugin in range(0, len(self.plugininfos)-1):
                if int(self.plugininfos[plugin]['order']) > int(self.plugininfos[plugin+1]['order']):
                    self.plugininfos[plugin], self.plugininfos[plugin+1] = self.plugininfos[plugin+1], self.plugininfos[plugin]

        #
        # Importing all plugins
        #
        ## list of imported plugins
        self.imported_modules = []
        for plugin in self.plugininfos:
            name = plugin['name']
            filename = plugin['filename']
            order = plugin['order']
            version = plugin['version']
            if not name+"-" in sys.argv and not name in self.pyjama.settings.get_value("PLUGINS", 'blacklist') or name+"+" in sys.argv:
                try:
                    mod = __import__ (plugin['filename'])
#                    if not self.pluginpath in mod.__file__:
#                        print "Error"
                    self.imported_modules.append({'module':mod, 'name':name, 'order':order, 'version':version})
                except Exception:
                    print traceback.format_exc()
                    print "Error importing Plugin %s (%s)" % (name, filename)
            else:
                print "Plugin %s ignored" % name

        #
        # Calling main() for each plugin
        #
        ev = self.pyjama.Events
        for plugin in self.imported_modules:
            module = plugin['module']
            name = plugin['name']
            order = plugin['order']
            version = plugin['version']
            mod_name = module.__name__
            try:
                self.loaded[mod_name] = module.main(self.pyjama)
                ev.raise_event('pluginloaded', name=name, version=version, order=order, mod_name=mod_name)
            except:
                print traceback.format_exc()
                print "Error calling Plugin %s (%s)" % (name, mod_name)
                print mod.__file__

        # removing plugin dir form the pathlist
        sys.path.pop(0)
        print("%s %s %s" % (30*"-", " </Plugins> ", 30*"-"))

    ## Reads out .info file of a plugin
    # @param self The Object pointer
    # @param plugin The plugin's filename as string
    # @return dictionary
    def get_infos(self, plugin):
        fh = open(os.path.join(self.pluginpath, plugin, "%s.info" % plugin))
        content = fh.read()
        fh.close()
        infos = content.split("\n")

        item_infos = {}
        item_infos['filename'] = plugin
        last_line = None
        
        item_infos['name'], item_infos['version'], item_infos['order'], item_infos['author'], item_infos['homepage'], item_infos['description'], item_infos['copyright'], item_infos['license'], item_infos['autoload'] = "unnamed plugin", "0.1", "100", "", "", "", "", "", "true"
        for line in infos:
            cur_item = line[:line.find("=")].strip().lower()
            if cur_item == "name":
                #last_line = "name"
                item_infos['name'] = line[line.find("=")+1:].strip()
            elif cur_item == "version": 
                #last_line = "version"
                item_infos['version'] = line[line.find("=")+1:].strip()
            elif cur_item == "order":
                #last_line = "order"
                item_infos['order'] = line[line.find("=")+1:].strip()
            elif cur_item == "author":
                #last_line = "author"
                item_infos['author'] = line[line.find("=")+1:].strip()
            elif cur_item == "homepage":
                #last_line = "homepage"
                item_infos['homepage'] = line[line.find("=")+1:].strip()
            elif cur_item == "copyright":
                #last_line = "copyright"
                item_infos['copyright'] = line[line.find("=")+1:].strip()
            elif cur_item == "autoload":
                item_infos['autoload'] = line[line.find("=")+1:].strip()
            elif cur_item == "license":
                item_infos['license'] = line[line.find("=")+1:].strip()
            elif cur_item == "description":
                last_line = "description"
                item_infos['description'] = line[line.find("=")+1:].strip()
            elif last_line is not None and line!="":
                item_infos[last_line] += "\n%s" % line.strip()
        return item_infos

(
    COLUMN_SELECTED,
    COLUMN_NAME,
    COLUMN_ID
) = range(3)

## This Plugin Dialog holds a list of all plugins
# in order to give the user the opportunity to
# choose which plugin is going to be loaded next
# time. Furthermore it shows some basic informations
# for each plugin as well as a preference dialog
# if the plugin has one.
class PluginDialog(gtk.Dialog):
    ## The Constructor
    # @param self The Object pointer
    # @param pyjama Reference to pyjama
    def __init__(self, pyjama):
        ## Holds a reference to pyjama
        self.pyjama = pyjama
        
        gtk.Dialog.__init__(self, "", pyjama.window)

        self.set_modal(True)
        self.set_title(_("Plugins"))
        self.set_border_width(5)
        self.set_size_request(500, 400)
        self.set_resizable(False)

        label = gtk.Label(_("Deselect Plugins you don't want to be started with pyjama."))
        label.set_line_wrap(True)
        label.set_single_line_mode(False)
        self.vbox.pack_start(label, expand=False, fill=True)

        hbox = gtk.HBox()
        self.vbox.pack_start(hbox)

        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        hbox.pack_start(sw, True, True)

        ## The model holding all plugins
        self.model = self.__create_model()

        # create tree view
        self.__treeview = gtk.TreeView(self.model)
        self.__treeview.set_rules_hint(True)
        self.__treeview.set_search_column(COLUMN_NAME)
        selection = self.__treeview.get_selection()
        selection.connect("changed", self.cb_treeview_selection_changed)

        sw.add(self.__treeview)

        # add columns
        self.__add_columns(self.__treeview)

        # some buttons for our plugins
        buttonbox = gtk.VButtonBox()
        buttonbox.set_layout(gtk.BUTTONBOX_START) #gtk.BUTTONBOX_EDGE #SPREAD
        buttonbox.set_spacing(30)
        hbox.pack_end(buttonbox, False, True)
        bInfos = gtk.Button("", gtk.STOCK_ABOUT)#StockButton(gtk.STOCK_ABOUT, gtk.ICON_SIZE_DND, _("More Infos"))
        bInfos.set_property("image-position", gtk.POS_TOP)
        bInfos.connect("clicked", self.cb_bInfos_clicked)
        buttonbox.pack_start(bInfos, False, True)
        self.__bConfigure = gtk.Button("", gtk.STOCK_PREFERENCES)
        self.__bConfigure.set_property("image-position", gtk.POS_TOP)
        self.__bConfigure.connect("clicked", self.cb_bConfigure_clicked)
        self.__bConfigure.set_sensitive(False)
        buttonbox.pack_start(self.__bConfigure, False, True)
        buttonbox.show_all()

        self.add_button(gtk.STOCK_CANCEL, -1)
        self.add_button(gtk.STOCK_OK, 1)

        self.populate_list()

        self.show_all()

    ## Treeview Selection Callback
    # called whenever the selection of the treeview changes
    # @param self The Object pointer
    # @param treeselection The treeview's treeselection
    # @return None
    def cb_treeview_selection_changed(self, treeselection):

        model, iter = treeselection.get_selected()
    
        if iter is not None:
            idstr = model.get(iter, 2)[0]
            plugin = self.get_plugin_by_filename(idstr)
            if plugin is not None:
                self.__bConfigure.set_sensitive(self.pyjama.preferences.has_preferences(idstr))

    ## Info Callback
    # called when the info button is pressed
    # @param self The Object pointer
    # @param widget The Info Button widget
    # @return None
    def cb_bInfos_clicked(self, widget):
        selection = self.__treeview.get_selection()
        model, iter = selection.get_selected()
    
        if iter is not None:
            idstr = model.get(iter, 2)[0]
            plugin = self.get_plugin_by_filename(idstr)
            if plugin is not None:
                icon = os.path.join(functions.install_dir(), "plugins", idstr, "%s.png" % idstr)
                if os.path.exists(icon):
                    pb = gtk.gdk.pixbuf_new_from_file(icon)
                else:
                    pb = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(functions.install_dir(), "images", "plugin.png"), 92, 92)
                dialog = gtk.AboutDialog()
                dialog.set_name(plugin['name'])
                dialog.set_logo(pb)
                dialog.set_version(plugin['version'])
                if plugin['copyright'] != "": 
                    dialog.set_copyright(plugin['copyright'])
                dialog.set_comments(plugin['description'])
                if plugin['license'] != "": 
                    dialog.set_license(functions.license2text(plugin['license']))
                if plugin['homepage'] != "": 
                    dialog.set_website(plugin['homepage'])
                dialog.set_authors(plugin['author'].split(","))
                dialog.set_logo(None)
                dialog.run()
                dialog.set_modal(True)
                dialog.destroy()

    ## Returns plugin infos for a given plugin filename
    # @param self The Object pointer
    # @param filename A plugin's filename
    # @return Dictionary holdingplugin infos
    def get_plugin_by_filename(self, filename):
        if filename in self.pyjama.plugins.plugins_by_name:
            return self.pyjama.plugins.plugins_by_name[filename]
#        for plugin in self.pyjama.plugins.plugininfos:
#            if plugin['filename'] == filename: return plugin
#        for plugin in self.pyjama.plugins.ignored:
#            if plugin['filename'] == filename: return plugin
#        return None

    ## Configure Callback
    # called when the configure button is pressed
    # @param self The Object pointer
    # @param widget The Configure Button widget
    # @return None
    def cb_bConfigure_clicked(self, widget):
        selection = self.__treeview.get_selection()
        model, iter = selection.get_selected()
    
        if iter is not None:
            idstr = model.get(iter, 2)[0]
            plugin = self.get_plugin_by_filename(idstr)
            if plugin is not None:
                if self.pyjama.preferences.has_preferences(idstr):
                    if not plugin['filename'] in self.pyjama.plugins.loaded:
                        dia = gtk.MessageDialog(self.pyjama.window, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, _("This plugin was not loaded yet.\nIf you want to configure it, please check it and restart Pyjama."))
                        dia.run()
                        dia.destroy()
                    else:
                        self.pyjama.show_preferences(name=idstr)

    def __create_model(self):

        # create list store
        model = gtk.ListStore(
            gobject.TYPE_BOOLEAN,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING
       )
        return model

    def __add_columns(self, treeview):
        model = treeview.get_model()

        # column for select toggles
        renderer = gtk.CellRendererToggle()
        renderer.connect('toggled', self.select_toggled, model)
        column = gtk.TreeViewColumn(_('Load'), renderer, active=COLUMN_SELECTED)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(50)
        treeview.append_column(column)


        # column for name
        column = gtk.TreeViewColumn('Name', gtk.CellRendererText(), text=COLUMN_NAME)
        column.set_sort_column_id(COLUMN_NAME)
        treeview.append_column(column)

    ## Populates the treemodel
    # Addes all loaded and ignored plugins to the treemodel
    # @param self The Object pointer
    # @return liststore
    def populate_list(self):
        lstore = self.__treeview.get_model()
        lstore.clear()

        for plugin in self.pyjama.plugins.plugininfos:
            name = plugin['name']
            idstr = plugin['filename']
            description = plugin['description']
            if len(description)>40:description=description[:40]+"..."
            iter = lstore.append()
            selected = True
            if plugin['filename'] in self.pyjama.settings.get_value("PLUGINS", "blacklist", ""):
                selected = False
            lstore.set(iter,
                COLUMN_SELECTED, selected,
                COLUMN_NAME, "%s\n%s" % (name, description),
                COLUMN_ID, idstr
                )

        for plugin in self.pyjama.plugins.ignored:
            name = plugin['name']
            idstr = plugin['filename']
            description = plugin['description']
            if len(description)>40:description=description[:40]+"..."
            iter = lstore.append()
            selected = False
            if not plugin['filename'] in self.pyjama.settings.get_value("PLUGINS", "blacklist", "") and not plugin['filename']+"-" in sys.argv:
                if plugin['autoload'] == "true" or plugin['filename'] in self.pyjama.settings.get_value("PLUGINS", "whitelist", ""):
                    selected = True
            lstore.set(iter,
                COLUMN_SELECTED, selected,
                COLUMN_NAME, "%s\n%s" % (name, description),
                COLUMN_ID, idstr
                )

        lstore.set_sort_column_id(COLUMN_NAME,gtk.SORT_ASCENDING)  

        return lstore

    ## Toggle Callback
    # called when a plugin is checked / unchecked
    # @param self The Object pointer
    # @param cell  
    # @param path Path of the toggled column
    # @param model Model
    # @return None
    def select_toggled(self, cell, path, model):
        # get toggled iter
        iter = model.get_iter((int(path),))
        fixed = model.get_value(iter, COLUMN_SELECTED)

        # do something with the value
        fixed = not fixed

        # set new value
        model.set(iter, COLUMN_SELECTED, fixed)

## Runs and evaluates the PluginDialog Class
# @param pyjama Pyjama Object Reference
# @return None
def ShowPluginsDialog(pyjama):
    dialog = PluginDialog(pyjama)
    model = dialog.model
    result = dialog.run()
    dialog.destroy()
    if result == 1: # delete
        blacklist = pyjama.settings.get_value("PLUGINS", 'blacklist', "")
        whitelist = pyjama.settings.get_value("PLUGINS", "whitelist", "")
        changes = None
        iter = model.get_iter_first()

        activated_browser = ""
        
        while iter:
            checked, name, idstr = ( model.get(iter, 0, 1, 2) )
            if checked == True:
                if pyjama.plugins.plugins_by_name[idstr]['autoload'] == "false" and not idstr in whitelist:
                    whitelist += " %s" % idstr
                    changes = True
                    print "added %s to whitelist" % idstr
                    if idstr == "mozplug":
                        activated_browser += "mozplug"
                    elif idstr == "webkit-plugin":
                        activated_browser += "webkit-plugin"
                elif idstr in blacklist:
                    blacklist = blacklist.replace(idstr, "")
                    changes = True
                    print "removed %s from blacklist" % idstr
            else:
                if pyjama.plugins.plugins_by_name[idstr]['autoload'] == "false":
                    if idstr in whitelist:
                        whitelist = whitelist.replace(idstr, "")
                        changes = True
                        print "removed %s from whitelist" % idstr      
                elif not idstr in blacklist:
                    changes = True
                    blacklist += " %s" % idstr
                    print "added %s to blacklist" % idstr
            iter = model.iter_next(iter)
        pyjama.settings.set_value("PLUGINS", 'blacklist', blacklist)
        pyjama.settings.set_value("PLUGINS", 'whitelist', whitelist)
        if changes is True:
            dia = gtk.MessageDialog(pyjama.window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, _("You (un)selected some plugins.\nPlease note, that you will need to restart pyjama\nto let the changes take effect."))
            dia.run()
            dia.destroy()
#            if activated_browser != "":
#                txt = _("You selected '<b>%s</b>' as an integrated browser.\nPlease notice: Both browser plugins might not work on some systems:\n\n<b>Mozplug</b> crashes pyjama on startup on some systems.\nWith <b>webkit-plugin</b> pyjama might hang from time to time.\n\nDelete ~/.pyjama/pyjama.cfg if errors occure." % activated_browser)
#                pyjama.info("Warning:", txt)
#                #~ dia = gtk.MessageDialog(pyjama.window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, txt)
#                #~ dia.run()
#                #~ dia.destroy()
            
