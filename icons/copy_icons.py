#!/usr/bin/env python3

##
## This file is part of the sigrok-meter project.
##
## Copyright (C) 2015 Jens Steinhauser <jens.steinhauser@gmail.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
##

# This scripts copies the icons that sigrok-meter uses from the icon pack,
# and outputs the matching entries for a Qt resource file.

import os
import shutil

ICONDIR = '../adwaita-icon-theme-3.18.0/Adwaita'
OUTDIR = 'icons/adwaita-icon-theme-3.18.0'

def find(iconname):
    result = []
    for root, dirs, files in os.walk(ICONDIR):
        if iconname in files:
            result.append(os.path.join(root[len(ICONDIR)+1:], iconname))
    return result

def copy(alias, iconname):
    for fn in sorted(find(iconname)):
        inputfile = os.path.join(ICONDIR, fn)
        outputfile = os.path.join(OUTDIR, fn)
        outputpath = os.path.dirname(outputfile)
        size = fn.split(os.sep)[0]

        if not os.path.exists(outputpath):
            os.makedirs(outputpath)

        shutil.copy(inputfile, outputpath)

        template = '<file alias="{}-{}.png">{}</file>'
        print(template.format(alias, size, outputfile))

copy('about',       'help-about.png')
copy('add',         'list-add.png')
copy('exit',        'application-exit.png')
copy('graph',       'utilities-system-monitor.png')
copy('log',         'accessories-text-editor.png')
copy('preferences', 'preferences-system.png')
copy('start',       'media-playback-start.png')
copy('stop',        'media-playback-stop.png')
