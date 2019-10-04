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

MODE_GNOMEVFS, MODE_WINREG = range(2)

try:
   import _winreg
   MODE = MODE_WINREG
except:
   MODE = MODE_GNOMEVFS
import os

def mime_get_all_applications(mimetype):
   paths=os.getenv("XDG_DATA_DIRS","/usr/local/share:/usr/share").split(":")
   paths+=os.getenv("XDG_DATA_HOME","~/.local/share").split(":")
   list_files=[]
   for i in paths:
      path=os.path.join(os.path.realpath(i.replace("~",os.getenv('HOME'))),"applications")
      mimeinfo=os.path.join(path,"mimeinfo.cache")
      if os.path.exists(mimeinfo) and os.access(mimeinfo,os.R_OK):
         list_files.append(mimeinfo)
   desktops={}
   for i in list_files:
      f=open(i)
      lines=f.read().splitlines()
      f.close()
      for j in lines:
         try:
            mtype,ds=j.split("=")
            if mtype==mimetype:
               for k in ds.split(";"):
                  if k and not k in desktops:
                     if not k in desktops:
                        filename=os.path.join(os.path.split(i)[0],k)
                        if os.path.exists(filename):
                           desktops[k]=filename
                        elif "-" in k:
                           l=k.index("-")
                           filename=os.path.join(os.path.split(i)[0],k[:l],k[l+1:])
                           if os.path.exists(filename):
                              desktops[k]=filename
         except:
            pass
   res=[]
   for i in desktops:
      try:
         command=None
         title=None
         f=open(desktops[i])
         lines=f.read().splitlines()
         f.close()
         for j in lines:
            try:
               k=j.index("=")
               key=j[:k]
               value=j[k+1:]
               if key=="Exec":
                  command=value
               if key=="Name":
                  title=value
            except:
               pass
         if command and title:
            res.append((i,title,command))
      except:
         pass
   return res

def listGnomeVFSApps():
   res=[]
   for i in mime_get_all_applications("application/x-bittorrent"):
      res.append(i[:3])
   return res

def listWinRegApps():
   classesReg=_winreg.ConnectRegistry(None,_winreg.HKEY_CLASSES_ROOT)
   regKey=_winreg.OpenKey(classesReg,".torrent")
   n_subkey,n_values,modtime=_winreg.QueryInfoKey(regKey)
   progIDS=[]
   progIDSKey=_winreg.OpenKey(regKey,"OpenWithProgids")
   n_subkey,n_values,modtime=_winreg.QueryInfoKey(progIDSKey)
   for i in range(n_values):
       key,value,vtype=_winreg.EnumValue(progIDSKey,i)
       progIDS.append(key)
   _winreg.CloseKey(progIDSKey)
   _winreg.CloseKey(regKey)
   res=[]
   for i in progIDS:
      try:
         progKey=_winreg.OpenKey(classesReg,i+"\\shell\\open\\command")
         n_subkey,n_values,modtime=_winreg.QueryInfoKey(progKey)
         for j in range(n_values):
             command=_winreg.EnumValue(progKey,j)[1].replace("%1","%f")
             res.append((i,i,command))
         _winreg.CloseKey(progKey)
      except:
         pass
   _winreg.CloseKey(classesReg)
   return res

def listApps():
   try:
      if MODE==MODE_GNOMEVFS:
         res=listGnomeVFSApps()
      else:
         res=listWinRegApps()
   except:
      res=[]
   return res