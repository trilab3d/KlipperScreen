import logging
import contextlib

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from WizardSteps.baseWizardStep import BaseWizardStep

currently_loading = ""
speed_request = 1


class Cancelable():
    def on_cancel(self):
        self._screen._ws.klippy.gcode_script("_FILAMENT_RETRACT")
        self._screen._ws.klippy.gcode_script("_RESTORE_TEMPERATURE")


class SelectFilament(BaseWizardStep):
    def __init__(self, screen, load_var = False):
        super().__init__(screen)

        self.preheat_options = self._screen._config.get_preheat_options()
        self.max_head_temp = float(self._screen.printer.data['configfile']["config"]["extruder"]["max_temp"]) - 10

        self.load_var = load_var

        self.heaters = []
        self.heaters.extend(iter(self._screen.printer.get_tools()))
        for h in self._screen.printer.get_heaters():
            if not h.endswith("panel"):
                self.heaters.append(h)

        self.next_step = WaitForTemperature
        self.label = _("Which material would you like to load?")
        self.label2 = _("Would you like to load ")

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("prusament", self._screen.gtk.content_width * .945, 450)
        self.content.add(img)

        if (self.load_var and 'save_variables' in self._screen.printer.data and
                "loaded_filament" in self._screen.printer.data['save_variables']['variables'] and
                self._screen.printer.data['save_variables']['variables']["loaded_filament"] in self.preheat_options):
            save_variables = self._screen.printer.data['save_variables']['variables']
            label = self._screen.gtk.Label("")
            label.set_margin_top(20)
            label.set_markup(
                "<span size='large'>" + (
                    self.label2 + f"{save_variables['loaded_filament']}?") + "</span>")
            self.content.add(label)
            grid = self._screen.gtk.HomogeneousGrid()
            yes = self._screen.gtk.Button(label=_("Yes"), style=f"color1")
            yes.connect("clicked", self.set_temperature, save_variables["loaded_filament"])
            yes.set_vexpand(False)
            grid.attach(yes, 0, 0, 1, 1)
            no = self._screen.gtk.Button(label=_("No, select a different material"), style=f"color1")
            no.connect("clicked", self.set_filament_unknown)
            no.set_vexpand(False)
            grid.attach(no, 0, 1, 1, 1)
            self.content.add(grid)
        else:
            label = self._screen.gtk.Label("")
            label.set_margin_top(20)
            label.set_markup(
                "<span size='large'>" + self.label + "</span>")
            self.content.add(label)
            preheat_grid = self._screen.gtk.HomogeneousGrid()
            i = 0
            for option in self.preheat_options:
                if (option != "cooldown" and "extruder" in self.preheat_options[option]
                        and self.preheat_options[option]["extruder"] <= self.max_head_temp):
                    option_btn = self._screen.gtk.Button(label=option, style=f"color{(i % 4) + 1}")
                    option_btn.connect("clicked", self.set_temperature, option)
                    option_btn.set_vexpand(False)
                    preheat_grid.attach(option_btn, (i % 2), int(i / 2), 1, 1)
                    i += 1
            scroll = self._screen.gtk.ScrolledWindow()
            scroll.add(preheat_grid)
            self.content.add(scroll)

    def set_temperature(self, widget, setting):
        self._screen._ws.klippy.gcode_script("_SAVE_TEMPERATURE")
        global currently_loading
        currently_loading = setting
        if len(self.heaters) == 0:
            self._screen.show_popup_message(_("Nothing selected"))
        else:
            for heater in self.heaters:
                logging.info(f"Looking for settings for heater {heater}")
                target = None
                max_temp = float(self._screen.printer.get_config_section(heater)['max_temp'])
                target_actual = self._screen.printer.data[heater]["target"]
                name = heater.split()[1] if len(heater.split()) > 1 else heater
                with contextlib.suppress(KeyError):
                    for i in self.preheat_options[setting]:
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
                    if setting == 'cooldown' or self.validate(heater, target, max_temp, target_actual):
                        self._screen._ws.klippy.set_tool_temp(self._screen.printer.get_tool_number(heater), target)
                elif heater.startswith('heater_bed'):
                    if target is None:
                        with contextlib.suppress(KeyError):
                            target = self.preheat_options[setting]["bed"]
                    if setting == 'cooldown' or self.validate(heater, target, max_temp, target_actual):
                        self._screen._ws.klippy.set_bed_temp(target)
                elif heater.startswith('heater_chamber'):
                    if target is None:
                        with contextlib.suppress(KeyError):
                            target = self.preheat_options[setting]["chamber"]
                    if setting == 'cooldown' or self.validate(heater, target, max_temp, target_actual):
                        self._screen._ws.klippy.set_chamber_temp(target)
                elif heater.startswith('heater_generic '):
                    if target is None:
                        with contextlib.suppress(KeyError):
                            target = self.preheat_options[setting]["heater_generic"]
                    if setting == 'cooldown' or self.validate(heater, target, max_temp, target_actual):
                        self._screen._ws.klippy.set_heater_temp(name, target)
                elif heater.startswith('temperature_fan '):
                    if target is None:
                        with contextlib.suppress(KeyError):
                            target = self.preheat_options[setting]["temperature_fan"]
                    if setting == 'cooldown' or self.validate(heater, target, max_temp, target_actual):
                        self._screen._ws.klippy.set_temp_fan_temp(name, target)

            if setting == 'cooldown':
                self._screen._ws.klippy.gcode_script(f"SET_FAN_SPEED FAN=intake_flap SPEED=1")
            elif "flap" in self.preheat_options[setting]:
                self._screen._ws.klippy.gcode_script(f"SET_FAN_SPEED FAN=intake_flap SPEED={self.preheat_options[setting]['flap']}")
            global speed_request
            if setting in self.preheat_options and "speed" in self.preheat_options[setting]:
                speed_request = float(self.preheat_options[setting]["speed"])
            else:
                speed_request = 1

        self.wizard_manager.set_step(self.next_step(self._screen))

    def validate(self, heater, target=None, max_temp=None, target_actual=None):
        if target is not None and target_actual is not None and target <= target_actual:
            logging.debug(f"Actual target {target_actual} is greater or equal than target {target}. Skipping.")
            return False
        if target is not None and max_temp is not None:
            if 0 <= target <= max_temp:
                self._screen.printer.set_dev_stat(heater, "target", target)
                return True
            elif target > max_temp:
                self._screen.show_popup_message(_("Can't set above the maximum:") + f' {max_temp}')
                return False
        logging.debug(f"Invalid {heater} Target:{target}/{max_temp}")
        return False

    def set_filament_unknown(self, widget):
        self.wizard_manager.set_step(self.__class__(self._screen, False))

class WaitForTemperature(Cancelable, BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = WaitForFilamentInserted
        self.settling_counter = self.settling_counter_max = 3

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("heating", self._screen.gtk.content_width * .945,450)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Wait for temperature...") + "</span>")
        self.content.add(heating_label)
        self.temperature_progressbar = Gtk.ProgressBar()
        #self.labels['temperature_progressbar'].set_fraction(0)
        self.temperature_progressbar.set_show_text(False)
        self.temperature_progressbar.set_hexpand(True)
        self.content.add(self.temperature_progressbar)
        self.actual_temperature = self._screen.gtk.Label("0 °C")
        self.actual_temperature.set_hexpand(True)
        self.actual_temperature.set_halign(Gtk.Align.START)
        self.target_temperature = self._screen.gtk.Label("0 °C")
        self.target_temperature.set_halign(Gtk.Align.END)
        temperature_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin_start=20, margin_end=20)
        temperature_box.set_hexpand(True)
        temperature_box.add(self.actual_temperature)
        temperature_box.add(self.target_temperature)
        self.content.add(temperature_box)
        cancel_button = self._screen.gtk.Button(label=_("Cancel"), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.cancel_pressed)
        self.content.add(cancel_button)

    def update_loop(self):
        extruder = self.fetch_extruder()
        fract = extruder["temperature"]/extruder["target"] if extruder["target"] > 0 else 1
        self.temperature_progressbar.set_fraction(fract)
        self.actual_temperature.set_label(f"{extruder['temperature']:.1f} °C")
        self.target_temperature.set_label(f"{extruder['target']:.1f} °C")

        if extruder['temperature'] >= extruder['target']:
            self.settling_counter -= 1
            if self.settling_counter < 1:
                self.go_to_next()
        else:
            self.settling_counter = self.settling_counter_max

    def go_to_next(self):
        self.wizard_manager.set_step(self.next_step(self._screen))

    def fetch_extruder(self):
        extruder = self._screen.printer.data['extruder']
        return extruder

    def cancel_pressed(self, widget):
        self._screen._menu_go_back()

class WaitForFilamentInserted(Cancelable, BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = Purging
        self.filament_sensor = self._screen.printer.data['filament_switch_sensor fil_sensor']\
            if 'filament_switch_sensor fil_sensor' in self._screen.printer.data else None

        self.load_guide = self._screen.gtk.Image("load_guide_arrow", self._screen.gtk.content_width * .945,450)

        self.load_guide2 = self._screen.gtk.Image("load_guide_2_arrow", self._screen.gtk.content_width * .945,450)

        self.loaded = False
        self.update_deadtime = 0

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.img_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.img_box.set_hexpand(True)
        self.img_box.add(self.load_guide)
        self.content.add(self.img_box)

        load_label = self._screen.gtk.Label("")
        load_label.set_margin_top(20)
        load_label.set_margin_left(10)
        load_label.set_margin_right(10)
        load_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        load_label.set_line_wrap(True)
        load_label.set_markup("<span size='large'>" + _("Insert filament and press continue.") + "</span>")
        self.content.add(load_label)
        load_comment = self._screen.gtk.Label("")
        load_comment.set_margin_top(5)
        load_comment.set_margin_left(10)
        load_comment.set_margin_right(10)
        load_comment.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        load_comment.set_line_wrap(True)
        load_comment.set_markup("<span size='small'>" + _("Feed the filament fully into the extruder until it stops "
                                                          "at the gears.") + "</span>")
        self.content.add(load_comment)
        self.load_button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        self.load_button.set_vexpand(False)
        self.load_button.connect("clicked", self.load_filament_pressed)
        self.load_button.set_sensitive(False)
        self.content.add(self.load_button)

        self.fs_label = Gtk.Label()
        self.fs_label.set_markup(f"<big><b>{_('Filament sensor')}</b></big>")
        self.fs_label.set_hexpand(True)
        self.fs_label.set_vexpand(True)
        self.fs_label.set_halign(Gtk.Align.START)
        self.fs_label.set_valign(Gtk.Align.CENTER)
        self.fs_label.set_line_wrap(True)
        self.fs_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        labels.add(self.fs_label)

        dev = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        #dev.get_style_context().add_class("frame-item")
        dev.set_hexpand(True)
        dev.set_vexpand(False)
        dev.set_margin_left(20)
        dev.set_margin_right(10)
        dev.set_valign(Gtk.Align.CENTER)
        dev.add(labels)
        self.switch = Gtk.Switch()
        self.switch.connect("notify::active", self._filament_sensor_callback)
        dev.add(self.switch)

        self.content.add(dev)
        self._filament_sensor_getter()

    def update_loop(self):
        self._filament_sensor_getter()
        if self.filament_sensor and self.filament_sensor["enabled"] and not self.filament_sensor["filament_detected"]:
            self.load_button.set_sensitive(False)
        else:
            self.load_button.set_sensitive(True)

        for ch in self.img_box.get_children():
            self.img_box.remove(ch)
        if self.filament_sensor and self.filament_sensor["filament_detected"] and self.filament_sensor["enabled"]:
            self.img_box.add(self.load_guide2)
            self.load_guide2.show()
        else:
            self.img_box.add(self.load_guide)
            self.load_guide.show()

    def load_filament_pressed(self, widget):
        self.wizard_manager.set_step(self.next_step(self._screen))

    def _filament_sensor_getter(self):
        filament_sensor = self._screen.printer.data['filament_switch_sensor fil_sensor']
        #obj["label"].set_text("")
        if not self.update_deadtime:
            self.switch.set_sensitive(True)
            if self.switch.get_active() != filament_sensor["enabled"]:
                self.update_deadtime = 1
                self.switch.set_active(filament_sensor["enabled"])
        else:
            self.switch.set_sensitive(False)
            self.update_deadtime -= 1
        if filament_sensor["enabled"]:
            badge = f" (<span foreground='#00FF00'>{_('Filament')}</span>)" if filament_sensor["filament_detected"] else \
                f" (<span foreground='#FF0000'>{_('No Filament')}</span>)"
        else:
            badge = f" (<span foreground='#666666'>{_('Disabled')}</span>)"
        self.fs_label.set_markup(f"<big><b>{_('Filament Sensor')}{badge}</b></big>")

    def _filament_sensor_callback(self, switch, gparam):
        self._screen._ws.klippy.gcode_script(f"SET_FILAMENT_SENSOR SENSOR=fil_sensor ENABLE={1 if switch.get_active() else 0}")
        self._screen.show_all()
        if not self.loaded:
            self.loaded = True
            if switch.get_active():
                return
        self.update_deadtime = 3
        self.switch.set_sensitive(False)


class Purging(Cancelable, BaseWizardStep):
    def __init__(self, screen, first_purge=True):
        super().__init__(screen)
        self.first_purge = first_purge
        self.next_step = PurgingMoreDialog
        self.waiting_for_start = 5

    def activate(self, wizard):
        super().activate(wizard)
        logging.info(f"Currently loading {currently_loading}")
        if self.first_purge:
            self._screen._ws.klippy.gcode_script(f"SAVE_GCODE_STATE NAME=LOAD_FILAMENT")
            self._screen._ws.klippy.gcode_script(
                f"SAVE_VARIABLE VARIABLE=loaded_filament VALUE='\"{currently_loading}\"'")
            self._screen._ws.klippy.gcode_script(f"M83")
            self._screen._ws.klippy.gcode_script(f"G0 E35 F{int(600*speed_request)}")
            self._screen._ws.klippy.gcode_script(f"G0 E50 F{int(300*speed_request)}")
            self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=filamentretracted VALUE=0")
            self._screen._ws.klippy.gcode_script(f"_FILAMENT_RETRACT")
            self._screen._ws.klippy.gcode_script(f"RESTORE_GCODE_STATE NAME=LOAD_FILAMENT")
        else:
            self._screen._ws.klippy.gcode_script(f"SAVE_GCODE_STATE NAME=LOAD_FILAMENT")
            self._screen._ws.klippy.gcode_script(f"M83")
            self._screen._ws.klippy.gcode_script(f"_FILAMENT_DERETRACT")
            self._screen._ws.klippy.gcode_script(f"G0 E50 F{int(300*speed_request)}")
            self._screen._ws.klippy.gcode_script(f"_FILAMENT_RETRACT")
            self._screen._ws.klippy.gcode_script(f"RESTORE_GCODE_STATE NAME=LOAD_FILAMENT")

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("purging", self._screen.gtk.content_width * .945, 450)
        self.content.add(img)
        load_label = self._screen.gtk.Label("")
        load_label.set_margin_top(20)
        load_label.set_markup("<span size='large'>" + _("Filament is purging...") + "</span>")
        self.content.add(load_label)

    def update_loop(self):
        self.waiting_for_start -= 1
        it = self._screen.printer.data['idle_timeout']
        logging.info(f"waiting_for_start: {self.waiting_for_start}, it: {it['state']}")
        if it["state"] not in ["Ready", "Idle"]:
            self.waiting_for_start = 0
        if self.waiting_for_start <= 0 and it["state"] in ["Ready", "Idle"]:
            self.wizard_manager.set_step(self.next_step(self._screen))

class PurgingMoreDialog(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.heaters = []
        self.heaters.extend(iter(self._screen.printer.get_tools()))
        for h in self._screen.printer.get_heaters():
            if not h.endswith("panel"):
                self.heaters.append(h)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("purging", self._screen.gtk.content_width * .945,450)
        self.content.add(img)
        confirm_label = self._screen.gtk.Label("")
        confirm_label.set_margin_top(20)
        confirm_label.set_markup(
            "<span size='large'>" + _("Is color clean?") + "</span>")
        self.content.add(confirm_label)
        purge_button = self._screen.gtk.Button(label=_("Purge More"), style=f"color1")
        purge_button.set_vexpand(False)
        purge_button.connect("clicked", self.purge_filament_pressed)
        self.content.add(purge_button)
        cooldown_button = self._screen.gtk.Button(label=_("Cooldown and Close"), style=f"color1")
        cooldown_button.set_vexpand(False)
        cooldown_button.connect("clicked", self.cooldown_pressed)
        self.content.add(cooldown_button)
        back_button = self._screen.gtk.Button(label=_("Close"), style=f"color1")
        back_button.set_vexpand(False)
        back_button.connect("clicked", self._screen._menu_go_back)
        self.content.add(back_button)

    def cooldown_pressed(self, widget):
        for heater in self.heaters:
            logging.info(f"Cooling Down heater {heater}")
            name = heater.split()[1] if len(heater.split()) > 1 else heater
            target = 0
            if heater.startswith('extruder'):
                self._screen._ws.klippy.set_tool_temp(self._screen.printer.get_tool_number(heater), target)
            elif heater.startswith('heater_bed'):
                self._screen._ws.klippy.set_bed_temp(target)
            elif heater.startswith('heater_chamber'):
                self._screen._ws.klippy.set_chamber_temp(target)
            elif heater.startswith('heater_generic '):
                self._screen._ws.klippy.set_heater_temp(name, target)
            elif heater.startswith('temperature_fan '):
                self._screen._ws.klippy.set_temp_fan_temp(name, target)
        self._screen._menu_go_back()

    def purge_filament_pressed(self, widget):
        self.wizard_manager.set_step(CheckReheatNeeded(self._screen))


class CheckReheatNeeded(SelectFilament):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super(SelectFilament,self).activate(wizard)
        if ("extruder" in self.preheat_options[currently_loading] and
                self.preheat_options[currently_loading]["extruder"] > self._screen.printer.data['extruder']["target"]):
            self.next_step = WaitForTemperatureForPurge
            self.set_temperature(None, currently_loading)
        else:
            self.wizard_manager.set_step(Purging(self._screen, False))


class WaitForTemperatureForPurge(WaitForTemperature):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = DoPurgeAfterReheat


class DoPurgeAfterReheat(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.wizard_manager.set_step(Purging(self._screen, False))

