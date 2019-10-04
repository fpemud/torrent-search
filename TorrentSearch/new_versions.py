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

import gtk, thread, gobject, httplib2, urllib

class VersionNoFilesDialog(gtk.Dialog):
   def __init__(self,app,url):
      gtk.Dialog.__init__(self,_("ERROR"),app)
      self.add_button(gtk.STOCK_CLOSE,gtk.RESPONSE_CLOSE)
      vbox=gtk.VBox()
      vbox.set_border_width(5)
      vbox.set_spacing(10)
      self.child.add(vbox)
      hbox=gtk.HBox()
      vbox.pack_start(hbox)
      hbox.set_spacing(10)
      img=gtk.Image()
      img.set_from_stock(gtk.STOCK_DIALOG_ERROR,gtk.ICON_SIZE_DIALOG)
      hbox.pack_start(img,False,False)
      svbox=gtk.VBox()
      svbox.set_spacing(10)
      hbox.pack_start(svbox)
      self.label=gtk.Label()
      self.label.set_markup("<span size='large'><b>%s</b></span>"%_("NO_DOWNLOAD_FILES"))
      self.label.set_alignment(0,0.5)
      svbox.pack_start(self.label,False,False)
      self.sublabel=gtk.Label(_("GO_TO_DOWNLOAD_LINK"))
      svbox.pack_start(self.sublabel,False,False)
      self.sublabel.set_alignment(0,0.5)
      self.urllabel=gtk.LinkButton(url,url)
      svbox.pack_start(self.urllabel,False,False)
   def run(self):
      self.show_all()
      gtk.Dialog.run(self)
      self.hide()

class VersionDownloadErrorDialog(gtk.Dialog):
   def __init__(self,app,url):
      gtk.Dialog.__init__(self,_("ERROR"),app)
      self.add_button(gtk.STOCK_CLOSE,gtk.RESPONSE_CLOSE)
      vbox=gtk.VBox()
      vbox.set_border_width(5)
      vbox.set_spacing(10)
      self.child.add(vbox)
      hbox=gtk.HBox()
      vbox.pack_start(hbox)
      hbox.set_spacing(10)
      img=gtk.Image()
      img.set_from_stock(gtk.STOCK_DIALOG_ERROR,gtk.ICON_SIZE_DIALOG)
      hbox.pack_start(img,False,False)
      svbox=gtk.VBox()
      svbox.set_spacing(10)
      hbox.pack_start(svbox)
      self.label=gtk.Label()
      self.label.set_markup("<span size='large'><b>%s</b></span>"%_("DOWNLOAD_FAILED"))
      self.label.set_alignment(0,0.5)
      svbox.pack_start(self.label,False,False)
      self.sublabel=gtk.Label(_("GO_TO_DOWNLOAD_LINK"))
      svbox.pack_start(self.sublabel,False,False)
      self.sublabel.set_alignment(0,0.5)
      self.urllabel=gtk.LinkButton(url,url)
      svbox.pack_start(self.urllabel,False,False)
   def run(self):
      self.show_all()
      gtk.Dialog.run(self)
      self.hide()

class VersionDownloadDialog(gtk.Dialog):
   def __init__(self,app,url,filename,size,dest):
      gtk.Dialog.__init__(self,_("DOWNLOADING"),app)
      self.src=url
      self.dest=dest
      self.filesize=size
      self.progress_lock=thread.allocate_lock()
      self.progress=0
      self.set_has_separator(False)
      self.set_deletable(False)
      self.connect('key_press_event',self.on_key_press_event)
      vbox=gtk.VBox()
      self.child.add(vbox)
      vbox.set_border_width(5)
      vbox.set_spacing(10)
      l=gtk.Label(_("DOWNLOADING_FILENAME")%filename)
      vbox.pack_start(l)
      l.set_alignment(0,0.5)
      self.pb=gtk.ProgressBar()
      vbox.pack_start(self.pb)
   def _get_progress(self):
      self.progress_lock.acquire()
      res=self._progress
      self.progress_lock.release()
      return res
   def _set_progress(self,value):
      self.progress_lock.acquire()
      self._progress=value
      self.progress_lock.release()
   progress=property(_get_progress,_set_progress)
   def on_key_press_event(self,widget,event):
      if event.keyval==65307:
         return True
   def do_download(self,src,dest,filesize):
      try:
         size=eval(filesize)
         read_length=0
         bufsize=size/50
         fsrc=urllib.urlopen(src)
         fdest=open(dest,"wb")
         data=fsrc.read(bufsize)
         while data:
            fdest.write(data)
            read_length+=bufsize
            self.progress=min(1,1.*read_length/size)
            data=fsrc.read(bufsize)
         fsrc.close()
         fdest.close()
      except:
         try:
            fdest.close()
            os.unlink(dest)
         except:
            pass
         self.progress=-1
   def watch_progress(self):
      p=self.progress
      if p>=1:
         self.response(gtk.RESPONSE_OK)
         return False
      if p<0:
         self.response(gtk.RESPONSE_CANCEL)
         return False
      if p==0:
         self.pb.pulse()
      else:
         self.pb.set_fraction(p)
      return True
   def run(self):
      self.show_all()
      gobject.timeout_add(50,self.watch_progress)
      thread.start_new_thread(self.do_download,(self.src,self.dest,self.filesize))
      res=gtk.Dialog.run(self)
      self.hide()
      return res==gtk.RESPONSE_OK

class VersionDestinationDialog(gtk.FileChooserDialog):
   def __init__(self,app,filename):
      gtk.FileChooserDialog.__init__(self,_("SELECT_DESTINATION"),app,gtk.FILE_CHOOSER_ACTION_SAVE)
      self.add_button(gtk.STOCK_SAVE,gtk.RESPONSE_OK)
      self.add_button(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL)
      self.set_default_response(gtk.RESPONSE_OK)
      self.set_current_name(filename)
      self.set_do_overwrite_confirmation(True)
   def run(self):
      self.show_all()
      if gtk.FileChooserDialog.run(self)==gtk.RESPONSE_OK:
         res=self.get_filename()
      else:
         res=None
      self.hide()
      return res

class VersionAvailableFilesDialog(gtk.Dialog):
   def __init__(self,app,files):
      gtk.Dialog.__init__(self,_("PLEASE_WAIT"),app)
      self.available_files_lock=thread.allocate_lock()
      self.urls_lock=thread.allocate_lock()
      self.add_button(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL)
      self.urls=files
      self.total_urls=len(self.urls)
      self.available_files=[]
      vbox=gtk.VBox()
      self.child.add(vbox)
      vbox.set_border_width(5)
      vbox.set_spacing(10)
      self.main_label=gtk.Label()
      vbox.pack_start(self.main_label)
      self.main_label.set_alignment(0,0.5)
      self.main_label.set_markup("<span size='large'><b>%s</b></span>"%_("LOOKING_UP_AVAILABLE_FILES"))
      self.pb=gtk.ProgressBar()
      vbox.pack_start(self.pb)
      self.sub_label=gtk.Label()
      self.sub_label.set_alignment(0,0.5)
      vbox.pack_start(self.sub_label)
      self.sub_label.set_text(_("FOUND_NB_FILES")%0)
   def _get_urls(self):
      self.urls_lock.acquire()
      res=self._urls
      self.urls_lock.release()
      return res
   def _set_urls(self,value):
      self.urls_lock.acquire()
      self._urls=value
      self.urls_lock.release()
   urls=property(_get_urls,_set_urls)
   def _get_available_files(self):
      self.available_files_lock.acquire()
      res=self._available_files
      self.available_files_lock.release()
      return res
   def _set_available_files(self,value):
      self.available_files_lock.acquire()
      self._available_files=value
      self.available_files_lock.release()
   available_files=property(_get_available_files,_set_available_files)
   def check_available_files(self):
      nrem=len(self.urls)
      self.sub_label.set_text(_("FOUND_NB_FILES")%len(self.available_files))
      self.pb.pulse()
      if nrem==0:
         self.response(gtk.RESPONSE_OK)
         return False
      else:
         return True
   def list_new_files(self):
      c=httplib2.Http()
      while self.urls:
         try:
            url,filename,desc=self.urls[0].split(";")
            resp,content=c.request(url,"HEAD")
            if resp.status==200:
               if "content-length" in resp:
                  content_length=resp["content-length"]
               else:
                  content_length=None
               if "content-location" in resp:
                  content_location=resp["content-location"]
               else:
                  content_location=url
               self.available_files=self.available_files+[(content_location,filename,desc,content_length)]
         except:
            pass
         self.urls=self.urls[1:]
   def run(self):
      timer=gobject.timeout_add(50,self.check_available_files)
      self.show_all()
      thread.start_new_thread(self.list_new_files,())
      res=gtk.Dialog.run(self)
      self.hide()
      if res==gtk.RESPONSE_OK:
         return self.available_files
      else:
         gobject.source_remove(timer)
         return None

class VersionFileSelectorDialog(gtk.Dialog):
   def __init__(self,app,files):
      gtk.Dialog.__init__(self,_("SELECT_FILE_TO_DOWNLOAD"),app)
      self.ok_button=gtk.Button(_("DOWNLOAD"))
      img=gtk.Image()
      img.set_from_icon_name("torrent-search-download",gtk.ICON_SIZE_BUTTON)
      self.ok_button.set_image(img)
      self.ok_button.set_flags(gtk.CAN_DEFAULT)
      self.add_action_widget(self.ok_button,gtk.RESPONSE_OK)
      self.add_button(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL)
      self.set_default_response(gtk.RESPONSE_OK)
      table=gtk.Table(2,len(files)+1)
      self.child.add(table)
      table.set_border_width(5)
      table.set_col_spacings(20)
      table.set_row_spacings(5)
      l=gtk.Label(_("PLEASE_SELECT_DOWNLOAD_FILE"))
      l.set_alignment(0,0.5)
      table.attach(l,0,2,0,1)
      self.rb_files={}
      prec_rb=None
      for i in range(len(files)):
         url,filename,desc,size=files[i]
         rb=gtk.RadioButton(prec_rb,"%s (%s)"%(_(desc),filename))
         rb.set_use_underline(False)
         prec_rb=rb
         self.rb_files[rb]=(url,filename,size)
         table.attach(rb,1,2,i+1,i+2)
   def run(self):
      self.show_all()
      if gtk.Dialog.run(self)==gtk.RESPONSE_OK:
         res=None
         for i in self.rb_files:
            if i.get_active():
               res=self.rb_files[i]
               break
      else:
         res=None
      self.hide()
      return res

class VersionNotifierDialog(gtk.Dialog):
   def __init__(self,app):
      gtk.Dialog.__init__(self,_("NEW_VERSION_AVAILABLE"),app)
      self._app=app
      self.download_button=gtk.Button(_("DOWNLOAD_NOW"))
      self.download_button.set_flags(gtk.CAN_DEFAULT)
      img=gtk.Image()
      img.set_from_icon_name("torrent-search-download",gtk.ICON_SIZE_BUTTON)
      self.download_button.set_image(img)
      self.add_action_widget(self.download_button,gtk.RESPONSE_YES)
      self.add_button(gtk.STOCK_CLOSE,gtk.RESPONSE_NO).grab_focus()
      self.set_default_response(gtk.RESPONSE_YES)
      vbox=gtk.VBox()
      vbox.set_border_width(5)
      vbox.set_spacing(10)
      self.child.add(vbox)
      hbox=gtk.HBox()
      vbox.pack_start(hbox)
      hbox.set_spacing(10)
      img=gtk.Image()
      img.set_from_stock(gtk.STOCK_DIALOG_INFO,gtk.ICON_SIZE_DIALOG)
      hbox.pack_start(img,False,False)
      svbox=gtk.VBox()
      svbox.set_spacing(10)
      hbox.pack_start(svbox)
      self.label=gtk.Label()
      self.label.set_alignment(0,0.5)
      svbox.pack_start(self.label,False,False)
      self.sublabel=gtk.Label()
      svbox.pack_start(self.sublabel,False,False)
      self.sublabel.set_alignment(0,0.5)
      self.dont_show_again_cb=gtk.CheckButton(_("DONT_SHOW_UNTIL_NEXT_VERSION"))
      vbox.pack_start(self.dont_show_again_cb,False,False)
      self.dont_show_again_cb.set_active(app.config["dont_show_new_version_again"])
      self.dont_show_again_cb.connect("toggled",self.on_dont_show_again_cb_toggled)
   def on_dont_show_again_cb_toggled(self,widget):
      self._app.config["dont_show_new_version_again"]=widget.get_active()
   def run(self,version):
      try:
         self.label.set_markup("<span size='large'><b>"+_("LAST_VERSION_MESG")%version+"</b></span>")
      except:
         self.label.set_markup("<span size='large'><b>"+_("NEW_VERSION_MESG")+"</b></span>")
      self.sublabel.set_text(_("CAN_DOWNLOAD_LAST_VERSION"))
      self.download_button.grab_focus()
      self.show_all()
      res=gtk.Dialog.run(self)
      self.destroy()
      return res==gtk.RESPONSE_YES
