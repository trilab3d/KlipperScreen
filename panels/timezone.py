import gi
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args, **kvargs):
    return TimezonePanel(*args, **kvargs)


class TimezonePanel(ScreenPanel):

    def __init__(self, screen, title, **kvargs):
        super().__init__(screen, title)

        if "zone" in kvargs:
            self.zones = kvargs["zone"]
        else:
            self.zones = self._config.timezones

        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.content.add(scroll)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll.add(box)

        for zone in self.zones:
            name = Gtk.Label()
            name.set_markup(f"<big><b>{zone}</b></big>")
            name.set_hexpand(True)
            name.set_vexpand(True)
            name.set_halign(Gtk.Align.START)
            name.set_valign(Gtk.Align.CENTER)
            name.set_line_wrap(True)
            name.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            labels.add(name)

            dev = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            dev.get_style_context().add_class("frame-item")
            dev.set_hexpand(True)
            dev.set_vexpand(False)
            dev.set_valign(Gtk.Align.CENTER)

            dev.add(labels)
            if type(self.zones[zone]) == str:
                select = self._gtk.Button("settings", style="color3")
                select.connect("clicked", self.set_timezone, zone)
            else:
                select = self._gtk.Button("load", style="color3")
                select.connect("clicked", self.set_subzone, zone)
            select.set_hexpand(False)
            select.set_halign(Gtk.Align.END)
            dev.add(select)

            box.add(dev)
    def set_timezone(self, widget, zone):
        os.system(f"timedatectl set-timezone {self.zones[zone]}")
        os.system(f"cp -P /etc/timezone /opt/timezone")  # to have timezone persistent between updates
        os.system(f"cp -P /etc/localtime /opt/localtime")
        # self._screen.restart_ks()
        os.system("systemctl restart klipper-screen")

    def set_subzone(self, widget, zone):
        self._screen.show_panel(f"timezone-{zone}", "timezone", zone, 1, False, zone=self.zones[zone])
