import logging
import contextlib

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from WizardSteps.baseWizardStep import BaseWizardStep
from WizardSteps import loadWizardSteps, servicePositionSteps


class SelectFilament(loadWizardSteps.SelectFilament):
    def __init__(self, screen, load_var=True):
        super().__init__(screen, load_var)
        self.next_step = WaitForTemperature
        self.label = _("Which material would you like to unload?")
        self.label2 = _("Is the loaded material ")

        self.heaters = []
        self.heaters.extend(iter(self._screen.printer.get_tools()))

    def activate(self, wizard):
        if ('save_variables' in self._screen.printer.data and
                "filamentretracted" in self._screen.printer.data['save_variables']['variables'] and
                self._screen.printer.data['save_variables']['variables']['filamentretracted'] == 1):
            wizard.set_step(Unloading(self._screen))
        super().activate(wizard)


class WaitForTemperature(loadWizardSteps.WaitForTemperature):
    def __init__(self, screen, setting):
        super().__init__(screen, setting)

    def go_to_next(self):
        self.wizard_manager.set_step(Unloading(self._screen))


class Unloading(loadWizardSteps.Cancelable, BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.waiting_for_start = 5
        self.next_step = DoneDialog

    def activate(self, wizard):
        super().activate(wizard)

        self._screen._ws.klippy.gcode_script(f"SAVE_GCODE_STATE NAME=LOAD_FILAMENT")
        self._screen._ws.klippy.gcode_script(f"M83")
        if not ('save_variables' in self._screen.printer.data and
                "filamentretracted" in self._screen.printer.data['save_variables'][
                    'variables'] and
                self._screen.printer.data['save_variables']['variables'][
                    'filamentretracted'] == 1):
            self._screen._ws.klippy.gcode_script(f"G0 E3.0 F300")
            self._screen._ws.klippy.gcode_script(f"_FILAMENT_RETRACT")
            self._screen._ws.klippy.gcode_script(f"G4 P4000")
        self._screen._ws.klippy.gcode_script(f"G1 E-30.0 F900 C")
        self._screen._ws.klippy.gcode_script(f"RESTORE_GCODE_STATE NAME=LOAD_FILAMENT")

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("purging", self._screen.gtk.content_width * .945, 450)
        self.content.add(img)
        unload_label = self._screen.gtk.Label("")
        unload_label.set_margin_top(20)
        unload_label.set_markup("<span size='large'>" + _("Filament is unloading...") + "</span>")
        self.content.add(unload_label)

    def update_loop(self):
        self.waiting_for_start -= 1
        it = self._screen.printer.data['idle_timeout']
        logging.info(f"waiting_for_start: {self.waiting_for_start}, it: {it['state']}")
        if it["state"] not in ["Ready", "Idle"]:
            self.waiting_for_start = 0
        if self.waiting_for_start <= 0 and it["state"] in ["Ready", "Idle"]:
            self.wizard_manager.set_step(self.next_step(self._screen))


class DoneDialog(loadWizardSteps.PurgingMoreDialog):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = WaitForTemperature

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("unload_guide32", self._screen.gtk.content_width * .945, 450)
        self.content.add(img)
        confirm_label = self._screen.gtk.Label("")
        confirm_label.set_margin_top(20)
        confirm_label.set_markup(
            "<span size='large'>" + _("Filament unloaded") + "</span>")
        self.content.add(confirm_label)
        second_label = self._screen.gtk.Label("")
        second_label.set_margin_left(40)
        second_label.set_margin_right(40)
        second_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        second_label.set_line_wrap(True)
        second_label.set_markup(
            "<span size='small'>" + _(
                "Pull the end of the filament out of the printer and secure it against tangling.") + "</span>")
        self.content.add(second_label)
        load_button = self._screen.gtk.Button(label=_("Load new material"), style=f"color1")
        load_button.set_vexpand(False)
        load_button.connect("clicked", self.go_to_load)
        self.content.add(load_button)
        cooldown_button = self._screen.gtk.Button(label=_("Cooldown and Close"), style=f"color1")
        cooldown_button.set_vexpand(False)
        cooldown_button.connect("clicked", self.cooldown_pressed)
        self.content.add(cooldown_button)
        back_button = self._screen.gtk.Button(label=_("Close"), style=f"color1")
        back_button.set_vexpand(False)
        back_button.connect("clicked", self._screen._menu_go_back, True)
        self.content.add(back_button)
        back_button = self._screen.gtk.Button(label=_("Filament can't be pulled out, try again"), style=f"color1")
        back_button.set_vexpand(False)
        back_button.connect("clicked", self.retry)
        self.content.add(back_button)

    def go_to_load(self, widget):
        self.wizard_manager.set_heading(_("Load Filament"))
        self.wizard_manager.set_step(loadWizardSteps.SelectFilament(self._screen))

    def retry(self, widget):
        self.wizard_manager.set_step(ServicePositionNeededDialog(self._screen))


class ServicePositionNeededDialog(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=filamentretracted VALUE=0")
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Move printhead to service position?") + "</span>")
        self.content.add(heating_label)
        continue_button = self._screen.gtk.Button(label=_("Yes"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.confirm_pressed)
        self.content.add(continue_button)
        cancel_button = self._screen.gtk.Button(label=_("No"), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.discard_pressed)
        self.content.add(cancel_button)

    def confirm_pressed(self, widget):
        self.wizard_manager.set_step(ConfirmNoPrintPressent(self._screen))

    def discard_pressed(self, widget):
        self.wizard_manager.set_step(SelectFilament(self._screen))


class ConfirmNoPrintPressent(servicePositionSteps.ConfirmNoPrintPressent):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = MoveToServicePosition

    def cancel_pressed(self, widget):
        self.wizard_manager.set_step(ServicePositionNeededDialog(self._screen))


class MoveToServicePosition(servicePositionSteps.MoveToServicePosition):
    def __init__(self, screen, first_purge=True):
        super().__init__(screen)
        self.next_step = SelectFilament

