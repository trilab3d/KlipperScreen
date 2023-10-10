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

        indicator_dev = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        #indicator_dev.get_style_context().add_class("frame-item")
        indicator_dev.set_hexpand(True)
        indicator_dev.set_vexpand(False)
        indicator_dev.set_valign(Gtk.Align.CENTER)

        indicator_name = Gtk.Label()
        indicator_name.set_markup(f"<big><b>Door Closed</b></big>")
        indicator_name.set_hexpand(True)
        indicator_name.set_vexpand(True)
        indicator_name.set_halign(Gtk.Align.START)
        indicator_name.set_valign(Gtk.Align.CENTER)

        indicator_labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        indicator_labels.add(indicator_name)

        indicator_dev.add(indicator_labels)
        self.indicator = Gtk.Switch()
        self.indicator.set_sensitive(False)
        #self.indicator.connect("notify::active", self.set_door_sensor_disabled)
        indicator_dev.add(self.indicator)

        self.content.add(indicator_dev)

        switch_dev = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        #switch_dev.get_style_context().add_class("frame-item")
        switch_dev.set_hexpand(True)
        switch_dev.set_vexpand(False)
        switch_dev.set_valign(Gtk.Align.CENTER)

        switch_name = Gtk.Label()
        switch_name.set_markup(f"<big><b>Enabled</b></big>")
        switch_name.set_hexpand(True)
        switch_name.set_vexpand(True)
        switch_name.set_halign(Gtk.Align.START)
        switch_name.set_valign(Gtk.Align.CENTER)

        switch_labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        switch_labels.add(switch_name)

        switch_dev.add(switch_labels)
        self.switch = Gtk.Switch()
        self.switch.connect("notify::active", self.set_door_sensor_disabled)
        switch_dev.add(self.switch)

        self.content.add(switch_dev)
        self.fetch_door_sensor()
        GLib.timeout_add_seconds(1, self.fetch_door_sensor)

    def activate(self):
        self.do_schedule_refresh = True
        self.fetch_door_sensor()
        GLib.timeout_add_seconds(1, self.fetch_door_sensor)

    def deactivate(self):
        self.do_schedule_refresh = False

    def fetch_door_sensor(self):
        door_sensor = self.screen.printer.data['door_sensor']
        #logging.info(f"Door sensor object: {door_sensor}")

        self.indicator.set_active(door_sensor["door_closed"] and door_sensor["enabled"])
        self.switch.set_active(door_sensor["enabled"])

        self._screen.show_all()

        return self.do_schedule_refresh

    def set_door_sensor_disabled(self, widget, active):
        self._screen._ws.klippy.gcode_script(f"SET_DOOR_SENSOR_DISABLED DISABLED={0 if widget.get_active() else 1}")