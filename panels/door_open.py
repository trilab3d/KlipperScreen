import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return DoorOpenPanel(*args)

class DoorOpenPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        self.screen = screen
        self.do_schedule_refresh = True
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_vexpand(True)
        self.header = Gtk.Label()
        self.header.set_margin_top(60)
        self.header.set_markup("<span size='xx-large'>"+_("Door opened!")+"</span>")
        box.add(self.header)

        image_box = Gtk.Box()
        image_box.set_vexpand(True)
        image = self._gtk.Image("door-opened", self._gtk.content_width * .9, self._gtk.content_height * .9)
        image_box.add(image)
        box.add(image_box)

        self.buttons = {
            'cancel': self._gtk.Button("stop", _("Cancel"), "color2"),
            'control': self._gtk.Button("settings", _("Settings"), "color3"),
            'fine_tune': self._gtk.Button("fine-tune", _("Fine Tuning"), "color4"),
            'resume': self._gtk.Button("resume", _("Resume"), "color1"),
        }
        #self.buttons['cancel'].connect("clicked", self.cancel)
        self.buttons['control'].connect("clicked", self.screen._go_to_submenu, "")
        self.buttons['fine_tune'].connect("clicked", self.menu_item_clicked, "fine_tune", {
            "panel": "fine_tune", "name": _("Fine Tuning")})
        self.buttons['resume'].connect("clicked", self.continue_print)

        self.button_grid = self._gtk.HomogeneousGrid()
        self.button_grid.set_vexpand(False)
        self.button_grid.attach(self.buttons['resume'], 0, 0, 1, 1)
        self.button_grid.attach(self.buttons['cancel'], 1, 0, 1, 1)
        self.button_grid.attach(self.buttons['fine_tune'], 2, 0, 1, 1)
        self.button_grid.attach(self.buttons['control'], 3, 0, 1, 1)

        box.add(self.button_grid)

        self.fetch_door_sensor()
        GLib.timeout_add_seconds(1, self.fetch_door_sensor)

        self.content.add(box)

    def activate(self):
        self.fetch_door_sensor()
        GLib.timeout_add_seconds(1, self.fetch_door_sensor)

    def fetch_door_sensor(self):
        closed = self.screen.printer.data['door_sensor']['door_closed']
        logging.info(f"Door sensor object: {self.screen.printer.data['door_sensor']}")

        self.buttons['resume'].set_sensitive(closed)

        return self.do_schedule_refresh

    def continue_print(self, widget):
        self.do_schedule_refresh = False
        self.screen._ws.klippy.print_resume()
        self.screen.show_panel('job_status', "job_status", _("Printing"), 2)

