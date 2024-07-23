import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango

from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return SplashScreenPanel(*args)


class SplashScreenPanel(ScreenPanel):

    def __init__(self, screen, title):
        super().__init__(screen, title)
        self.is_shutdown = False
        self.image_warning = self._gtk.Image("warning", self._gtk.content_width * .9, self._gtk.content_height * .5)
        self.image_connecting = self._gtk.Image("info", self._gtk.content_width * .9, self._gtk.content_height * .5)
        self.labels['text'] = Gtk.Label(_("Initializing printer..."))
        self.labels['text'].set_line_wrap(True)
        self.labels['text'].set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.labels['text'].set_halign(Gtk.Align.CENTER)
        self.labels['text'].set_valign(Gtk.Align.CENTER)

        self.labels['menu'] = self._gtk.Button("settings", _("Menu"), "color4", 2)
        self.labels['menu'].connect("clicked", self._screen._go_to_submenu, "")
        self.labels['firmware_restart'] = self._gtk.Button("refresh", _("Firmware Restart"), "color2")
        self.labels['firmware_restart'].connect("clicked", self.firmware_restart)
        self.labels['retry'] = self._gtk.Button("load", _('Retry'), "color3")
        self.labels['retry'].connect("clicked", self.retry)

        self.labels['actions'] = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.labels['actions'].set_hexpand(True)
        self.labels['actions'].set_vexpand(False)
        self.labels['actions'].set_halign(Gtk.Align.CENTER)
        self.labels['actions'].set_homogeneous(True)
        self.labels['actions'].set_size_request(self._gtk.content_width, -1)

        scroll = self._gtk.ScrolledWindow()
        scroll.set_hexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll.add(self.scroll_box)
        self.scroll_box.add(self.labels['text'])

        self.temperature_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.heaters = {}
        self.heater_labels = {}

        self.image_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        info.pack_start(self.image_box, False, True, 8)
        info.pack_end(scroll, True, True, 8)

        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main.pack_start(info, True, True, 8)
        main.pack_end(self.labels['actions'], False, False, 0)

        self.show_restart_buttons()

        self.content.add(main)

    def process_update(self, action, data):
        if action != "notify_status_update":
            return

        for heater in self.heaters:
            if heater in data:
                self.heater_labels[heater].set_label(f"{heater}: {data[heater]['temperature']:.1f}°C / "
                                    f"{self.heaters[heater]['min_temp']}°C to {self.heaters[heater]['max_temp']}°C")


    def update_image(self, image):
        for child in self.image_box.get_children():
            self.image_box.remove(child)
        self.image_box.add(image)
        self.content.show_all()

    def update_text(self, text:str):
        if text.startswith("Klipper has shut down"):
            self.is_shutdown = True
        else:
            self.is_shutdown = False
        if "ADC out of range" in text and self.temperature_info not in self.scroll_box.get_children():
            self.scroll_box.add(self.temperature_info)
        elif "ADC out of range" not in text and self.temperature_info in self.scroll_box.get_children():
            self.scroll_box.remove(self.temperature_info)
        self.labels['text'].set_label(f"{text}")
        self.show_restart_buttons()
        if text.startswith("Connecting"):
            self.update_image(self.image_connecting)
        else:
            self.update_image(self.image_warning)

    def clear_action_bar(self):
        for child in self.labels['actions'].get_children():
            self.labels['actions'].remove(child)

    def show_restart_buttons(self):

        self.clear_action_bar()
        if self.ks_printer_cfg is not None and self._screen._ws.connected:
            power_devices = self.ks_printer_cfg.get("power_devices", "")
            if power_devices and self._printer.get_power_devices():
                logging.info(f"Associated power devices: {power_devices}")
                self.add_power_button(power_devices)

        if self._screen.initialized:
            self.labels['actions'].add(self.labels['firmware_restart'])
        self.labels['actions'].add(self.labels['menu'])
        if (self._screen._ws and not self._screen._ws.connecting
            or self._screen.reinit_count > self._screen.max_retries) and not self.is_shutdown:
            self.labels['actions'].add(self.labels['retry'])
        self.labels['actions'].show_all()

    def add_power_button(self, powerdevs):
        self.labels['power'] = self._gtk.Button("shutdown", _("Power On Printer"), "color3")
        self.labels['power'].connect("clicked", self._screen.power_devices, powerdevs, True)
        self.check_power_status()
        self.labels['actions'].add(self.labels['power'])

    def activate(self):
        self.check_power_status()
        self._screen.base_panel.show_heaters(False)
        self._screen.base_panel.show_estop(False)

        # rebuild heater debug
        heaters = self._printer.get_heaters() + self._printer.get_tools()
        self.heaters = {}
        self.heater_labels = {}
        config = self._printer.data["configfile"]["config"]
        for child in self.temperature_info.get_children():
            self.temperature_info.remove(child)
        for heater in heaters:
            self.heaters[heater] = {"min_temp": config[heater]["min_temp"] if "min_temp" in config[heater] else None,
                                    "max_temp": config[heater]["max_temp"] if "max_temp" in config[heater] else None}
            self.heater_labels[heater] = Gtk.Label(heater)
            self.temperature_info.add(self.heater_labels[heater])

    def check_power_status(self):
        if 'power' in self.labels:
            devices = self._printer.get_power_devices()
            if devices is not None:
                for device in devices:
                    if self._printer.get_power_device_status(device) == "off":
                        self.labels['power'].set_sensitive(True)
                        break
                    elif self._printer.get_power_device_status(device) == "on":
                        self.labels['power'].set_sensitive(False)

    def firmware_restart(self, widget):
        self._screen._ws.klippy.restart_firmware()

    def retry(self, widget):
        self.update_text((_("Connecting to %s") % self._screen.connecting_to_printer))
        if self._screen._ws and not self._screen._ws.connecting:
            self._screen._ws.retry()
        else:
            self._screen.reinit_count = 0
            self._screen.init_printer()
        self.show_restart_buttons()
