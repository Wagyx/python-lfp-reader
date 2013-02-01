#!/usr/bin/env python
#
# lfp-reader
# LFP (Light Field Photography) File Reader.
#
# http://code.behnam.es/python-lfp-reader/
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2012-2013  Behnam Esfahbod


"""View and refocus LFP Picture file
"""


from __future__ import division

import os.path
import sys
from cStringIO import StringIO

import Tkinter
import tkFileDialog

try:
    import Image, ImageTk
except ImportError:
    pass

from lfp_reader import LfpPictureFile, LfpPictureError


################################################################

class LfpPictureViewer():
    """View and refocues Processed LFP Picture files (*-stk.lfp)
    """

    def __init__(self, lfp_path=None, display_size=(648, 648)):
        self._display_size = display_size

        self._tkroot = Tkinter.Tk()
        self._lfp_path = lfp_path
        if lfp_path is None:
            self._lfp_path = tkFileDialog.askopenfilename(defaultextension="lfp")
        self._tkroot.wm_title(os.path.basename(self._lfp_path))
        self._tkroot.protocol("WM_DELETE_WINDOW", self.quit)
        self._tkroot.geometry("%dx%d" % self._display_size)
        #todo self._tkroot.bind('<Configure>', self.resize)

        self._lfp = LfpPictureFile(self._lfp_path).load()

        # Create picture gui object
        self._pic = Tkinter.Label(self._tkroot)
        self._pic.bind("<Button-1>", self._cb_refocus)
        self._pic.bind("<B1-Motion>", self._cb_refocus)
        self._pic.bind("<Button-2>", self._cb_all_focused)
        self._pic.bind("<B2-Motion>", self._cb_all_focused)
        self._pic.bind("<Button-3>", self._cb_parallax)
        self._pic.bind("<B3-Motion>", self._cb_parallax)
        self._pic.pack()

        # Set default image
        self._showing_pil_image = None
        self.do_refocus_at(.5, .5)
        #self.do_all_focused()
        #self.do_parallax_at(.5, .5)

        self._tkroot.mainloop()

    def quit(self):
        self._tkroot.destroy()
        self._tkroot.quit()

    ################################
    # Display Image

    def show_image_by_group_id(self, group, image_id):
        pil_image = self._lfp.get_pil_image(group, image_id)
        return self.show_pil_image(pil_image)

    def show_pil_image(self, pil_image):
        if pil_image == self._showing_pil_image: return False
        self._showing_pil_image = pil_image
        self._resized_pil_image = self._showing_pil_image.resize(self._display_size, Image.ANTIALIAS)
        self._resized_tkp_image = ImageTk.PhotoImage(self._resized_pil_image)
        self._pic.configure(image=self._resized_tkp_image)
        return True

    ################################
    # Refocus

    def do_refocus_at(self, x_f, y_f):
        try:
            closest_refocus = self._lfp.find_closest_refocus_image(x_f, y_f)
        except:
            return False
        return self.show_image_by_group_id('refocus', closest_refocus.id)

    def _cb_refocus(self, event):
        coords_f = [event.x / self._display_size[0], event.y / self._display_size[1]]
        self.do_refocus_at(*coords_f)

    ################################
    # All-Focused

    def do_all_focused(self):
        return self.show_image_by_group_id('all_focused', None)

    def _cb_all_focused(self, event):
        self.do_all_focused()

    ################################
    # Parallax

    def do_parallax_at(self, x_f, y_f):
        try:
            closest_parallax = self._lfp.find_closest_parallax_image(x_f, y_f)
        except:
            return False
        return self.show_image_by_group_id('parallax', closest_parallax.id)

    def _cb_parallax(self, event):
        self.do_parallax_at(
                event.x / self._display_size[0],
                event.y / self._display_size[1])

################################################################

def main(lfp_paths):
    if len(lfp_paths) > 0:
        for idx, lfp_path in enumerate(lfp_paths):
            if idx > 0: print
            print "LFP Picture file: %s" % lfp_path
            LfpPictureViewer(lfp_path)
    else:
        LfpPictureViewer()


def usage(errcode=0, of=sys.stderr):
    print >>of, ("Usage: %s picture-stk.lfp [picture-stk-2.lfp ...]" %
            os.path.basename(sys.argv[0]))
    sys.exit(errcode)


if __name__=='__main__':
    if len(sys.argv) < 1:
        usage(1)
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        exit(2)
    except Exception as err:
        print >>sys.stderr, "Error:", err
        if sys.platform == 'win32': raw_input()
        exit(9)

