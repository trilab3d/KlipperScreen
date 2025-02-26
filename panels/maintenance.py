import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango
from datetime import datetime

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return MaintenancePanel(*args)


class MaintenancePanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        lbl = Gtk.Label()
        lbl.set_markup("<span size='x-large'>" + _("Maintenance Intervals") + "</span>")
        lbl.set_margin_top(10)
        lbl.set_margin_bottom(10)
        self.main_box.add(lbl)

        self.item_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.main_box.add(self.item_box)

        self.content.add(self.main_box)
        self.content.show_all()

    def activate(self):
        for child in self.item_box:
            self.item_box.remove(child)

        maintenance_intervals = self._screen.maintenance.show_maintenance()

        for mi in maintenance_intervals:
            name = Gtk.Label()
            name.set_markup(f"<big><b>{mi['name']}</b></big>")
            name.set_hexpand(True)
            name.set_vexpand(True)
            name.set_halign(Gtk.Align.START)
            name.set_valign(Gtk.Align.CENTER)
            name.set_line_wrap(True)
            name.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

            interval = Gtk.Label()
            interval.set_markup(f"Interval: {mi['interval']}h")
            interval.set_hexpand(True)
            interval.set_vexpand(True)
            interval.set_halign(Gtk.Align.START)
            interval.set_valign(Gtk.Align.CENTER)
            interval.set_line_wrap(True)
            interval.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

            if mi['to_next_maintenance'] > 20:
                color = "#FFFFFF"
            elif mi['to_next_maintenance'] > 0:
                color = "#FA6831"
            else:
                color = "#FF0000"

            to_next = Gtk.Label()
            to_next.set_markup(f"To next: <span color=\"{color}\">{int(mi['to_next_maintenance'])}h</span>")
            to_next.set_hexpand(True)
            to_next.set_vexpand(True)
            to_next.set_halign(Gtk.Align.START)
            to_next.set_valign(Gtk.Align.CENTER)
            to_next.set_line_wrap(True)
            to_next.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            labels.add(name)
            labels.add(interval)
            labels.add(to_next)

            dev = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            dev.get_style_context().add_class("frame-item")
            dev.set_hexpand(True)
            dev.set_vexpand(False)
            dev.set_valign(Gtk.Align.CENTER)

            dev.add(labels)

            button = self._screen.gtk.Button("retract", None, "color1")
            button.connect("clicked", self.reset_clicked, mi)
            button.set_hexpand(False)
            button.set_halign(Gtk.Align.END)

            dev.add(button)

            self.item_box.add(dev)
            self.content.show_all()

    def reset_clicked(self, widget, mi):
        self._screen.panels_reinit.append("maintenance-wizard")
        self._screen.show_panel("maintenance-wizard", "wizard", "Maintenance", 1, False,
                                wizard="maintenanceWizardSteps.ConfirmDone",
                                wizard_name="Maintenance Recommended",
                                data={"maintenance_required": [mi,], "called_from_panel": True})