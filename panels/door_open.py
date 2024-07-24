import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args, **kvargs):
    return DoorOpenFilamentRunoutPanel(*args, **kvargs)

class DoorOpenFilamentRunoutPanel(ScreenPanel):
    def __init__(self, screen, title, **kvargs):
        super().__init__(screen, title)
        self.screen = screen
        self.do_schedule_refresh = True

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_vexpand(True)
        self.header = Gtk.Label()
        self.header.set_margin_top(40)
        self.header.set_margin_bottom(20)
        self.header.set_markup("<span size='xx-large'>" + _("The door was open") + "</span>")
        box.add(self.header)

        image_box = Gtk.Box()
        image_box.set_vexpand(True)
        image = self._gtk.Image("door-opened", self._gtk.content_width * .9, self._gtk.content_height * .9)
        image_box.add(image)
        box.add(image_box)
        self.image_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.image_box.set_vexpand(True)
        self.image_door = self._gtk.Image("door-opened", self._gtk.content_width * .9, self._gtk.content_height * .9)
        self.image_prusament = self._gtk.Image("unload_guide", self._gtk.content_width * .8, self._gtk.content_height * .8)

        self.buttons = {
            'cancel': self._gtk.Button("stop", _("Cancel"), "color2"),
            'control': self._gtk.Button("settings", _("Settings"), "color3"),
            'fine_tune': self._gtk.Button("fine-tune", _("Fine Tuning"), "color4"),
            'resume': self._gtk.Button("resume", _("Resume"), "color1"),
        }
        self.buttons['cancel'].connect("clicked", self.cancel)
        self.buttons['control'].connect("clicked", self.screen._go_to_submenu, "")
        self.buttons['fine_tune'].connect("clicked", self.menu_item_clicked, "fine_tune", {
            "panel": "fine_tune", "name": _("Fine Tuning")})
        self.buttons['resume'].connect("clicked", self.continue_print)

        self.button_grid = self._gtk.HomogeneousGrid()
        self.button_grid.set_vexpand(False)
        self.button_grid.attach(self.buttons['resume'], 0, 0, 1, 1)
        self.button_grid.attach(self.buttons['cancel'], 1, 0, 1, 1)
        #self.button_grid.attach(self.buttons['fine_tune'], 2, 0, 1, 1)
        self.button_grid.attach(self.buttons['control'], 3, 0, 1, 1)

        box.add(self.button_grid)

        self.fetch_sensors()
        GLib.timeout_add_seconds(1, self.fetch_sensors)

        self.content.add(box)

    def activate(self):
        self.do_schedule_refresh = True
        self.fetch_sensors()
        GLib.timeout_add_seconds(1, self.fetch_sensors)

    def deactivate(self):
        self.do_schedule_refresh = False

    def fetch_sensors(self):
        closed = self.screen.printer.data['door_sensor']['door_closed']

        self.buttons['resume'].set_sensitive(closed)

        return self.do_schedule_refresh

    def continue_print(self, widget):
        self.do_schedule_refresh = False
        self.screen._ws.klippy.print_resume()
        self.screen.show_panel('job_status', "job_status", _("Printing"), 2)

    def cancel(self, widget):
        buttons = [
            {"name": _("Cancel Print"), "response": Gtk.ResponseType.OK},
            {"name": _("Go Back"), "response": Gtk.ResponseType.CANCEL},
        ]
        if len(self._printer.get_stat("exclude_object", "objects")) > 1:
            buttons.insert(
                0, {"name": _("Exclude Object"), "response": Gtk.ResponseType.APPLY}
            )
        label = Gtk.Label()
        label.set_markup(_("Are you sure you wish to cancel this print?"))
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.CENTER)
        label.set_vexpand(True)
        label.set_valign(Gtk.Align.CENTER)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        dialog = self._gtk.Dialog(self._screen, buttons, label, self.cancel_confirm)
        dialog.set_title(_("Cancel"))

    def cancel_confirm(self, dialog, response_id):
        self._gtk.remove_dialog(dialog)
        if response_id == Gtk.ResponseType.APPLY:
            self.menu_item_clicked(
                None, "exclude", {"panel": "exclude", "name": _("Exclude Object")}
            )
            return
        if response_id == Gtk.ResponseType.CANCEL:
            self.enable_button("resume", "cancel")
            return
        logging.debug("Canceling print")
        self.disable_button("resume", "cancel")
        self._screen._ws.klippy.print_cancel()

    def enable_button(self, *args):
        for arg in args:
            self.buttons[arg].set_sensitive(True)

    def disable_button(self, *args):
        for arg in args:
            self.buttons[arg].set_sensitive(False)