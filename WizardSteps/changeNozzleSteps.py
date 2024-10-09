import logging
import contextlib

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from WizardSteps.baseWizardStep import BaseWizardStep
from WizardSteps import loadWizardSteps, unloadWizardSteps, servicePositionSteps, wizardCommons

class CooldownPrompt(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)

        extruder = self._screen.printer.data['extruder']
        if extruder["temperature"] < 60 and extruder["target"] == 0:
            self.wizard_manager.set_step(ServicePositionDialog(self._screen))
            return
        if extruder["target"] == 0:
            self.wizard_manager.set_step(Cooling(self._screen))
            return

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("warning", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Nozzle is Hot!") + "</span>")
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
            "<span size='small'>" + _("Nozzle has to be cooled down before the nozzle change procedure.") + "</span>")
        self.content.add(second_label)
        self.continue_button = self._screen.gtk.Button(label=_("Cooldown and Continue"), style=f"color1")
        self.continue_button.set_vexpand(False)
        self.continue_button.connect("clicked", self._cooldown)
        self.content.add(self.continue_button)
        self.cancel_back = self._screen.gtk.Button(label=_("Go Back"), style=f"color1")
        self.cancel_back.set_vexpand(False)
        self.cancel_back.connect("clicked", self._go_back)
        self.content.add(self.cancel_back)

    def update_loop(self):
        extruder = self._screen.printer.data['extruder']
        if extruder["target"] == 0:
            self.wizard_manager.set_step(Cooling(self._screen))

    def _cooldown(self, widget):
        self._screen._ws.klippy.gcode_script(f"SET_HEATER_TEMPERATURE HEATER=extruder TARGET=0")
        self.wizard_manager.set_step(Cooling(self._screen))

    def _go_back(self, widget):
        self._screen._menu_go_back()

class Cooling(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("cooling", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Wait for nozzle cooldown") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)
        extruder = self._screen.printer.data['extruder']
        self.actual_temperature = self._screen.gtk.Label(f"Temperature: {int(extruder['temperature'])} °C")
        self.actual_temperature.set_hexpand(True)
        self.content.add(self.actual_temperature)
        cancel_button = self._screen.gtk.Button(label=_("Skip"), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.skip_pressed)
        self.content.add(cancel_button)
        cancel_button = self._screen.gtk.Button(label=_("Cancel"), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.cancel_pressed)
        self.content.add(cancel_button)

    def update_loop(self):
        extruder = self._screen.printer.data['extruder']
        self.actual_temperature.set_label(f"{int(extruder['temperature'])} °C")

        if extruder['temperature'] < 60:
            self.wizard_manager.set_step(ServicePositionDialog(self._screen))

    def cancel_pressed(self, widget):
        self._screen._menu_go_back()

    def skip_pressed(self, widget):
        self.wizard_manager.set_step(ConfirmSkipCooling(self._screen))

class ConfirmSkipCooling(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("warning", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Nozzle is still dangerously hot. Continue at your own risk!") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)
        extruder = self._screen.printer.data['extruder']
        self.actual_temperature = self._screen.gtk.Label(f"Temperature: {int(extruder['temperature'])} °C")
        self.actual_temperature.set_hexpand(True)
        self.content.add(self.actual_temperature)
        cancel_button = self._screen.gtk.Button(label=_("Wait for cooldown"), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.cancel_pressed)
        self.content.add(cancel_button)
        cancel_button = self._screen.gtk.Button(label=_("Continue at own risk"), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.continue_pressed)
        self.content.add(cancel_button)

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(ServicePositionDialog(self._screen))

    def cancel_pressed(self, widget):
        self.wizard_manager.set_step(Cooling(self._screen))

class ServicePositionDialog(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("is_bed_clear", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Check Print volume is empty") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)
        comment = self._screen.gtk.Label("")
        comment.set_margin_top(5)
        comment.set_margin_left(10)
        comment.set_margin_right(10)
        comment.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        comment.set_line_wrap(True)
        comment.set_markup("<span size='small'>" + _("Printhead will move to service position for comfortable access.") + "</span>")
        self.content.add(comment)
        continue_button = self._screen.gtk.Button(label=_("Print volume empty, continue"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.confirm_pressed)
        self.content.add(continue_button)
        cancel_button = self._screen.gtk.Button(label=_("I will change nozzle at current position"), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.discard_pressed)
        self.content.add(cancel_button)

    def confirm_pressed(self, widget):
        self.wizard_manager.set_step(MoveToServicePosition(self._screen))

    def discard_pressed(self, widget):
        self.wizard_manager.set_step(UnscrewNozzle(self._screen))


class MoveToServicePosition(servicePositionSteps.MoveToServicePosition):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = UnscrewNozzle


class UnscrewNozzle(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("unscrew", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Unscrew Nozzle") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)
        extruder = self._screen.printer.data['extruder']
        self.actual_temperature = self._screen.gtk.Label(f"Temperature: {int(extruder['temperature'])} °C")
        self.actual_temperature.set_hexpand(True)
        self.content.add(self.actual_temperature)
        continue_button = self._screen.gtk.Button(label=_("Nozzle unscrewed, continue"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)
        cancel_button = self._screen.gtk.Button(label=_("Cancel"), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.cancel_pressed)
        self.content.add(cancel_button)

    def update_loop(self):
        extruder = self._screen.printer.data['extruder']
        self.actual_temperature.set_label(f"{int(extruder['temperature'])} °C")

    def cancel_pressed(self, widget):
        self._screen._menu_go_back()

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(SelectNozzleType(self._screen))

class SelectNozzleType(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        current_printhead = self._screen.printer.data["config_constant printhead"]["value"] \
            if "config_constant printhead" in self._screen.printer.data else ""
        all_nozzle_types = self._screen._config.get_nozzle_types()
        self.nozzle_types = {}
        logging.info(f"current printhead: {current_printhead}")
        for nt in all_nozzle_types:
            logging.info(f"Checking nozzle type {nt} - {all_nozzle_types[nt]}")
            if current_printhead in all_nozzle_types[nt]["printheads"]:
                self.nozzle_types[nt] = all_nozzle_types[nt]
        self.next_step = SelectNozzleDiameter
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("revos", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Select Nozzle Type") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)

        preheat_grid = self._screen.gtk.HomogeneousGrid()
        i = 0
        for option in self.nozzle_types:
            option_pretty = option
            if option == "HF":
                option_pretty = "HF - HighFlow"
            elif option == "HT":
                option_pretty = "HT - HighTemp"
            elif option == "Standard":
                option_pretty = "Standard (Brass)"
            option_btn = self._screen.gtk.Button(label=option_pretty, style=f"color{(i % 4) + 1}")
            option_btn.connect("clicked", self.option_selected, option)
            option_btn.set_vexpand(False)
            preheat_grid.attach(option_btn, (i % 2), int(i / 2), 1, 1)
            i += 1
        scroll = self._screen.gtk.ScrolledWindow()
        scroll.add(preheat_grid)
        self.content.add(scroll)


    def option_selected(self, widget, option):
        print(option)
        print(self.nozzle_types[option])
        self.wizard_manager.set_step(self.next_step(self._screen,option))


class SelectNozzleDiameter(BaseWizardStep):
    def __init__(self, screen, nozzle_type):
        super().__init__(screen)
        self.nozzle_type = nozzle_type
        self.nozzle_types = self._screen._config.get_nozzle_types()
        self.nozzle_diameters = self.nozzle_types[nozzle_type]['diameters']
        self.can_back = True
        self.can_exit = False
        self.next_step = ScrewNozzleIn

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("revos", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Select Nozzle Diameter") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)

        preheat_grid = self._screen.gtk.HomogeneousGrid()
        i = 0
        for option in self.nozzle_diameters:
            option_btn = self._screen.gtk.Button(label=option, style=f"color{(i % 4) + 1}")
            option_btn.connect("clicked", self.option_selected, option)
            option_btn.set_vexpand(False)
            preheat_grid.attach(option_btn, (i % 2), int(i / 2), 1, 1)
            i += 1
        scroll = self._screen.gtk.ScrolledWindow()
        scroll.add(preheat_grid)
        self.content.add(scroll)

    def option_selected(self, widget, option):
        print(f"{option} {self.nozzle_type}")
        self.wizard_manager.set_step(self.next_step(self._screen, self.nozzle_type, option))

    def on_back(self):
        self.wizard_manager.set_step(SelectNozzleType(self._screen))
        return True


class ScrewNozzleIn(BaseWizardStep):
    def __init__(self, screen, nozzle_type, nozzle_diameter):
        super().__init__(screen)
        self.nozzle_type = nozzle_type
        self.nozzle_diameter = nozzle_diameter
        self.can_back = True
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("screw-in", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Screw the nozzle in") + "</span>")
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
            "<span size='small'>" + _("Nozzle") + f" {self.nozzle_diameter} {self.nozzle_type}" + "</span>")
        self.content.add(second_label)

        continue_button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)

    def continue_pressed(self, widget):
        self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=nozzle VALUE='\"{self.nozzle_diameter} {self.nozzle_type}\"'")
        self.wizard_manager.set_step(PurgeDialog(self._screen))

    def on_back(self):
        self.wizard_manager.set_step(SelectNozzleDiameter(self._screen,self.nozzle_type))
        return True

class PurgeDialog(BaseWizardStep, wizardCommons.TemperatureSetter):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_back = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("purged", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Nozzle purge is required") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)

        save_variables = self._screen.printer.data['save_variables']['variables']
        loaded_filament = save_variables['loaded_filament'] if 'loaded_filament' in save_variables else "NONE"
        printhead = self._screen.printer.data['config_constant printhead']['value'] \
            if 'config_constant printhead_pretty' in self._screen.printer.data else ""

        if (loaded_filament == "NONE" or loaded_filament not in loaded_filament or
                not printhead in self._screen._config.get_preheat_options()[loaded_filament]["printheads"]):
            button = self._screen.gtk.Button(label=_("Load filament"), style=f"color1")
            button.set_vexpand(False)
            button.connect("clicked", self.load_pressed)
            self.content.add(button)
        else:
            self.wizard_manager.set_wizard_data('currently_loading', loaded_filament)
            button = self._screen.gtk.Button(label=_("Purge with") + f" {loaded_filament}" , style=f"color1")
            button.set_vexpand(False)
            button.connect("clicked", self.continue_pressed)
            self.content.add(button)
            button = self._screen.gtk.Button(label=_("Load another filament"), style=f"color1")
            button.set_vexpand(False)
            button.connect("clicked", self.load_another_pressed)
            self.content.add(button)

        # guess of filament inside the new nozzle. Not destructive for any material,
        # but may not be good enough for HT materials
        self.wizard_manager.set_wizard_data("temperature_override_option", "PC")

    def load_pressed(self, widget):
        self.wizard_manager.set_step(SelectFilamentLoad(self._screen))

    def continue_pressed(self, widget):
        self.set_temperature(self.wizard_manager.get_wizard_data("temperature_override_option"),
                             self._screen.printer.get_tools())
        self.wizard_manager.set_step(WaitForTemperatureLoad(self._screen))

    def load_another_pressed(self, widget):
        self.wizard_manager.set_step(SelectFilament(self._screen))


class SelectFilament(unloadWizardSteps.SelectFilament):
    def __init__(self, screen, load_var=True):
        super().__init__(screen)
        self.next_step = WaitForTemperature
        self.next_step_on_skip = Unloading
        self.label = _("Which material would you like to unload?")
        self.label2 = _("Is the loaded material ")
        self.load_var = load_var

        self.heaters = []
        self.heaters.extend(iter(self._screen.printer.get_tools()))
        self.preheat_options = self._screen._config.get_preheat_options()
        self.max_head_temp = float(self._screen.printer.data['configfile']["config"]["extruder"]["max_temp"]) - 10

class WaitForTemperature(unloadWizardSteps.WaitForTemperature):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = Unloading

class Unloading(unloadWizardSteps.Unloading):
    def __init__(self, screen):
        super().__init__(screen)
        self.waiting_for_start = 5
        self.next_step = DoneDialog

class DoneDialog(loadWizardSteps.PurgingMoreDialog):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("unload_guide32", self._screen.gtk.content_width * .945, 450)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Filament unloaded") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)
        second_label = self._screen.gtk.Label("")
        second_label.set_margin_left(40)
        second_label.set_margin_right(40)
        second_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        second_label.set_line_wrap(True)
        second_label.set_markup(
            "<span size='small'>" + _(
                "Pull the end of the filament out of the printer and secure it against tangling.") + "</span>")
        self.content.add(second_label)
        load_button = self._screen.gtk.Button(label=_("Load New Material"), style=f"color1")
        load_button.set_vexpand(False)
        load_button.connect("clicked", self.go_to_load)
        self.content.add(load_button)
        back_button = self._screen.gtk.Button(label=_("Filament cannot be pulled out, try again"), style=f"color1")
        back_button.set_vexpand(False)
        back_button.connect("clicked", self.retry)
        self.content.add(back_button)

    def go_to_load(self, widget):
        self.wizard_manager.set_heading(_("Load Filament"))
        self.wizard_manager.set_step(SelectFilamentLoad(self._screen))

    def retry(self, widget):
        self.wizard_manager.set_step(ServicePositionNeededDialog(self._screen))

class ServicePositionNeededDialog(unloadWizardSteps.ServicePositionNeededDialog):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step_discard = SelectFilament
        self.next_step_confirm = ConfirmNoPrintPressent

class ConfirmNoPrintPressent(servicePositionSteps.ConfirmNoPrintPressent):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = MoveToServicePosition2
        self.cancel_step = SelectFilament

    def cancel_pressed(self, widget):
        self.wizard_manager.set_step(ServicePositionNeededDialog(self._screen))


class MoveToServicePosition2(servicePositionSteps.MoveToServicePosition):
    def __init__(self, screen, first_purge=True):
        super().__init__(screen)
        self.next_step = SelectFilamentLoad


class SelectFilamentLoad(loadWizardSteps.SelectFilament):
    def __init__(self, screen, load_var = False):
        super().__init__(screen)
        if ('config_constant printhead' in self._screen.printer.data and
                self._screen.printer.data['config_constant printhead']['value'] == "revoht"):
            self.next_step = SetFlapDialog
        else:
            self.next_step = WaitForChamberCooldown

        self.heaters = []
        self.heaters.extend(iter(self._screen.printer.get_tools()))
        logging.info(f"SelectFilamentLoad(loadWizardSteps.SelectFilament).init called")

class SetFlapDialog(loadWizardSteps.SetFlapDialog):
    def __init__(self, screen):
        super().__init__(screen)

class WaitForChamberCooldown(loadWizardSteps.WaitForChamberCooldown):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = WaitForTemperatureLoad

class WaitForTemperatureLoad(loadWizardSteps.WaitForTemperature):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = WaitForFilamentInserted

class WaitForFilamentInserted(loadWizardSteps.WaitForFilamentInserted):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = Purging

class Purging(loadWizardSteps.Purging):
    def __init__(self, screen, first_purge=True):
        super().__init__(screen)
        self.first_purge = first_purge
        self.next_step = PurgingMoreDialog

class PurgingMoreDialog(loadWizardSteps.PurgingMoreDialog):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = CheckReheatNeeded
        self.next_step_failed = WaitForTemperatureLoad

class CheckReheatNeeded(loadWizardSteps.CheckReheatNeeded):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = Purging
