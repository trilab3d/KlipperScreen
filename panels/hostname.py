import logging
import os

import gi
import json

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args, **kvargs):
    return NetworkManagerConnectionPanel(*args, **kvargs)

class NetworkManagerConnectionPanel(ScreenPanel):
    def __init__(self, screen, title, **kvargs):
        super().__init__(screen, title)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.content.add(self.box)

        self.grid = self._gtk.HomogeneousGrid()
        self.grid.set_hexpand(True)
        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.grid)
        self.box.add(scroll)

        btn_save = self._gtk.Button("settings", _("Save"), "color1")
        btn_save.set_hexpand(False)
        btn_save.set_vexpand(False)
        btn_save.connect("clicked", self.save_changes)
        btn_discard = self._gtk.Button("cancel", _("Discard"), "color1")
        btn_discard.set_hexpand(False)
        btn_discard.set_vexpand(False)
        btn_discard.connect("clicked", self.revert_changes)

        self.button_panel = self._gtk.HomogeneousGrid()
        # self.button_panel
        self.box.add(self.button_panel)
        self.button_panel.attach(btn_discard, 0, 0, 1, 1)
        self.button_panel.attach(btn_save, 1, 0, 1, 1)

        self.changed_fields = {}

        self.rebuild_pages()

    def rebuild_pages(self):
        self.refetch_settings()
        self.changed_fields = {}

        for ch in self.grid.get_children():
            self.grid.remove(ch)

        entries = []

        hostname_label = Gtk.Label(label=_("Printer Name:"))
        hostname_label.set_halign(Gtk.Align.END)
        hostname_entry = Gtk.Entry()
        hostname_entry.set_text(self.settings["hostname"])
        hostname_entry.connect("changed", self.change_hostname)
        hostname_entry.set_visibility(True)
        hostname_entry.connect("button-press-event", self._screen.show_keyboard)
        hostname_entry.set_hexpand(True)
        hostname_entry.set_vexpand(False)
        entries.append(hostname_entry)
        self.grid.attach(hostname_label, 0, 0, 2, 1)
        self.grid.attach(hostname_entry, 2, 0, 3, 1)

        self._screen.show_all()

    def change_hostname(self, widget):
        self.changed_fields["hostname"] = widget.get_text()

    def save_changes(self, widget):
        #print(json.dumps(self.changed_fields, indent=2))
        if "hostname" in self.changed_fields:
            b = {
                "hostname": self.changed_fields["hostname"]
            }
            self._screen.tpcclient.send_request(f"set_hostname", "POST", body=b)
        #self.rebuild_pages()
        self._screen._menu_go_back()

    def revert_changes(self, widget):
        #print(json.dumps(self.changed_fields, indent=2))
        self.rebuild_pages()

    def refetch_settings(self):
        settings = {
            "hostname": os.popen(f"hostname").read().strip()
        }
        self.settings = settings

    def activate(self):
        self.rebuild_pages()