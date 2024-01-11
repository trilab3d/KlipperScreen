import logging
import os
from enum import Enum
import contextlib

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel

class STATE(Enum):
    STARTED = 0
    WAIT_FOR_PROFILE = 1
    HEATING = 2
    UNLOADING = 3
    DONE = 4

def create_panel(*args):
    return LoadFilamentPanel(*args)

class LoadFilamentPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        self.screen = screen
        self.preheat_options = self._screen._config.get_preheat_options()
        self.max_head_temp = float(self.screen.printer.data['configfile']["config"]["extruder"]["max_temp"]) - 10
        logging.info(self.preheat_options)
        self.do_schedule_refresh = True
        self.state = STATE.STARTED
        self.waiting_for_unload_start = False

        self.prusament_img = self._gtk.Image("prusament", self._gtk.content_width * .9, self._gtk.content_height * .5)
        self.load_guide_img = self._gtk.Image("load_guide", self._gtk.content_width * .9, self._gtk.content_height * .5)

        self.heaters = []
        self.heaters.extend(iter(self._printer.get_tools()))
        self.show_preheat = True
        for h in self._printer.get_heaters():
            if not h.endswith("panel"):
                self.heaters.append(h)
        logging.info(self.heaters)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.img_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.img_box.set_hexpand(True)

        self.status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.add(self.status_box)

        self.content.add(box)

        GLib.timeout_add_seconds(1, self._update_loop)

    def activate(self):
        self.do_schedule_refresh = True
        GLib.timeout_add_seconds(1, self._update_loop)

    def deactivate(self):
        self.state = STATE.STARTED
        self.do_schedule_refresh = False

    def _update_loop(self):
        if self.state == STATE.STARTED:
            save_variables = self._screen.printer.data['save_variables']['variables'] \
                if 'save_variables' in self._screen.printer.data else None
            for ch in self.status_box.get_children():
                self.status_box.remove(ch)
            for ch in self.img_box.get_children():
                self.img_box.remove(ch)
            self.img_box.add(self.prusament_img)
            self.status_box.add(self.img_box)
            self.labels["select_material_label"] = self._gtk.Label("")
            self.labels["select_material_label"].set_margin_top(20)
            scroll = self._gtk.ScrolledWindow()
            if (save_variables and "loaded_filament" in save_variables and save_variables["loaded_filament"] in self.preheat_options):
                self.labels["select_material_label"].set_markup(
                    "<span size='large'>" + _(_("Is the loaded material ") + f"{save_variables['loaded_filament']}?") + "</span>")
                grid = self._gtk.HomogeneousGrid()
                yes = self._gtk.Button(label=_(_("Yes, unload ") + save_variables['loaded_filament']), style=f"color1")
                yes.connect("clicked", self.set_temperature, save_variables["loaded_filament"])
                yes.set_vexpand(False)
                grid.attach(yes, 0,0, 1, 1)
                yes = self._gtk.Button(label=_("No, select a different material"), style=f"color1")
                yes.connect("clicked", self.set_filament_unknown)
                yes.set_vexpand(False)
                grid.attach(yes, 0, 1, 1, 1)
                scroll.add(grid)
            else:
                self.labels["select_material_label"].set_markup(
                    "<span size='large'>" + _("Which material is loaded in printer?") + "</span>")

                self.labels["preheat_grid"] = self._gtk.HomogeneousGrid()
                i = 0
                for option in self.preheat_options:
                    if (option != "cooldown" and "extruder" in self.preheat_options[option]
                            and self.preheat_options[option]["extruder"] <= self.max_head_temp):
                        self.labels[option] = self._gtk.Button(label=option, style=f"color{(i % 4) + 1}")
                        self.labels[option].connect("clicked", self.set_temperature, option)
                        self.labels[option].set_vexpand(False)
                        self.labels['preheat_grid'].attach(self.labels[option], (i % 2), int(i / 2), 1, 1)
                        i += 1
                scroll.add(self.labels["preheat_grid"])
            self.status_box.add(self.labels['select_material_label'])
            self.status_box.add(scroll)
            self.state = STATE.WAIT_FOR_PROFILE
        elif self.state == STATE.WAIT_FOR_PROFILE:
            pass
        elif self.state == STATE.HEATING:
            extruder = self.fetch_extruder()
            if extruder["target"] > 0:
                fract = extruder["temperature"]/extruder["target"]
                self.labels['temperature_progressbar'].set_fraction(fract)
                if extruder["temperature"] >= extruder["target"]:
                    self._screen._ws.klippy.gcode_script(f"SAVE_GCODE_STATE NAME=LOAD_FILAMENT")
                    self._screen._ws.klippy.gcode_script(f"M83")
                    self._screen._ws.klippy.gcode_script(f"G0 E3.0 F300")
                    self._screen._ws.klippy.gcode_script(f"_FILAMENT_RETRACT")
                    self._screen._ws.klippy.gcode_script(f"G4 P4000")
                    self._screen._ws.klippy.gcode_script(f"G1 E-30.0 F900")
                    self._screen._ws.klippy.gcode_script(f"RESTORE_GCODE_STATE NAME=LOAD_FILAMENT")

                    for ch in self.status_box.get_children():
                        self.status_box.remove(ch)

                    for ch in self.img_box.get_children():
                        self.img_box.remove(ch)
                    self.img_box.add(self.prusament_img)
                    self.status_box.add(self.img_box)

                    self.labels["loading_label"] = self._gtk.Label("")
                    self.labels["loading_label"].set_margin_top(20)
                    self.labels["loading_label"].set_markup(
                        "<span size='large'>" + _("Filament is unloading...") + "</span>")
                    self.status_box.add(self.labels['loading_label'])
                    self._screen.show_all()

                    self.waiting_for_unload_start = True
                    self.state = STATE.UNLOADING
        elif self.state == STATE.UNLOADING:
            it = self.fetch_idle_timeout()
            if not it["state"] == "Ready":
                self.waiting_for_unload_start = False
            if it["state"] == "Ready" and not self.waiting_for_unload_start:
                for ch in self.status_box.get_children():
                    self.status_box.remove(ch)
                for ch in self.img_box.get_children():
                    self.img_box.remove(ch)
                self.img_box.add(self.load_guide_img)
                self.status_box.add(self.img_box)
                self.labels["confirm_label"] = self._gtk.Label("")
                self.labels["confirm_label"].set_margin_top(20)
                self.labels["confirm_label"].set_markup(
                    "<span size='large'>" + _("Filament unloaded successfully") + "</span>")
                self.status_box.add(self.labels['confirm_label'])
                self.labels["load_button"] = self._gtk.Button(label=_("Load new material"), style=f"color1")
                self.labels["load_button"].set_vexpand(False)
                self.labels["load_button"].connect("clicked", self.got_to_load)
                self.status_box.add(self.labels['load_button'])
                self.labels["cooldown_button"] = self._gtk.Button(label=_("Cooldown and Close"), style=f"color1")
                self.labels["cooldown_button"].set_vexpand(False)
                self.labels["cooldown_button"].connect("clicked", self.cooldown_pressed)
                self.status_box.add(self.labels['cooldown_button'])
                self.labels["back_button"] = self._gtk.Button(label=_("Close"), style=f"color1")
                self.labels["back_button"].set_vexpand(False)
                self.labels["back_button"].connect("clicked", self._screen._menu_go_back, True)
                self.status_box.add(self.labels['back_button'])
                self.state = STATE.DONE
        elif self.state == STATE.DONE:
            pass
        self._screen.show_all()
        return self.do_schedule_refresh or self.state == STATE.HEATING
    def fetch_extruder(self):
        extruder = self.screen.printer.data['extruder']
        return extruder

    def fetch_idle_timeout(self):
        idle_timeout = self.screen.printer.data['idle_timeout']
        return idle_timeout

    def set_filament_unknown(self, widget):
        self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=loaded_filament VALUE='\"unknown\"'")
        self.state = STATE.STARTED

    def set_temperature(self, widget, setting):
        if len(self.heaters) == 0:
            self._screen.show_popup_message(_("Nothing selected"))
        else:
            for heater in self.heaters:
                logging.info(f"Looking for settings for heater {heater}")
                target = None
                max_temp = float(self._printer.get_config_section(heater)['max_temp'])
                name = heater.split()[1] if len(heater.split()) > 1 else heater
                with contextlib.suppress(KeyError):
                    for i in self.preheat_options[setting]:
                        logging.info(f"{self.preheat_options[setting]}")
                        if i == name:
                            # Assign the specific target if available
                            target = self.preheat_options[setting][name]
                            logging.info(f"name match {name}")
                        elif i == heater:
                            target = self.preheat_options[setting][heater]
                            logging.info(f"heater match {heater}")
                if target is None and setting == "cooldown" and not heater.startswith('temperature_fan '):
                    target = 0
                if heater.startswith('extruder'):
                    if self.validate(heater, target, max_temp):
                        self._screen._ws.klippy.set_tool_temp(self._printer.get_tool_number(heater), target)
                elif heater.startswith('heater_generic '):
                    if target is None:
                        with contextlib.suppress(KeyError):
                            target = self.preheat_options[setting]["heater_generic"]
                    if self.validate(heater, target, max_temp):
                        self._screen._ws.klippy.set_heater_temp(name, target)
                elif heater.startswith('temperature_fan '):
                    if target is None:
                        with contextlib.suppress(KeyError):
                            target = self.preheat_options[setting]["temperature_fan"]
                    if self.validate(heater, target, max_temp):
                        self._screen._ws.klippy.set_temp_fan_temp(name, target)

        self.state = STATE.HEATING
        for ch in self.status_box.get_children():
            self.status_box.remove(ch)
        for ch in self.img_box.get_children():
            self.img_box.remove(ch)
        self.img_box.add(self.prusament_img)
        self.status_box.add(self.img_box)
        self.labels["heating_label"] = self._gtk.Label("")
        self.labels["heating_label"].set_margin_top(60)
        self.labels["heating_label"].set_markup(
            "<span size='large'>" + _("Wait for temperature...") + "</span>")
        self.status_box.add(self.labels['heating_label'])
        self.labels['temperature_progressbar'] = Gtk.ProgressBar()
        #self.labels['temperature_progressbar'].set_fraction(0)
        self.labels['temperature_progressbar'].set_show_text(False)
        self.labels['temperature_progressbar'].set_hexpand(True)
        self.status_box.add(self.labels['temperature_progressbar'])
        self.labels["cancel_button"] = self._gtk.Button(label=_("Cancel"), style=f"color1")
        self.labels["cancel_button"].set_vexpand(False)
        self.labels["cancel_button"].connect("clicked", self.cancel_pressed)
        self.status_box.add(self.labels['cancel_button'])
        self._screen.show_all()

    def cancel_pressed(self, widget):
        for ch in self.status_box.get_children():
            self.status_box.remove(ch)

        self.state = STATE.STARTED

    def cooldown_pressed(self, widget):
        for heater in self.heaters:
            logging.info(f"Cooling Down heater {heater}")
            name = heater.split()[1] if len(heater.split()) > 1 else heater
            target = 0
            if heater.startswith('extruder'):
                self._screen._ws.klippy.set_tool_temp(self._printer.get_tool_number(heater), target)
            elif heater.startswith('heater_bed'):
                self._screen._ws.klippy.set_bed_temp(target)
            elif heater.startswith('heater_chamber'):
                self._screen._ws.klippy.set_chamber_temp(target)
            elif heater.startswith('heater_generic '):
                self._screen._ws.klippy.set_heater_temp(name, target)
            elif heater.startswith('temperature_fan '):
                self._screen._ws.klippy.set_temp_fan_temp(name, target)
        self._screen._menu_go_back(True)

    def got_to_load(self, widget):
        self._screen.show_panel(f"Load", "load_filament", "Load", 1, False)

    def validate(self, heater, target=None, max_temp=None):
        if target is not None and max_temp is not None:
            if 0 <= target <= max_temp:
                self._printer.set_dev_stat(heater, "target", target)
                return True
            elif target > max_temp:
                self._screen.show_popup_message(_("Can't set above the maximum:") + f' {max_temp}')
                return False
        logging.debug(f"Invalid {heater} Target:{target}/{max_temp}")
        return False

