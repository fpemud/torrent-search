#!/usr/bin/env python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

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

import optparse
from .informations import *
from .constants import DEFAULT_SHARE_PATH


class OptionParser(optparse.OptionParser):

    def __init__(self):
        optparse.OptionParser.__init__(self, add_help_option=False)
        self.version = VERSION

        basic_group = self.add_option_group(_("BASIC_OPTIONS"))
        basic_group.add_option("-h", "--help", dest="show_help",
                               action="store_true", help=_("SHOW_THIS_HELP_AND_EXIT"))
        basic_group.add_option("-v", "--version", action="store_true",
                               dest="show_version", help=_("HELP_SHOW_VERSION"))
        basic_group.add_option("--search", "-s", dest="search_pattern",
                               default="", help=_("RUN_SEARCH_ON_STARTUP"))
        basic_group.add_option("--no-plugins-check", dest="no_plugins_check",
                               action="store_true", help=_("HELP_NO_PLUGIN_CHECK"))

        advanced_group = self.add_option_group(_("ADVANCED_OPTIONS"))
        advanced_group.add_option("--share-dir", dest="share_dir",
                                  default=DEFAULT_SHARE_PATH, help=_("PATH_TO_SHARE"))
        advanced_group.add_option("--add-plugin", dest="add_plugin", default="",
                                  help=_("HELP_ADD_PLUGIN"))
