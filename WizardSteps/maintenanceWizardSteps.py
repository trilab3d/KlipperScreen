import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango, GdkPixbuf
from threading import Thread
import os
import logging
import requests
import qrcode

from WizardSteps.baseWizardStep import BaseWizardStep


class CheckMaintenance(BaseWizardStep):
    def __init__(self, screen, load_var=True):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.wizard_manager.set_wizard_data("always_reinit_wizard", True)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.maintenance_required = self.wizard_manager.get_wizard_data("maintenance_required")
        if len(self.maintenance_required) == 0:
            self._screen._menu_go_back()
            return

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.maintenance_required[0]['guide_url'])
        qr.make(fit=True)
        qr_pil = qr.make_image(fill_color="black", back_color="white")
        qr_pil.save(f"/tmp/{self.maintenance_required[0]['code']}QRCode.png")
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(f"/tmp/{self.maintenance_required[0]['code']}QRCode.png", -1, 450)

        img = Gtk.Image.new_from_pixbuf(pixbuf)

        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + self.maintenance_required[0]["label1"] + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)
        second_label = self._screen.gtk.Label("")
        second_label.set_margin_top(20)
        second_label.set_margin_left(10)
        second_label.set_margin_right(10)
        second_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        second_label.set_line_wrap(True)
        second_label.set_markup(
            "<span size='small'>" + self.maintenance_required[0]["label2"] + "</span>")
        self.content.add(second_label)

        button = self._screen.gtk.Button(label=_("Remind me later"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.remind_later)
        self.content.add(button)
        button = self._screen.gtk.Button(label=_("Mark as done"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.mark_done)
        self.content.add(button)

    def remind_later(self, widget):
        self.maintenance_required = self.maintenance_required[1:]
        self.wizard_manager.set_wizard_data("maintenance_required", self.maintenance_required)
        self.wizard_manager.set_step(CheckMaintenance(self._screen))

    def mark_done(self, widget):
        self.wizard_manager.set_step(ConfirmDone(self._screen))

class ConfirmDone(BaseWizardStep):
    def __init__(self, screen, load_var=True):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.wizard_manager.debug_wizard_data()

        self.maintenance_required = self.wizard_manager.get_wizard_data("maintenance_required")
        self.called_from_panel = self.wizard_manager.get_wizard_data("called_from_panel")

        if self.called_from_panel:
            img = self._screen.gtk.Image("warning43", self._screen.gtk.content_width * .945, 450)
        else:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(f"/tmp/{self.maintenance_required[0]['code']}QRCode.png", -1, 450)
            img = Gtk.Image.new_from_pixbuf(pixbuf)

        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Confirm maintenance was performed") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)
        second_label = self._screen.gtk.Label("")
        second_label.set_margin_top(20)
        second_label.set_margin_left(10)
        second_label.set_margin_right(10)
        second_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        second_label.set_line_wrap(True)
        second_label.set_markup(
            "<span size='small'>" + _("Do not ignore regular maintenance of your printer.") + "</span>")
        self.content.add(second_label)

        button = self._screen.gtk.Button(label=_("Mark as done"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.mark_done)
        self.content.add(button)
        button = self._screen.gtk.Button(label=_("Go Back"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self.go_back)
        self.content.add(button)

    def go_back(self, widget):
        if self.called_from_panel:
            self._screen._menu_go_back()
        else:
            self.wizard_manager.set_step(CheckMaintenance(self._screen))

    def mark_done(self, widget):
        maintenance = self.maintenance_required[0]
        self._screen.maintenance.reset_maintenance(maintenance)

        if self.called_from_panel:
            self._screen._menu_go_back()
        else:
            self.maintenance_required = self.maintenance_required[1:]
            self.wizard_manager.set_wizard_data("maintenance_required", self.maintenance_required)
            self.wizard_manager.set_step(CheckMaintenance(self._screen))