import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return EmergencyStopPanel(*args)

class EmergencyStopPanel(ScreenPanel):
    def __init__(self, screen, title=None):
        super().__init__(screen, title)
        self.screen = screen
        self.do_schedule_refresh = True
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_vexpand(True)
        self.header = Gtk.Label()
        self.header.set_margin_top(60)
        self.header.set_markup("<span size='xx-large'>"+_("Emergency Stop Triggered!")+"</span>\n<span size='large'>Release Emerency Stop to continue.</span>")
        box.add(self.header)

        image_box = Gtk.Box()
        image_box.set_vexpand(True)
        image = self._gtk.Image("warning", self._gtk.content_width * .9, self._gtk.content_height * .9)
        image_box.add(image)
        box.add(image_box)

        self.content.add(box)



