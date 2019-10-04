#! /usr/bin/python
# -*- coding=utf-8 -*-

"""
    This file is part of Torrent Search.
    
    Torrent Search is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Torrent Search is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import gtk, os, time, torrentApps, libxml2, webbrowser, _codecs
try:
   import gconf
   GCONF_SUPPORT=True
except:
   GCONF_SUPPORT=False
from informations import *
from constants import *

CONFIG_KEYS={
"torrent_mode":("torrent_mode","string","save_in_folder"),
"torrent_standard_app":("torrent_standard_app","string",""),
"torrent_custom_app":("torrent_custom_app","string",""),
"torrent_save_folder":("torrent_save_folder","string",os.getcwd()),
"window_x":("window_pos/x","int",100),
"window_y":("window_pos/y","int",100),
"window_width":("window_pos/width","int",640),
"window_height":("window_pos/height","int",480),
"config_dialog_width":("window_pos/config_dialog_width","int",1),
"config_dialog_height":("window_pos/config_dialog_height","int",400),
"window_maximized":("window_pos/maximized","bool",False),
"search_history":("search_history","string_list",[]),
"disabled_plugins":("disabled_plugins","string_list",[]),
"hide_zero_seeders":("hide_zero_seeders","bool",False),
"min_size_enable":("min_size_enable","bool",False),
"max_size_enable":("max_size_enable","bool",False),
"min_size_value":("min_size_value","int",50),
"max_size_value":("max_size_value","int",200),
"min_size_unit":("min_size_unit","string","MB"),
"max_size_unit":("max_size_unit","string","MB"),
"only_exact_phrase":("only_exact_phrase","bool",False),
"only_all_words":("only_all_words","bool",False),
"dont_show_new_version_again":("dont_show_new_version_again","bool",False),
"last_version_notified":("last_version_notified","string",""),
"name_does_not_contain":("name_does_not_contain","string",""),
"name_contains":("name_contains","string",""),
"download_manager_width":("download_manager_width","int",450),
"search_options_expanded":("search_options_expanded","bool",False),
"max_sim_downloads":("max_sim_downloads","int",3),
"check_plugins_updates":("check_plugins_updates","bool",True),
"filter_duplicates":("filter_duplicates","bool",False),
"converted_from_gconf":("converted_from_gconf","bool",False),
"confirmed_plugins":("confirmed_plugins","string_list",[]),
"after_date_enable":("after_date_enable","bool",False),
"before_date_enable":("before_date_enable","bool",False),
"after_date":("after_date","string",""),
"before_date":("before_date","string",""),
"category":("category","object",None),
"stop_search_when_nb_results_reaches_enabled":("stop_search_when_nb_results_reaches_enabled","bool",False),
"stop_search_when_nb_results_reaches_value":("stop_search_when_nb_results_reaches_value","int",100),
"stop_search_when_nb_plugin_results_reaches_enabled":("stop_search_when_nb_plugin_results_reaches_enabled","bool",True),
"stop_search_when_nb_plugin_results_reaches_value":("stop_search_when_nb_plugin_results_reaches_value","int",100),
"sort_column":("sort_column","int",-1),
"sort_desc":("sort_desc","bool",False),
}
#TODO1: Add option to limit the number of comments to load

class AppConfig(object):
   def __init__(self,app):
      self._app=app
      self._values={}
      self._listeners=[]
      for key in CONFIG_KEYS:
         real_key,keytype,default=CONFIG_KEYS[key]
         self._values[key]=default
      if GCONF_SUPPORT and not self._values["converted_from_gconf"]:
         self._convert_from_gconf()
      self._load()
   def _convert_from_gconf(self):
      gclient=gconf.client_get_default()
      for key in CONFIG_KEYS:
         real_key,keytype,default=CONFIG_KEYS[key]
         value=gclient.get_without_default("/apps/%s/%s"%(UNIXNAME,real_key))
         if value==None:
            self._values[key]=default
         else:
            if keytype=="int":
               self._values[key]=value.get_int()
            if keytype=="string":
               self._values[key]=value.get_string()
            if keytype=="bool":
               self._values[key]=value.get_bool()
            if keytype=="string_list":
               res=list(value.get_list(gconf.VALUE_STRING))
               for i in range(len(res)):
                  res[i]=res[i].get_string()
               self._values[key]=res
   def _notify(self,key):
      for i in self._listeners:
         i(key,self[key])
   def register_listener(self,listener):
      self._listeners.append(listener)
   def __getitem__(self,key):
      return self._values[key]
   def __setitem__(self,key,value):
      real_key,keytype,default=CONFIG_KEYS[key]
      if value!=self[key] or keytype=="string_list":
         self._values[key]=value
         self._save()
         self._notify(key)
   def __call__(self,key,value):
      self[key]=value
   def _save(self):
      d=libxml2.newDoc("1.0")
      root=libxml2.newNode("torrent-search-config")
      d.setRootElement(root)
      for key in CONFIG_KEYS:
         real_key,keytype,default=CONFIG_KEYS[key]
         if keytype=="string":
            root.newTextChild(None, key, self[key]).setProp('type','string')
         if keytype=="int":
            root.newTextChild(None, key, str(self[key])).setProp('type','int')
         if keytype=="bool":
            if self[key]:
               root.newTextChild(None, key, "true").setProp('type','bool')
            else:
               root.newTextChild(None, key, "false").setProp('type','bool')
         if keytype=="string_list":
            node=libxml2.newNode(key)
            node.setProp('type','string_list')
            root.addChild(node)
            for item in self[key]:
               node.newTextChild(None,"item",item)
      if not os.path.exists(APPDATA_PATH):
         self._app.rec_mkdir(APPDATA_PATH)
      filename=os.path.join(APPDATA_PATH,"config.xml")
      d.saveFormatFileEnc(filename,"utf-8",True)
   def _load(self):
      try:
         filename=os.path.join(APPDATA_PATH,"config.xml")
         d=libxml2.parseFile(filename)
         root=d.getRootElement()
         child=root.children
         while child:
            if child.type=="element":
               if child.prop('type')=="string":
                  self._values[child.name]=_codecs.utf_8_decode(child.getContent())[0]
               if child.prop('type')=="int":
                  self._values[child.name]=int(child.getContent())
               if child.prop('type')=="bool":
                  self._values[child.name]=(child.getContent()=="true")
               if child.prop('type')=="string_list":
                  res=[]
                  item=child.children
                  while item:
                     if item.name=="item":
                        res.append(_codecs.utf_8_decode(item.getContent())[0])
                     item=item.next
                  self._values[child.name]=res
            child=child.next
      except:
         pass

class GeneralPreferencesPage(gtk.VBox):
   def __init__(self,app):
      self._app=app
      gtk.VBox.__init__(self)
      self.set_border_width(5)
      self.set_spacing(10)
      f=gtk.Frame()
      l=gtk.Label()
      l.set_markup("<b>%s</b>"%_("TORRENT_FILES"))
      f.set_label_widget(l)
      self.pack_start(f,False,False)
      table=gtk.Table()
      table.set_border_width(5)
      table.set_col_spacings(10)
      table.set_row_spacings(10)
      f.add(table)
      self.torrent_save_in_folder_rb=gtk.RadioButton(None,_("SAVE_IN_FOLDER"))
      table.attach(self.torrent_save_in_folder_rb,0,1,0,1,xoptions=gtk.FILL,yoptions=0)
      self.torrent_save_in_folder_fs=gtk.FileChooserButton(_("SELECT_FOLDER"))
      self.torrent_save_in_folder_fs.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
      table.attach(self.torrent_save_in_folder_fs,1,2,0,1,yoptions=0)
      self.torrent_save_in_folder_fs.set_sensitive(False)
      self.torrent_use_standard_app_rb=gtk.RadioButton(self.torrent_save_in_folder_rb,_("USE_STANDARD_APP"))
      table.attach(self.torrent_use_standard_app_rb,0,1,1,2,xoptions=gtk.FILL,yoptions=0)
      self.torrent_use_standard_app_cb=gtk.ComboBox()
      table.attach(self.torrent_use_standard_app_cb,1,2,1,2,yoptions=0)
      self.torrent_use_standard_app_cb_ls=gtk.ListStore(str,str)
      self.torrent_use_standard_app_cb.set_model(self.torrent_use_standard_app_cb_ls)
      r=gtk.CellRendererText()
      self.torrent_use_standard_app_cb.pack_start(r)
      self.torrent_use_standard_app_cb.add_attribute(r,"text",1)
      self.torrent_use_standard_app_cb.set_sensitive(False)
      for appID,label,command in torrentApps.listApps():
         self.torrent_use_standard_app_cb_ls.append([appID,label])
      for i in range(len(self.torrent_use_standard_app_cb_ls)):
         if self.torrent_use_standard_app_cb_ls[i][0]==app.config["torrent_standard_app"]:
            self.torrent_use_standard_app_cb.set_active(i)
      self.torrent_use_custom_app_rb=gtk.RadioButton(self.torrent_save_in_folder_rb,_("USE_CUSTOM_APP"))
      table.attach(self.torrent_use_custom_app_rb,0,1,2,3,xoptions=gtk.FILL,yoptions=0)
      self.torrent_use_custom_app_entry=gtk.Entry()
      table.attach(self.torrent_use_custom_app_entry,1,2,2,3,xoptions=gtk.FILL,yoptions=0)
      self.torrent_use_custom_app_entry.set_text(app.config['torrent_custom_app'])
      self.torrent_use_custom_app_entry.set_sensitive(False)
      if app.config["torrent_mode"]=="save_in_folder":
         self.torrent_save_in_folder_rb.set_active(True)
         self.torrent_save_in_folder_fs.set_sensitive(True)
      elif app.config["torrent_mode"]=="use_standard_app":
         self.torrent_use_standard_app_rb.set_active(True)
         self.torrent_use_standard_app_cb.set_sensitive(True)
      else:
         self.torrent_use_custom_app_rb.set_active(True)
         self.torrent_use_custom_app_entry.set_sensitive(True)
      for i in [self.torrent_save_in_folder_rb,self.torrent_use_standard_app_rb,self.torrent_use_custom_app_rb]:
         i.connect('toggled',self.on_torrent_mode_changed)
      self.torrent_use_standard_app_cb.connect('changed',self.on_torrent_standard_app_changed)
      self.torrent_use_custom_app_entry.connect('changed',self.on_torrent_custom_app_changed)
      if os.path.exists(app.config['torrent_save_folder']) and os.path.isdir(app.config['torrent_save_folder']):
         self.torrent_save_in_folder_fs.set_current_folder(app.config['torrent_save_folder'])
      else:
         if PLATFORM=="unix":
            self.torrent_save_in_folder_fs.set_current_folder(os.getenv('HOME'))
            app.config['torrent_save_folder']=os.getenv('HOME')
         else:
            self.torrent_save_in_folder_fs.set_current_folder(os.getenv('APPDATA'))
            app.config['torrent_save_folder']=os.getenv('APPDATA')
      f=gtk.Frame()
      l=gtk.Label()
      l.set_markup("<b>%s</b>"%_("PLUGINS_UPDATES"))
      f.set_label_widget(l)
      self.pack_start(f,False,False)
      vbox=gtk.VBox()
      f.add(vbox)
      vbox.set_border_width(5)
      vbox.set_spacing(10)
      self.check_plugins_updates=gtk.CheckButton(_("CHECK_PLUGINS_UPDATES"))
      vbox.pack_start(self.check_plugins_updates,False,False)
      self.check_plugins_updates.set_active(app.config["check_plugins_updates"])
      self.check_plugins_updates.connect("toggled",self.on_check_plugins_updates_toggled)
      b=gtk.Button(_("CHECK_NOW"))
      img=gtk.Image()
      img.set_from_stock(gtk.STOCK_REFRESH,gtk.ICON_SIZE_BUTTON)
      b.set_image(img)
      vbox.pack_start(b,False,False)
      b.connect('clicked',lambda w:self._app.check_plugin_updates())
      f=gtk.Frame()
      l=gtk.Label()
      l.set_markup("<b>%s</b>"%_("SEARCH_OPTIONS"))
      f.set_label_widget(l)
      self.pack_start(f,False,False)
      table=gtk.Table()
      f.add(table)
      table.set_border_width(5)
      table.set_col_spacings(10)
      table.set_row_spacings(10)
      self.stop_search_when_nb_results_reaches_cb=gtk.CheckButton(_("STOP_SEARCH_WHEN_NB_RESULTS_REACHES"))
      self.stop_search_when_nb_results_reaches_cb.set_active(app.config["stop_search_when_nb_results_reaches_enabled"])
      table.attach(self.stop_search_when_nb_results_reaches_cb,0,1,0,1,xoptions=gtk.FILL,yoptions=0)
      self.stop_search_when_nb_results_reaches_nb=gtk.SpinButton()
      self.stop_search_when_nb_results_reaches_nb.set_range(10,10000)
      self.stop_search_when_nb_results_reaches_nb.set_increments(10,100)
      table.attach(self.stop_search_when_nb_results_reaches_nb,1,2,0,1,yoptions=0)
      self.stop_search_when_nb_results_reaches_cb.connect('toggled',self.on_stop_search_when_nb_results_reaches_cb_toggled)
      self.stop_search_when_nb_results_reaches_nb.connect('changed',self.on_stop_search_when_nb_results_reaches_nb_changed)
      self.stop_search_when_nb_results_reaches_nb.set_value(app.config["stop_search_when_nb_results_reaches_value"])
   def on_stop_search_when_nb_results_reaches_cb_toggled(self,widget):
      self._app.config["stop_search_when_nb_results_reaches_enabled"]=widget.get_active()
   def on_stop_search_when_nb_results_reaches_nb_changed(self,widget):
      self._app.config["stop_search_when_nb_results_reaches_value"]=int(widget.get_value())
   def on_check_plugins_updates_toggled(self,widget):
      self._app.config["check_plugins_updates"]=widget.get_active()
   def on_hide_zero_seeders_toggled(self,widget):
      self._app.config["hide_zero_seeders"]=widget.get_active()
   def on_torrent_custom_app_changed(self,widget):
      self._app.config['torrent_custom_app']=widget.get_text()
   def on_torrent_standard_app_changed(self,widget):
      self._app.config["torrent_standard_app"]=self.torrent_use_standard_app_cb_ls[widget.get_active()][0]
   def on_torrent_mode_changed(self,widget):
      self.torrent_save_in_folder_fs.set_sensitive(False)
      self.torrent_use_standard_app_cb.set_sensitive(False)
      self.torrent_use_custom_app_entry.set_sensitive(False)
      if self.torrent_save_in_folder_rb.get_active():
         self._app.config["torrent_mode"]="save_in_folder"
         self.torrent_save_in_folder_fs.set_sensitive(True)
      elif self.torrent_use_standard_app_rb.get_active():
         self._app.config["torrent_mode"]="use_standard_app"
         self.torrent_use_standard_app_cb.set_sensitive(True)
      else:
         self._app.config["torrent_mode"]="use_custom_app"
         self.torrent_use_custom_app_entry.set_sensitive(True)

class PluginsPreferencesPage(gtk.ScrolledWindow):
   def __init__(self,app):
      gtk.ScrolledWindow.__init__(self)
      self.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
      self.tv=gtk.TreeView()
      self.tv.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
      self.add(self.tv)
      self.lb=gtk.ListStore(object,str)
      self.tv.set_model(self.lb)
      r=gtk.CellRendererText()
      col=gtk.TreeViewColumn(_("PLUGIN_NAME"),r,text=1)
      self.tv.append_column(col)
      r=gtk.CellRendererToggle()
      col=gtk.TreeViewColumn(_("ENABLE"),r)
      self.tv.append_column(col)
      r.set_property("activatable", True)
      r.connect('toggled',self._on_enabled_toggled)
      col.set_cell_data_func(r,self._enabled_data_func)
      r=gtk.CellRendererText()
      col=gtk.TreeViewColumn(_("LAST_UPDATE"),r)
      self.tv.append_column(col)
      col.set_cell_data_func(r,self._last_update_data_func)
      r=gtk.CellRendererText()
      col=gtk.TreeViewColumn(_("URL"),r)
      self.tv.append_column(col)
      col.set_cell_data_func(r,self._url_data_func)
      r=gtk.CellRendererText()
      col=gtk.TreeViewColumn(_("AUTHOR"),r)
      self.tv.append_column(col)
      col.set_cell_data_func(r,self._author_data_func)
      l=[]
      for i in app.search_plugins:
         l.append(i)
      l.sort(lambda a,b:cmp(a.TITLE.lower(),b.TITLE.lower()))
      for i in l:
         self.lb.append((i,i.TITLE))
      self.tv.connect('button_press_event',self.on_button_press_event)
      self.tv.connect('motion_notify_event',self.on_motion_notify_event)
   def on_motion_notify_event(self,widget,event):
      data=widget.get_path_at_pos(int(event.x),int(event.y))
      if data:
         path,column,x,y=data
         if column.get_property('title')==_("URL"):
            self.tv.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
            return
      self.tv.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.ARROW))
   def _url_data_func(self,column,cell,model,iter):
      plugin=model.get_value(iter,0)
      cell.set_property('markup',"<span color='#0000FF'><u>%s</u></span>"%plugin.website_url)
   def enable_items(self,paths):
      for i in paths:
         self.lb[i][0].enabled=True
   def disable_items(self,paths):
      for i in paths:
         self.lb[i][0].enabled=False
   def on_button_press_event(self,widget,event):
      if event.button==1:
         data=widget.get_path_at_pos(int(event.x),int(event.y))
         if data:
            path,column,x,y=data
            if column.get_property('title')==_("URL"):
               iter=self.lb.get_iter(path)
               plugin=self.lb.get_value(iter,0)
               webbrowser.open(plugin.website_url)
               return True
      if event.button==3:
         data=widget.get_path_at_pos(int(event.x),int(event.y))
         res=False
         if data:
            sel=[]
            for i in self.tv.get_selection().get_selected_rows()[1]:
               sel.append(i[0])
            path,col,cx,cy=data
            if path[0] in sel:
               res=True
            else:
               sel=[path[0]]
            if sel:
               m=gtk.Menu()
               item=gtk.MenuItem(_("ENABLE"))
               m.add(item)
               item.connect('activate',lambda w,s:self.enable_items(s),sel)
               item=gtk.MenuItem(_("DISABLE"))
               m.add(item)
               item.connect('activate',lambda w,s:self.disable_items(s),sel)
               m.show_all()
               m.popup(None,None,None,3,event.time)
         return res
   def _last_update_data_func(self,column,cell,model,iter):
      plugin=model.get_value(iter,0)
      try:
         cell.set_property("text",time.strftime("%c",time.strptime(plugin.RELEASED_TIME,"%Y-%m-%d %H:%M:%S")))
      except:
         cell.set_property("text",_("UNKNOWN"))
   def _author_data_func(self,column,cell,model,iter):
      plugin=model.get_value(iter,0)
      cell.set_property('text',plugin.AUTHOR)
   def _on_enabled_toggled(self,cell,path):
      iter=self.lb.get_iter(path)
      plugin=self.lb.get_value(iter,0)
      plugin.enabled=not plugin.enabled
   def _enabled_data_func(self,column,cell,model,iter):
      plugin=model.get_value(iter,0)
      cell.set_property('active',plugin.enabled)

class PreferencesDialog(gtk.Dialog):
   def __init__(self,app):
      self._app=app
      self._accel_group=gtk.AccelGroup()
      gtk.Dialog.__init__(self,_("PREFERENCES"),app)
      self.resize(app.config['config_dialog_width'],app.config['config_dialog_height'])
      self.add_accel_group(self._accel_group)
      self.add_button(gtk.STOCK_CLOSE,gtk.RESPONSE_CLOSE)
      self.help_button=gtk.Button(stock=gtk.STOCK_HELP)
      self.help_button.add_accelerator("clicked",self._accel_group,gtk.keysyms.F1,0,gtk.ACCEL_VISIBLE)
      self.action_area.add(self.help_button)
      self.action_area.set_child_secondary(self.help_button,True)
      self.set_icon_name("gtk-preferences")
      notebook=gtk.Notebook()
      notebook.set_border_width(5)
      self.child.add(notebook)
      self.general_page=GeneralPreferencesPage(app)
      notebook.append_page(self.general_page,gtk.Label(_('GENERAL_OPTIONS')))
      notebook.append_page(PluginsPreferencesPage(app),gtk.Label(_('SEARCH_PLUGINS')))
      self.help_button.connect("clicked",lambda w,n:self.show_help(n),notebook)
      self.connect('configure_event',self._on_configure_event)
   def _on_configure_event(self,window,event):
      if self.window:
         self._app.config["config_dialog_width"]=event.width
         self._app.config["config_dialog_height"]=event.height
   def show_help(self,notebook):
      item=["preferences-general","preferences-plugins"][notebook.get_current_page()]
      self._app.show_help(item)
   def run(self):
      self.show_all()
      gtk.Dialog.run(self)
      self._app.config['torrent_save_folder']=self.general_page.torrent_save_in_folder_fs.get_filename()
      self.hide()
      
      
