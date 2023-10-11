import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return PostUpdatePanel(*args)

class PostUpdatePanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        self.screen = screen
        self.do_schedule_refresh = True
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_vexpand(True)
        self.header = Gtk.Label()
        self.header.set_margin_top(300)
        self.header.set_markup("<span size='xx-large'>"+_("Update almost done")+"</span>")
        box.add(self.header)

        self.fetch_post_update_status()
        GLib.timeout_add_seconds(1, self.fetch_post_update_status)

        self.content.add(box)

    def activate(self):
        self.fetch_post_update_status()
        GLib.timeout_add_seconds(1, self.fetch_post_update_status)

    def deactivate(self):
        self.do_schedule_refresh = False

    def fetch_post_update_status(self):
        try:
            with open("/home/trilab/post-update-status","r") as f:
                status = f.readline()
                logging.info(f"Read post-update-status {status}")
                f.close()
            if status.strip() == "DONE":
                logging.info(f"post-update done, restart KS")
                self._screen.restart_ks()
        except Exception:
            pass

        return self.do_schedule_refresh

