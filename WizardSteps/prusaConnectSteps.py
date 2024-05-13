import logging
import contextlib

import gi
import requests
import qrcode
from io import BytesIO

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango, GdkPixbuf

from WizardSteps.baseWizardStep import BaseWizardStep
from WizardSteps import loadWizardSteps, servicePositionSteps
from WizardSteps.wizardCommons import *

CONNECT_PARAMS={
    "connect": {
		"hostname": "connect.prusa3d.com",
		"tls": True,
		"port": 443
	}
}

class GetStatus(BaseWizardStep):
    def __init__(self, screen, load_var=True):
        super().__init__(screen)
        self.printer_config = self._screen.printers[0][list(self._screen.printers[0])[0]]

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945, 450)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Getting Prusa Connect state") + "</span>")
        self.content.add(heating_label)
        self.update_loop()

    def update_loop(self):
        r = requests.get(f"http://{self.printer_config['moonraker_host']}:{self.printer_config['prusa_connect_port']}/connection").json()
        if "registration" in r:
            if r["registration"] == "NO_REGISTRATION":
                self.wizard_manager.set_step(InitConnect(self._screen))
            elif r["registration"] == "IN_PROGRESS":
                self.wizard_manager.set_step(InProgress(self._screen))
            elif r["registration"] == "FINISHED":
                self.wizard_manager.set_step(Done(self._screen))


class InitConnect(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("disconected", self._screen.gtk.content_width * .945, 450)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Prusa Connect not configured") + "</span>")
        self.content.add(heating_label)
        continue_button = self._screen.gtk.Button(label=_("Configure Prusa Connect"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(InProgress(self._screen))

class InProgress(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.printer_config = self._screen.printers[0][list(self._screen.printers[0])[0]]
        r = requests.post(f"http://{self.printer_config['moonraker_host']}:{self.printer_config['prusa_connect_port']}/connection",json=CONNECT_PARAMS).json()
        self.code = r["code"]
        self.url = r["url"]
        logging.info(f"Continue on {self.url}")
    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.url)
        qr.make(fit=True)
        qr_pil = qr.make_image(fill_color="black", back_color="white")
        qr_pil.save("/tmp/ConnectQRCode.png")
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size("/tmp/ConnectQRCode.png", -1, -1)

        img = Gtk.Image.new_from_pixbuf(pixbuf)
        self.content.add(img)

        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='xx-large'>" + self.code + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)

        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Scan this QR code and continue on your mobile device.") + "\n" +
            _("Alternatively, you can visit") + " <span color='#7777FF'>prusa.io/add</span> " +
            _("and provide code manually") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)

    def update_loop(self):
        r = requests.get(f"http://{self.printer_config['moonraker_host']}:{self.printer_config['prusa_connect_port']}/connection").json()
        if "registration" in r:
            if r["registration"] == "FINISHED":
                self.wizard_manager.set_step(Done(self._screen))

class Done(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945, 450)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Your Connect is configured successfully") + "</span>")
        self.content.add(heating_label)
