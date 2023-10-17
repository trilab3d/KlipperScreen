import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return LightPanel(*args)


class LightPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        self.devices = {}
        # Create a grid for all devices
        self.labels['devices'] = Gtk.Grid()
        self.labels['devices'].set_valign(Gtk.Align.CENTER)

        self.load_lights()

        scroll = self._gtk.ScrolledWindow()
        scroll.add(self.labels['devices'])

        self.content.add(scroll)

    def process_update(self, action, data):
        if action != "notify_status_update":
            return

        for light in self.devices:
            if light in data and "value" in data[light]:
                self.update_light_val(None, light, self._printer.get_light_val(light))

    def update_light_val(self, widget, light, speed):
        if light not in self.devices:
            return

        if self.devices[light]['scale'].has_grab():
            return
        self.devices[light]["speed"] = round(float(speed) * 100)
        self.devices[light]['scale'].disconnect_by_func(self.set_light_val)
        self.devices[light]['scale'].set_value(self.devices[light]["speed"])
        self.devices[light]['scale'].connect("button-release-event", self.set_light_val, light)

        if widget is not None:
            self.set_light_val(None, None, light)

    def add_light(self, light):

        logging.info(f"Adding light: {light}")
        name = Gtk.Label()
        light_name = light.split()[1]
        light_name_pretty = ' '.join(x.capitalize() for x in light_name.split('_'))
        name.set_markup(f"\n<big><b>{light_name_pretty}</b></big>\n")
        name.set_hexpand(True)
        name.set_vexpand(True)
        name.set_halign(Gtk.Align.START)
        name.set_valign(Gtk.Align.CENTER)
        name.set_line_wrap(True)
        name.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        fan_col = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        stop_btn = self._gtk.Button("light-off", _("Off"), "color1")
        max_btn = self._gtk.Button("light", _("On"), "color2")
        stop_btn.set_hexpand(False)
        stop_btn.connect("clicked", self.update_light_val, light, 0)
        max_btn.set_hexpand(False)
        max_btn.connect("clicked", self.update_light_val, light, 100)

        value = float(self._printer.get_light_val(light))
        value = round(value * 100)
        scale = Gtk.Scale.new_with_range(orientation=Gtk.Orientation.HORIZONTAL, min=0, max=100, step=1)
        scale.set_value(value)
        scale.set_digits(0)
        scale.set_hexpand(True)
        scale.set_has_origin(True)
        scale.get_style_context().add_class("fan_slider")
        scale.connect("button-release-event", self.set_light_val, light)
        fan_col.add(stop_btn)
        fan_col.add(scale)
        fan_col.add(max_btn)

        light_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        light_row.add(name)
        light_row.add(fan_col)

        self.devices[light] = {
            "scale": scale,
            "value": value,
        }

        devices = sorted(self.devices)
        pos = devices.index(light)

        self.labels['devices'].insert_row(pos)
        self.labels['devices'].attach(light_row, 0, pos, 1, 1)
        self.labels['devices'].show_all()

    def load_lights(self):
        lights = self._printer.get_lights()
        for light in lights:
            # Support for hiding devices by name
            name = light.split()[1] if len(light.split()) > 1 else light
            if name.startswith("_"):
                continue
            self.add_light(light)

    def set_light_val(self, widget, event, light):
        logging.info(f"Light: {light}")
        logging.info(f"object: {self.devices[light]}")
        logging.info(f"scale: {self.devices[light]['scale']}")
        value = self.devices[light]['scale'].get_value()

        self._screen._ws.klippy.gcode_script(f"SET_LED LED={light.split()[1]} WHITE={float(value) / 100}")
        # Check the speed in case it wasn't applied
        GLib.timeout_add_seconds(1, self.check_light_val, light)

    def check_light_val(self, light):
        self.update_light_val(None, light, self._printer.get_light_val(light))
        return False
