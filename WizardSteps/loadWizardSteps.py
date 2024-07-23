import logging
import contextlib

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from WizardSteps.baseWizardStep import BaseWizardStep
from WizardSteps.wizardCommons import *

class Cancelable(TemperatureSetter):
    def on_cancel(self):
        self._screen._ws.klippy.gcode_script("_FILAMENT_RETRACT")
        heaters = []
        heaters.extend(iter(self._screen.printer.get_tools()))
        for h in self._screen.printer.get_heaters():
            if not h.endswith("panel"):
                heaters.append(h)
        logging.info(heaters)
        self.set_temperature("cooldown",heaters)


class CheckLoaded(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        save_variables = self._screen.printer.data['save_variables']['variables']
        loaded_filament = save_variables['loaded_filament'] if 'loaded_filament' in save_variables else "NONE"
        logging.info(f"Loaded filament is {loaded_filament}")
        if loaded_filament == "NONE":
            logging.info(f"Loaded filament is NONE, skipping")
            self.wizard_manager.set_step(SelectFilament(self._screen))
            return

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("filament_already_inserted", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("It seems that another filament is already inserted") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)
        unload_button = self._screen.gtk.Button(label=_("Perform Unload first"), style=f"color1")
        unload_button.set_vexpand(False)
        unload_button.connect("clicked", self.unload_pressed)
        self.content.add(unload_button)
        continue_button = self._screen.gtk.Button(label=_("Continue anyway"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(SelectFilament(self._screen))

    def unload_pressed(self, widget):
        from WizardSteps import unloadWizardSteps
        self.wizard_manager.set_heading(_("Load Filament"))
        self.wizard_manager.set_step(unloadWizardSteps.SelectFilament(self._screen))

class SelectFilament(BaseWizardStep, TemperatureSetter):
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

        if ('config_constant printhead' in self._screen.printer.data and
                self._screen.printer.data['config_constant printhead']['value'] == "revoht"):
            self.next_step = SetFlapDialog
        else:
            self.next_step = WaitForChamberCooldown

        self.label = _("Which material would you like to load?")
        self.label2 = _("Would you like to load ")

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("prusament", self._screen.gtk.content_width * .945, 450)
        self.content.add(img)

        expected_filament = self.wizard_manager.get_wizard_data("expected_filament")
        if (expected_filament and expected_filament in self.preheat_options):
            label = self._screen.gtk.Label("")
            label.set_margin_top(20)
            label.set_markup(
                "<span size='large'>" + (
                        self.label2 + f"{expected_filament}?") + "</span>")
            label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            label.set_line_wrap(True)
            self.content.add(label)
            grid = self._screen.gtk.HomogeneousGrid()
            yes = self._screen.gtk.Button(label=_("Yes"), style=f"color1")
            yes.connect("clicked", self.set_filament_clicked, self.preheat_options)
            yes.set_vexpand(False)
            grid.attach(yes, 0, 0, 1, 1)
            no = self._screen.gtk.Button(label=_("No, select a different material"), style=f"color1")
            no.connect("clicked", self.set_filament_unknown)
            no.set_vexpand(False)
            grid.attach(no, 0, 1, 1, 1)
            self.content.add(grid)
        elif (self.load_var and 'save_variables' in self._screen.printer.data and
                "loaded_filament" in self._screen.printer.data['save_variables']['variables'] and
                self._screen.printer.data['save_variables']['variables']["loaded_filament"] in self.preheat_options):
            save_variables = self._screen.printer.data['save_variables']['variables']
            label = self._screen.gtk.Label("")
            label.set_margin_top(20)
            label.set_markup(
                "<span size='large'>" + (
                    self.label2 + f"{save_variables['loaded_filament']}?") + "</span>")
            label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            label.set_line_wrap(True)
            self.content.add(label)
            grid = self._screen.gtk.HomogeneousGrid()
            yes = self._screen.gtk.Button(label=_("Yes"), style=f"color1")
            yes.connect("clicked", self.set_filament_clicked, save_variables["loaded_filament"])
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
            label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            label.set_line_wrap(True)
            self.content.add(label)
            preheat_grid = self._screen.gtk.HomogeneousGrid()
            i = 0
            printhead = self._screen.printer.data['config_constant printhead']['value'] \
                if 'config_constant printhead_pretty' in self._screen.printer.data else ""
            for option in self.preheat_options:
                if ((option != "cooldown" and "extruder" in self.preheat_options[option]
                        and self.preheat_options[option]["extruder"] <= self.max_head_temp) and
                        ("printheads" not in self.preheat_options[option] or
                         printhead in self.preheat_options[option]["printheads"])):
                    option_btn = self._screen.gtk.Button(label=option, style=f"color{(i % 4) + 1}")
                    option_btn.connect("clicked", self.set_filament_clicked, option)
                    option_btn.set_vexpand(False)
                    preheat_grid.attach(option_btn, (i % 2), int(i / 2), 1, 1)
                    i += 1
            scroll = self._screen.gtk.ScrolledWindow()
            scroll.add(preheat_grid)
            self.content.add(scroll)

    def set_filament_clicked(self, widget, option):
        self.wizard_manager.set_wizard_data("currently_loading", option)
        max_load_temp = self.preheat_options[option]["extruder_max"] if "extruder_max" in self.preheat_options[option] else None
        speed = self.preheat_options[option]["speed"] if "speed" in self.preheat_options[option] else 1
        self.wizard_manager.set_wizard_data("speed_request", speed)
        save_variables = self._screen.printer.data['save_variables']['variables']
        self.set_temperature(option, self.heaters)

        if self.wizard_manager.get_wizard_data("temperature_override_option"):
            self.set_temperature(self.wizard_manager.get_wizard_data("temperature_override_option"), self._screen.printer.get_tools())
        elif ("last_filament" in save_variables and save_variables["last_filament"] in self.preheat_options and
                self.preheat_options[save_variables["last_filament"]]["extruder"] > self.preheat_options[option]["extruder"]):
            self.set_temperature(save_variables["last_filament"],self._screen.printer.get_tools())
            self.wizard_manager.set_wizard_data("temperature_override_option", save_variables["last_filament"])
            if self.preheat_options[save_variables["last_filament"]]["extruder"] >= max_load_temp:
                max_load_temp = self.preheat_options[save_variables["last_filament"]]["extruder"] + 10

        self.wizard_manager.set_wizard_data("max_load_temperature", max_load_temp)
        self.wizard_manager.set_step(self.next_step(self._screen))

    def set_filament_unknown(self, widget):
        self.wizard_manager.set_wizard_data("expected_filament", None)
        self.wizard_manager.set_step(self.__class__(self._screen, False))


class SetFlapDialog(Cancelable, BaseWizardStep):
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
        setting = self._screen._config.get_preheat_options()[self.wizard_manager.get_wizard_data('currently_loading')]
        flap_position = setting["flap_position"]
        img = self._screen.gtk.Image(f"htflap{int(flap_position)}", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Set flap to position ") + f"{int(flap_position)}</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)
        continue_button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)

    def continue_pressed(self, wizard):
        self.wizard_manager.set_step(WaitForTemperature(self._screen))

class WaitForChamberCooldown(Cancelable, BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = WaitForTemperature
        self.settling_counter = self.settling_counter_max = 3


    def activate(self, wizard):
        super().activate(wizard)

        if not hasattr(self, 'setting'):
            self.setting = self._screen._config.get_preheat_options()[
                self.wizard_manager.get_wizard_data('currently_loading')]

        if "chamber_max" not in self.setting or self.fetch_chamber()['temperature'] < self.setting["chamber_max"]:
            self.go_to_next()
            return

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("cooling", self._screen.gtk.content_width * .945,450)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Chamber too hot") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)
        self.chamber_progressbar = Gtk.ProgressBar()
        self.chamber_progressbar.set_show_text(False)
        self.chamber_progressbar.set_hexpand(True)
        self.content.add(self.chamber_progressbar)
        self.actual_chamber = self._screen.gtk.Label("0 °C")
        self.actual_chamber.set_hexpand(True)
        self.actual_chamber.set_halign(Gtk.Align.START)
        self.target_chamber = self._screen.gtk.Label("0 °C")
        self.target_chamber.set_halign(Gtk.Align.END)
        temperature_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, margin_start=20, margin_end=20)
        temperature_box.set_hexpand(True)
        temperature_box.add(self.actual_chamber)
        temperature_box.add(self.target_chamber)
        self.content.add(temperature_box)
        cancel_button = self._screen.gtk.Button(label=_("Cancel"), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.cancel_pressed)
        self.content.add(cancel_button)

    def update_loop(self):
        chamber = self.fetch_chamber()

        err = chamber["temperature"] - self.setting["chamber_max"]
        fract = 1 - (err / (90-self.setting["chamber_max"]))
        self.chamber_progressbar.set_fraction(fract)
        self.actual_chamber.set_label(f"{chamber['temperature']:.1f} °C")
        self.target_chamber.set_label(f"{self.setting['chamber_max']:.1f} °C")

        if chamber['temperature'] < self.setting["chamber_max"]:
            self.settling_counter -= 1
            if self.settling_counter < 1:
                self.go_to_next()
        else:
            self.settling_counter = self.settling_counter_max

    def go_to_next(self):
        self.wizard_manager.set_step(self.next_step(self._screen))

    def fetch_chamber(self):
        if "heater_chamber" in self._screen.printer.data:
            chamber = self._screen.printer.data['heater_chamber']
        else:
            chamber = {
                "temperature": 0,
                "target": 0
            }
        return chamber

    def cancel_pressed(self, widget):
        self._screen._menu_go_back()

class WaitForTemperature(Cancelable, BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = WaitForFilamentInserted
        self.settling_counter = self.settling_counter_max = 3

    def activate(self, wizard):
        super().activate(wizard)
        self.max_load_temperature = wizard.get_wizard_data("max_load_temperature")
        if not hasattr(self, 'setting'):
            self.setting = self._screen._config.get_preheat_options()[
                self.wizard_manager.get_wizard_data('currently_loading')]
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("heating", self._screen.gtk.content_width * .945,450)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Wait for temperature...") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)
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

        if (abs(extruder['temperature'] - extruder['target']) < 3 or
                (self.max_load_temperature is not None and self.max_load_temperature > extruder['temperature'] >
                 extruder['target'])):
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
        self.fs_label.set_markup(f"<big><b>{_('Filament Sensor')}</b></big>")
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


class Purging(Cancelable, BaseWizardStep, TemperatureSetter):
    def __init__(self, screen, first_purge=True):
        super().__init__(screen)
        self.first_purge = first_purge
        self.next_step = PurgingMoreDialog
        self.waiting_for_start = 5
        self.preheat_options = self._screen._config.get_preheat_options()

    def activate(self, wizard):
        super().activate(wizard)
        speed_request = self.wizard_manager.get_wizard_data('speed_request')
        if not speed_request:
            speed_request = 1
        logging.info(f"Currently loading {self.wizard_manager.get_wizard_data('currently_loading')}, speed_request: {speed_request}")
        if self.first_purge:
            self.set_temperature(self.wizard_manager.get_wizard_data('currently_loading'),
                                 self._screen.printer.get_tools())
            self._screen._ws.klippy.gcode_script(f"SAVE_GCODE_STATE NAME=LOAD_FILAMENT")
            self._screen._ws.klippy.gcode_script(
                f"SAVE_VARIABLE VARIABLE=loaded_filament VALUE='\"{self.wizard_manager.get_wizard_data('currently_loading')}\"'")
            self._screen._ws.klippy.gcode_script(
                f"SAVE_VARIABLE VARIABLE=last_filament VALUE='\"{self.wizard_manager.get_wizard_data('currently_loading')}\"'")
            self._screen._ws.klippy.gcode_script(f"M83")
            self._screen._ws.klippy.gcode_script(f"G0 E35 F{int(600*speed_request)}")
            self._screen._ws.klippy.gcode_script(f"G0 E50 F{int(300*speed_request)}")
            self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=filamentretracted VALUE=0")
            self._screen._ws.klippy.gcode_script(f"_FILAMENT_RETRACT SPEED={int(40*speed_request)}")
            self._screen._ws.klippy.gcode_script(f"RESTORE_GCODE_STATE NAME=LOAD_FILAMENT")
            self._screen._ws.klippy.gcode_script(f"SET_STEPPER_ENABLE STEPPER=extruder ENABLE=0")
        else:
            self._screen._ws.klippy.gcode_script(f"SAVE_GCODE_STATE NAME=LOAD_FILAMENT")
            self._screen._ws.klippy.gcode_script(f"M83")
            self._screen._ws.klippy.gcode_script(f"_FILAMENT_DERETRACT SPEED={int(40*speed_request)}")
            self._screen._ws.klippy.gcode_script(f"G0 E50 F{int(300*speed_request)}")
            self._screen._ws.klippy.gcode_script(f"_FILAMENT_RETRACT SPEED={int(40*speed_request)}")
            self._screen._ws.klippy.gcode_script(f"RESTORE_GCODE_STATE NAME=LOAD_FILAMENT")
            self._screen._ws.klippy.gcode_script(f"SET_STEPPER_ENABLE STEPPER=extruder ENABLE=0")

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("purging", self._screen.gtk.content_width * .945, 450)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup("<span size='large'>" + _("Filament is purging...") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)

    def update_loop(self):
        self.waiting_for_start -= 1
        it = self._screen.printer.data['idle_timeout']
        logging.info(f"waiting_for_start: {self.waiting_for_start}, it: {it['state']}")
        if it["state"] not in ["Ready", "Idle"]:
            self.waiting_for_start = 0
        if self.waiting_for_start <= 0 and it["state"] in ["Ready", "Idle"]:
            self.wizard_manager.set_step(self.next_step(self._screen))

class PurgingMoreDialog(BaseWizardStep, TemperatureSetter):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = CheckReheatNeeded
        self.next_step_failed = WaitForTemperature
        self.heaters = []
        self.heaters.extend(iter(self._screen.printer.get_tools()))
        self.preheat_options = self._screen._config.get_preheat_options()
        for h in self._screen.printer.get_heaters():
            if not h.endswith("panel"):
                self.heaters.append(h)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("purging", self._screen.gtk.content_width * .945,450)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Is the color clean?") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)
        purge_button = self._screen.gtk.Button(label=_("Purge More"), style=f"color1")
        purge_button.set_vexpand(False)
        purge_button.connect("clicked", self.purge_filament_pressed)
        self.content.add(purge_button)
        cooldown_button = self._screen.gtk.Button(label=_("Close"), style=f"color1")
        cooldown_button.set_vexpand(False)
        cooldown_button.connect("clicked", self.cooldown_pressed)
        self.content.add(cooldown_button)
        if self.wizard_manager.get_wizard_data("temperature_override_option"):
            failed_button = self._screen.gtk.Button(label=_("Load Failed, Re-Heat"), style=f"color1")
            failed_button.set_vexpand(False)
            failed_button.connect("clicked", self.failed_pressed)
            self.content.add(failed_button)

    def cooldown_pressed(self, widget):
        self.set_temperature("cooldown",self.heaters)
        self._screen._menu_go_back()

    def purge_filament_pressed(self, widget):
        self.wizard_manager.set_step(self.next_step(self._screen))

    def failed_pressed(self, widget):
        self.set_temperature(self.wizard_manager.get_wizard_data("temperature_override_option"),self._screen.printer.get_tools())
        self.wizard_manager.set_step(self.next_step_failed(self._screen))

    def on_cancel(self):
        self.set_temperature("cooldown",self.heaters)



class CheckReheatNeeded(SelectFilament):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = Purging

    def activate(self, wizard):
        super(SelectFilament,self).activate(wizard)
        currently_loading = self.wizard_manager.get_wizard_data('currently_loading')
        if ("extruder" in self.preheat_options[currently_loading] and
                self.preheat_options[currently_loading]["extruder"] > self._screen.printer.data['extruder']["target"]):
            self.next_step = WaitForTemperatureForPurge
            self.set_temperature(currently_loading, self.heaters)
        else:
            self.wizard_manager.set_step(self.next_step(self._screen, False))


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

