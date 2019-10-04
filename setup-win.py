#!/usr/bin/env python

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

from distutils.core import setup
import py2exe
import os, sys

def walk_lib_files(res,path,files):
   if ".svn" in path:
      return
   l=[]
   for i in files:
      if os.path.isfile(os.path.join(path,i)):
         if i[-1]!='~' and i[-4:]!='.bak':
            l.append(os.path.join(path,i))
   if l:
      res.append((os.path.join("lib",path[4:]),l))

def list_lib_files():
   res=[]
   os.path.walk('lib',walk_lib_files,res)
   return res

def walk_share_files(res,path,files):
   if ".svn" in path:
      return
   l=[]
   for i in files:
      if os.path.isfile(os.path.join(path,i)):
         if i[-1]!='~' and i[-4:]!='.bak':
            l.append(os.path.join(path,i))
   if l:
      res.append((os.path.join("share",path[10:]),l))

def list_share_files():
   res=[]
   os.path.walk('share-win',walk_share_files,res)
   return res
   
def walk_etc_files(res,path,files):
   if ".svn" in path:
      return
   l=[]
   for i in files:
      if os.path.isfile(os.path.join(path,i)):
         if i[-1]!='~' and i[-4:]!='.bak':
            l.append(os.path.join(path,i))
   if l:
      res.append((os.path.join("etc",path[8:]),l))

def list_etc_files():
   res=[]
   os.path.walk('etc-win',walk_etc_files,res)
   return res

setup(name='torrent-search',
   version="0.11.2",
   author='Gwendal Le Bihan',
   author_email='gwendal.lebihan.dev@gmail.com',
   maintainer='Gwendal Le Bihan',
   maintainer_email='gwendal.lebihan.dev@gmail.com',
   description='Search for torrents on different websites',
   packages=["TorrentSearch","TorrentSearch.exceptions"],
   data_files=list_share_files()+list_lib_files()+list_etc_files(),
   url="http://torrent-search.sourceforge.net",
   download_url="http://sourceforge.net/projects/torrent-search/files/",
   windows=[
   {"script":'torrent-search',
   "icon_resources":[(1,"torrent-search.ico")]},
   ],
   options = {
                  'py2exe': {
                      'packages':'encodings, email.iterators, TorrentSearch.htmltools, PIL',
                      'includes': 'cairo, pango, pangocairo, atk, gobject, httplib2, commands',
                  },
              },

   )
