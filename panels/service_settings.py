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

        btn_save = self._gtk.Button("settings", "Save", "color1")
        btn_save.set_hexpand(False)
        btn_save.set_vexpand(False)
        btn_save.connect("clicked", self.save_changes)
        btn_discard = self._gtk.Button("cancel", "Discard", "color1")
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

        index = 0
        model_name_label = Gtk.Label(label="Model Name:")
        model_name_label.set_halign(Gtk.Align.END)
        model_name_entry = Gtk.Entry()
        model_name_entry.set_text(self.settings["model_name"])
        model_name_entry.connect("changed", self.change_model_name)
        model_name_entry.set_visibility(True)
        entries.append(model_name_entry)
        self.grid.attach(model_name_label, 0, index, 2, 1)
        self.grid.attach(model_name_entry, 2, index, 3, 1)

        index += 1
        model_revision_label = Gtk.Label(label="Model Revision:")
        model_revision_label.set_halign(Gtk.Align.END)
        model_revision_entry = Gtk.Entry()
        model_revision_entry.set_text(self.settings["model_revision"])
        model_revision_entry.connect("changed", self.change_model_revision)
        model_revision_entry.set_visibility(True)
        entries.append(model_revision_entry)
        self.grid.attach(model_revision_label, 0, index, 2, 1)
        self.grid.attach(model_revision_entry, 2, index, 3, 1)

        index += 1
        serial_label = Gtk.Label(label="Serial Number:")
        serial_label.set_halign(Gtk.Align.END)
        serial_entry = Gtk.Entry()
        serial_entry.set_text(self.settings["serial_number"])
        serial_entry.connect("changed", self.change_serial_number)
        serial_entry.set_visibility(True)
        entries.append(serial_entry)
        self.grid.attach(serial_label, 0, index, 2, 1)
        self.grid.attach(serial_entry, 2, index, 3, 1)

        index += 1
        mfd_label = Gtk.Label(label="Manufacture Date:")
        mfd_label.set_halign(Gtk.Align.END)
        mfd_entry = Gtk.Entry()
        mfd_entry.set_text(self.settings["date_of_manufacture"])
        mfd_entry.connect("changed", self.change_mfd)
        mfd_entry.set_visibility(True)
        entries.append(mfd_entry)
        self.grid.attach(mfd_label, 0, index, 2, 1)
        self.grid.attach(mfd_entry, 2, index, 3, 1)

        index += 1
        update_channel_label = Gtk.Label(label="Manufacture Date:")
        update_channel_label.set_halign(Gtk.Align.END)
        self.update_channel_dropdown = Gtk.ComboBoxText()
        self.update_channels = [("dev", "Develop"), ("beta", "Beta"), ("stable", "Stable"), ("prusa-beta","Prusa Beta")]
        for i, opt in enumerate(self.update_channels):
            self.update_channel_dropdown.append(opt[0], opt[1])
            if opt[0] == self.settings["release_channel"]:
                self.update_channel_dropdown.set_active(i)
        self.update_channel_dropdown.connect("changed", self.switch_release_channel)
        self.update_channel_dropdown.set_entry_text_column(0)
        self.grid.attach(update_channel_label, 0, index, 2, 1)
        self.grid.attach(self.update_channel_dropdown, 2, index, 3, 1)

        for entry in entries:
            entry.connect("button-press-event", self._screen.show_keyboard)
            entry.set_hexpand(True)
            entry.set_vexpand(False)

        self._screen.show_all()

    def change_model_name(self, widget):
        self.changed_fields["model_name"] = widget.get_text()

    def change_model_revision(self, widget):
        self.changed_fields["model_revision"] = widget.get_text()

    def change_serial_number(self, widget):
        self.changed_fields["serial_number"] = widget.get_text()

    def change_mfd(self, widget):
        self.changed_fields["date_of_manufacture"] = widget.get_text()

    def switch_release_channel(self, widget):
        tree_iter = widget.get_active_iter()
        model = widget.get_model()
        value = model[tree_iter][1]
        self.changed_fields["release_channel"] = value

    def save_changes(self, widget):
        #print(json.dumps(self.changed_fields, indent=2))
        self._screen.tpcclient.send_request(f"settings", "POST",
                                            body=self.changed_fields)
        #self.rebuild_pages()
        self._screen._menu_go_back()

    def revert_changes(self, widget):
        #print(json.dumps(self.changed_fields, indent=2))
        self.rebuild_pages()

    def refetch_settings(self):
        settings = self._screen.tpcclient.send_request(f"settings")
        self.settings = settings

    def activate(self):
        self.rebuild_pages()