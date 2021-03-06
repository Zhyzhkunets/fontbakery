#!/usr/bin/env python
# coding: utf-8
# Copyright 2013 The Font Bakery Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# See AUTHORS.txt for the list of Authors and LICENSE.txt for the License.

"""
Script to find for TTF fonts in the given dir the character set coverage 
by family average and per style, and list missing characters.

Usage: $ ./famchar.py directory/
"""

import sys, os, glob, pprint
from fontaine.font import Font

# Need 1 arg 
if len(sys.argv) < 2:
    print __doc__
    sys.exit()
# Check the arg is a directory
workingDir = sys.argv[1]
if os.path.exists(workingDir):
    # If it is a directory, change context to it
    os.chdir(workingDir)
else:
    print __doc__
    sys.exit()

# Run pyFontaine on all the TTF fonts
fonts = {}
for filename in glob.glob("*.*tf"):
    fontaine = Font(filename)
    fonts[filename] = fontaine

# Make a plain dictionary 
family = {}
for fontfilename, fontaine in fonts.iteritems():
    # Use the font file name as a key to a dictionary of char sets
    family[fontfilename] = {}
    for charset, coverage, percentcomplete, missingchars in fontaine.get_orthographies():
        # Use each char set name as a key to a dictionary of this font's coverage details
        charsetname = charset.common_name
        family[fontfilename][charsetname] = {}
        family[fontfilename][charsetname]['coverage'] = coverage # unsupport, fragmentary, partial, full
        family[fontfilename][charsetname]['percentcomplete'] = percentcomplete # int
        family[fontfilename][charsetname]['missingchars'] = missingchars # list of ord numbers
        # Use the char set name as a key to a list of the family's average coverage
        if not family.has_key(charsetname):
            family[charsetname] = []
        # Append the char set percentage of each font file to the list
        family[charsetname].append(percentcomplete) # [10, 32, 40, 40] etc
        # And finally, if the list now has all the font files, make it the mean average percentage
        if len(family[charsetname]) == len(fonts.items()):
            family[charsetname] = sum(family[charsetname]) / len(fonts.items())


# # pprint the full dict, could be yaml/json/etc
# pp = pprint.PrettyPrinter(indent=1, width=1000, depth=6)
# pprint.pprint(family)

# # pprint all the totals
#import ipdb; ipdb.set_trace()
#for k in sorted(family.keys()):
#    if not k.endswith('.ttf'):
#        print k + ',' + str(family[k])

# import ipdb; ipdb.set_trace()
# Make a plain dictionary with just the bits we want on the dashboard
totals = {} 
totals['gwf'] = family[u'GWF latin']
totals['al3'] = family[u'Adobe Latin 3']
totals['cyr'] = family[u'Basic Cyrillic']
for charset in sorted(totals.keys()):
    #import ipdb; ipdb.set_trace()
    #print charset, totals[charset], 
    print charset + ",", str(totals[charset]) + ',',
