import logging
import os

import gi
import json

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args, **kvargs):
    return Security(*args, **kvargs)

class Security(ScreenPanel):
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

        self.btn_save = self._gtk.Button("settings", _("Save"), "color1")
        self.btn_save.set_hexpand(False)
        self.btn_save.set_vexpand(False)
        self.btn_save.connect("clicked", self.save_changes)
        btn_discard = self._gtk.Button("cancel", _("Discard"), "color1")
        btn_discard.set_hexpand(False)
        btn_discard.set_vexpand(False)
        btn_discard.connect("clicked", self.revert_changes)

        self.button_panel = self._gtk.HomogeneousGrid()
        # self.button_panel
        self.box.add(self.button_panel)
        self.button_panel.attach(btn_discard, 0, 0, 1, 1)
        self.button_panel.attach(self.btn_save, 1, 0, 1, 1)

        self.changed_fields = {}

        self.rebuild_pages()

    def rebuild_pages(self):
        creds = self._screen.tpcclient.send_request("/credentials")
        setts = self._screen.tpcclient.send_request("/settings")

        for ch in self.grid.get_children():
            self.grid.remove(ch)

        entries = []

        user_label = Gtk.Label(label=_("User:"))
        user_label.set_halign(Gtk.Align.END)
        user_entry = Gtk.Entry()
        user_entry.set_text(creds["user"])
        user_entry.connect("changed", self.change_user)
        user_entry.set_visibility(True)
        user_entry.connect("button-press-event", self._screen.show_keyboard)
        user_entry.set_hexpand(True)
        user_entry.set_vexpand(False)
        entries.append(user_entry)
        self.grid.attach(user_label, 0, 0, 1, 1)
        self.grid.attach(user_entry, 1, 0, 2, 1)

        password_label = Gtk.Label(label=_("Password:"))
        password_label.set_halign(Gtk.Align.END)
        password_entry = Gtk.Entry()
        password_entry.set_text("")
        password_entry.connect("changed", self.change_password)
        password_entry.set_visibility(True)
        password_entry.connect("button-press-event", self._screen.show_keyboard)
        password_entry.set_hexpand(True)
        password_entry.set_vexpand(False)
        entries.append(password_entry)
        self.grid.attach(password_label, 0, 1, 1, 1)
        self.grid.attach(password_entry, 1, 1, 2, 1)

        enabled_label = Gtk.Label(label="Enabled:")
        enabled_label.set_halign(Gtk.Align.END)
        enabled_switch = Gtk.Switch()
        enabled_switch.set_active(setts["locked"])
        enabled_switch.set_hexpand(False)
        enabled_switch.connect("notify::active", self.change_enabled)
        self.grid.attach(enabled_label, 0, 2, 1, 1)
        self.grid.attach(enabled_switch, 1, 2, 1, 1)
        blank_box = Gtk.Box()
        blank_box.set_hexpand(False)
        #self.grid.attach(blank_box, 3, 2, 1, 1)

        self.update_valid()

        self._screen.show_all()

    def change_user(self, widget):
        self.changed_fields["user"] = widget.get_text()
        self.update_valid()

    def change_password(self, widget):
        self.changed_fields["password"] = widget.get_text()
        self.update_valid()

    def change_enabled(self, widget, active):
        self.changed_fields["enabled"] = widget.get_active()
        self.update_valid()

    def update_valid(self):
        print(f"chnaged fileds: {self.changed_fields}")
        if (("user" in self.changed_fields or "enabled" in self.changed_fields) and
                ("user" not in self.changed_fields or
                 (len(self.changed_fields["user"]) > 0 and "password" in self.changed_fields and
                  len(self.changed_fields["password"]) > 0))):
            self.btn_save.set_sensitive(True)
        else:
            self.btn_save.set_sensitive(False)

    def save_changes(self, widget):
        if "user" in self.changed_fields:
            credentials = {
                "user": self.changed_fields["user"],
                "password": self.changed_fields["password"]
            }
            self._screen.tpcclient.send_request(f"credentials", "POST", body=credentials)
        if "enabled" in self.changed_fields:
            settings = {
                "locked": self.changed_fields["enabled"],
            }
            self._screen.tpcclient.send_request(f"settings", "POST", body=settings)
        self._screen._menu_go_back()

    def revert_changes(self, widget):
        self.rebuild_pages()

    def activate(self):
        self.rebuild_pages()