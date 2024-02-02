import logging
import re
import contextlib

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return FineTunePanel(*args)


class FineTunePanel(ScreenPanel):
    bs_deltas = ["0.01", "0.05"]
    bs_delta = "0.01"
    speed = extrusion = 100

    def __init__(self, screen, title):
        super().__init__(screen, title)

        grid = self._gtk.HomogeneousGrid()
        grid.set_row_homogeneous(False)

        self.labels['z+'] = self._gtk.Button("z-farther", "Z+", "color1")
        self.labels['z-'] = self._gtk.Button("z-closer", "Z-", "color1")
        self.labels['zoffset'] = self._gtk.Button("refresh", '  0.00' + _("mm"),
                                                  "color1", self.bts, Gtk.PositionType.LEFT, 1)
        self.labels['speed+'] = self._gtk.Button("speed+", _("Speed +"), "color3")
        self.labels['speed-'] = self._gtk.Button("speed-", _("Speed -"), "color3")
        self.labels['speedfactor'] = self._gtk.Button("refresh", "  100%",
                                                      "color3", self.bts, Gtk.PositionType.LEFT, 1)

        self.labels['extruder+'] = self._gtk.Button("extruder+", _("Hotend +"), "color4")
        self.labels['extruder-'] = self._gtk.Button("extruder-", _("Hotend -"), "color4")
        self.labels['extruder'] = self._gtk.Button(None, "  100%",
                                                        "color4", self.bts, Gtk.PositionType.LEFT, 1)
        self.labels['extruder'].set_sensitive(False)

        self.labels['heater_bed+'] = self._gtk.Button("bed+", _("Bed +"), "color4")
        self.labels['heater_bed-'] = self._gtk.Button("bed-", _("Bed -"), "color4")
        self.labels['heater_bed'] = self._gtk.Button(None, "  100%",
                                                        "color4", self.bts, Gtk.PositionType.LEFT, 1)
        self.labels['heater_bed'].set_sensitive(False)

        self.labels['heater_chamber+'] = self._gtk.Button("chamber+", _("Chamber +"), "color4")
        self.labels['heater_chamber-'] = self._gtk.Button("chamber-", _("Chamber -"), "color4")
        self.labels['heater_chamber'] = self._gtk.Button(None, "  100%",
                                                        "color4", self.bts, Gtk.PositionType.LEFT, 1)
        self.labels['heater_chamber'].set_sensitive(False)

        self.labels['extrude+'] = self._gtk.Button("flow+", _("Extrusion +"), "color4")
        self.labels['extrude-'] = self._gtk.Button("flow-", _("Extrusion -"), "color4")
        self.labels['extrudefactor'] = self._gtk.Button("refresh", "  100%",
                                                        "color4", self.bts, Gtk.PositionType.LEFT, 1)

        grid.attach(self.labels['z-'], 0, 0, 1, 1)
        grid.attach(self.labels['zoffset'], 1, 0, 1, 1)
        grid.attach(self.labels['z+'], 2, 0, 1, 1)
        grid.attach(self.labels['speed-'], 0, 1, 1, 1)
        grid.attach(self.labels['speedfactor'], 1, 1, 1, 1)
        grid.attach(self.labels['speed+'], 2, 1, 1, 1)
        grid.attach(self.labels['extruder-'], 0, 2, 1, 1)
        grid.attach(self.labels['extruder'], 1, 2, 1, 1)
        grid.attach(self.labels['extruder+'], 2, 2, 1, 1)
        grid.attach(self.labels['heater_bed-'], 0, 3, 1, 1)
        grid.attach(self.labels['heater_bed'], 1, 3, 1, 1)
        grid.attach(self.labels['heater_bed+'], 2, 3, 1, 1)
        grid.attach(self.labels['heater_chamber-'], 0, 4, 1, 1)
        grid.attach(self.labels['heater_chamber'], 1, 4, 1, 1)
        grid.attach(self.labels['heater_chamber+'], 2, 4, 1, 1)
        grid.attach(self.labels['extrude-'], 0, 5, 1, 1)
        grid.attach(self.labels['extrudefactor'], 1, 5, 1, 1)
        grid.attach(self.labels['extrude+'], 2, 5, 1, 1)

        self.labels['z+'].connect("clicked", self.change_babystepping, "+")
        self.labels['zoffset'].connect("clicked", self.change_babystepping, "reset")
        self.labels['z-'].connect("clicked", self.change_babystepping, "-")
        self.labels['speed+'].connect("clicked", self.change_speed, "+")
        self.labels['speedfactor'].connect("clicked", self.change_speed, "reset")
        self.labels['speed-'].connect("clicked", self.change_speed, "-")
        self.labels['extruder+'].connect("clicked", self.change_temperature, "extruder", "+")
        self.labels['extruder-'].connect("clicked", self.change_temperature, "extruder", "-")
        self.labels['heater_bed+'].connect("clicked", self.change_temperature, "heater_bed", "+")
        self.labels['heater_bed-'].connect("clicked", self.change_temperature, "heater_bed", "-")
        self.labels['heater_chamber+'].connect("clicked", self.change_temperature, "heater_chamber", "+")
        self.labels['heater_chamber-'].connect("clicked", self.change_temperature, "heater_chamber", "-")
        self.labels['extrude+'].connect("clicked", self.change_extrusion, "+")
        self.labels['extrudefactor'].connect("clicked", self.change_extrusion, "reset")
        self.labels['extrude-'].connect("clicked", self.change_extrusion, "-")

        self.content.add(grid)

    def activate(self):
        for heater in ["extruder", "heater_bed", "heater_chamber"]:
            target = self._printer.get_dev_stat(heater, "target")
            self.labels[heater].set_label(f'{target} °C')

    def process_update(self, action, data):

        if action != "notify_status_update":
            return

        if "gcode_move" in data:
            if "homing_origin" in data["gcode_move"]:
                self.labels['zoffset'].set_label(f'  {data["gcode_move"]["homing_origin"][2]:.3f}mm')
            if "extrude_factor" in data["gcode_move"]:
                self.extrusion = round(float(data["gcode_move"]["extrude_factor"]) * 100)
                self.labels['extrudefactor'].set_label(f"  {self.extrusion:3}%")
            if "speed_factor" in data["gcode_move"]:
                self.speed = round(float(data["gcode_move"]["speed_factor"]) * 100)
                self.labels['speedfactor'].set_label(f"  {self.speed:3}%")

    def change_babystepping(self, widget, direction):
        if direction == "reset":
            self.labels['zoffset'].set_label('  0.00mm')
            self._screen._ws.klippy.gcode_script("SET_GCODE_OFFSET Z=0 MOVE=1")
        elif direction in ["+", "-"]:
            with contextlib.suppress(KeyError):
                z_offset = float(self._printer.data["gcode_move"]["homing_origin"][2])
                if direction == "+":
                    z_offset += float(self.bs_delta)
                else:
                    z_offset -= float(self.bs_delta)
                self.labels['zoffset'].set_label(f'  {z_offset:.3f}mm')
            self._screen._ws.klippy.gcode_script(f"SET_GCODE_OFFSET Z_ADJUST={direction}{self.bs_delta} MOVE=1")

    def change_extrusion(self, widget, direction):
        if direction == "+":
            self.extrusion += 1
        elif direction == "-":
            self.extrusion -= 1
        elif direction == "reset":
            self.extrusion = 100

        self.extrusion = max(self.extrusion, 1)
        self.labels['extrudefactor'].set_label(f"  {self.extrusion:3}%")
        self._screen._ws.klippy.gcode_script(KlippyGcodes.set_extrusion_rate(self.extrusion))

    def change_speed(self, widget, direction):
        if direction == "+":
            self.speed += 5
        elif direction == "-":
            self.speed -= 5
        elif direction == "reset":
            self.speed = 100

        self.speed = max(self.speed, 1)
        self.labels['speedfactor'].set_label(f"  {self.speed:3}%")
        self._screen._ws.klippy.gcode_script(KlippyGcodes.set_speed_rate(self.speed))

    def change_temperature(self, widget, heater, direction):
        tempdelta = 1
        if direction == "-":
            tempdelta = -1

        if heater == "extruder" or heater == "heater_bed":
            tempdelta *= 5

        target = self._printer.get_dev_stat(heater, "target") + tempdelta
        max_temp = int(float(self._printer.get_config_section(heater)['max_temp']))
        if target > max_temp:
            target = max_temp
            self._screen.show_popup_message(_("Can't set above the maximum:") + f' {target}')

        self._screen._ws.klippy.gcode_script(f"SET_HEATER_TEMPERATURE HEATER={heater} TARGET={target}")
        self.labels[heater].set_label(f'{target} °C')

