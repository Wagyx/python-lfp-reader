# python
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


"""An LFP Picture Viewer using Tkinter GUI library
"""

from __future__ import division

import Tkinter

# Python Imageing Library
try:
    import Image as PIL, ImageTk as TkPIL
except ImportError:
    PIL = None
def _check_pil_module():
    if PIL is None:
        raise RuntimeError("Cannot find Python Imaging Library (PIL or Pillow)")


################################################################

class LfpTkViewer():
    """View and refocues Processed LFP Picture files (*-stk.lfp)
    """

    def __init__(self, lfp_picture,
                 title="Light-Field Picture",
                 title_pattern="%s [Python LFP Reader]",
                 init_size=(648, 648)):
        self._title_pattern = title_pattern
        self._active_size = None
        self._active_pil_image = None

        # Set LFP Picture
        self._lfp = lfp_picture
        self._preload_lfp_pil_images()

        # Show tk window
        self._tk_root = Tkinter.Tk()
        self._tk_root.protocol("WM_DELETE_WINDOW", self.quit)
        self._tk_root.geometry("%dx%d" % init_size)
        self._tk_root.configure(background='black')
        self._tk_root.bind('<Configure>', self._cb_resize)
        self._tk_root.bind('<Control-w>', self.quit)
        self._tk_root.bind('<Control-q>', self.quit)
        self.set_title(title)

        # Create tk picture
        self._tk_pic = Tkinter.Label(self._tk_root)
        if self._lfp.has_refocus_stack():
            self._tk_pic.bind("<Button-1>",  self._cb_refocus)
            self._tk_pic.bind("<B1-Motion>", self._cb_refocus)
            self._tk_pic.bind("<Button-2>",  self._cb_all_focused)
            self._tk_pic.bind("<B2-Motion>", self._cb_all_focused)
        if self._lfp.has_parallax_stack():
            self._tk_pic.bind("<Button-3>",  self._cb_parallax)
            self._tk_pic.bind("<B3-Motion>", self._cb_parallax)
        self._tk_pic.pack()

        # Verify and init view
        self.set_active_size(init_size)
        if self._lfp.has_refocus_stack():
            self.do_refocus_at(.5, .5)
        elif self._lfp.has_parallax_stack():
            self.do_parallax_at(.5, .5)
        elif self._lfp.has_frame():
            #todo Processing raw data!
            pass
        else:
            raise Exception("Unsupported LFP Picture file")

        # Main loop
        self._tk_root.mainloop()

    def quit(self, event=None):
        self._tk_root.destroy()
        self._tk_root.quit()


    ################################
    # PIL

    def _preload_lfp_pil_images(self):
        if self._lfp.has_refocus_stack():
            for id in self._lfp.get_refocus_stack().refocus_images:
                self._lfp.get_pil_image('refocus', id)
            self._lfp.get_pil_image('all_focused')
        if self._lfp.has_parallax_stack():
            for id in self._lfp.get_parallax_stack().parallax_images:
                self._lfp.get_pil_image('parallax', id)

    ################################
    # Title

    def set_title(self, title):
        if self._title_pattern:
            title = self._title_pattern % title
        self._tk_root.wm_title(title)

    ################################
    # Size

    def set_active_size(self, size):
        if size == self._active_size:
            return
        self._active_size = size
        self._reset_caches()
        self._redraw_active_image()

    def _cb_resize(self, event):
        new_size = (min(event.width, event.height), )*2
        self.set_active_size(new_size)


    ################################
    # Image

    def set_active_image(self, group, image_id):
        pil_image = self._lfp.get_pil_image(group, image_id)
        self.set_active_pil_image(pil_image)

    def set_active_pil_image(self, pil_image=None):
        if self._active_pil_image == pil_image:
            return
        self._active_pil_image = pil_image
        self._redraw_active_image()

    def _redraw_active_image(self):
        if not self._active_pil_image:
            return
        tkp_image = self._get_resized_tkp_image(self._active_pil_image)
        self._tk_pic.configure(image=tkp_image)


    ################################
    # PIL.Image/TK.PhotoImage Caches

    def _reset_caches(self):
        self._resized_pil_cache = {}
        self._resized_tkp_cache = {}

    def _get_resized_tkp_image(self, pil_image):
        if pil_image not in self._resized_tkp_cache:
            resized_pil_image = self._get_resized_pil_image(pil_image)
            self._resized_tkp_cache[pil_image] = TkPIL.PhotoImage(resized_pil_image)
        return self._resized_tkp_cache[pil_image]

    def _get_resized_pil_image(self, pil_image):
        if pil_image not in self._resized_pil_cache:
            self._resized_pil_cache[pil_image] = pil_image.resize(self._active_size, PIL.ANTIALIAS)
        return self._resized_pil_cache[pil_image]


    ################################
    # Refocus

    def do_refocus_at(self, x_f, y_f):
        closest_refocus = self._lfp.find_closest_refocus_image(x_f, y_f)
        self.set_active_image('refocus', closest_refocus.id)

    def _cb_refocus(self, event):
        self.do_refocus_at(
                event.x / self._active_size[0],
                event.y / self._active_size[1])


    ################################
    # All-Focused

    def do_all_focused(self):
        self.set_active_image('all_focused', None)

    def _cb_all_focused(self, event):
        self.do_all_focused()


    ################################
    # Parallax

    def do_parallax_at(self, x_f, y_f):
        closest_parallax = self._lfp.find_closest_parallax_image(x_f, y_f)
        self.set_active_image('parallax', closest_parallax.id)

    def _cb_parallax(self, event):
        self.do_parallax_at(
                event.x / self._active_size[0],
                event.y / self._active_size[1])

