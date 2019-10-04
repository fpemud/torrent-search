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

import gtk, os

def load_icons(share_dir):
   path=os.path.join(share_dir,"torrent-search","icons")
   sizes=[16, 22, 32, 48, 64, 128]
   for size in sizes:
      sizepath=os.path.join(path,"%dx%d"%(size,size))
      try:
         for filename in os.listdir(sizepath):
            try:
               fullfilename=os.path.join(sizepath,filename)
               iconname,ext=filename.split(".")
               if ext=="png":
                  gtk.icon_theme_add_builtin_icon(iconname, size, gtk.gdk.pixbuf_new_from_file(fullfilename))
            except:
               pass
      except:
         pass
   
