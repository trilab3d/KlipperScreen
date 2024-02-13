import logging
import contextlib

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from WizardSteps.baseWizardStep import BaseWizardStep
from WizardSteps import loadWizardSteps

class SelectFilament(loadWizardSteps.SelectFilament):
    def __init__(self, screen, load_var = True):
        super().__init__(screen, load_var)
        self.next_step = WaitForTemperature
        self.label = _("Which material would you like to unload?")
        self.label2 = _("Is the loaded material ")

        self.heaters = []
        self.heaters.extend(iter(self._screen.printer.get_tools()))

    def set_temperature(self, widget, setting):
        if ('save_variables' in self._screen.printer.data and
                "filamentretracted" in self._screen.printer.data['save_variables']['variables'] and
                self._screen.printer.data['save_variables']['variables']['filamentretracted'] == 1):
            self.wizard_manager.set_step(Unloading(self._screen))
            return
        super().set_temperature(widget,setting)

class WaitForTemperature(loadWizardSteps.WaitForTemperature):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = Unloading

class Unloading(loadWizardSteps.Cancelable, BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.waiting_for_start = 5
        self.next_step = DoneDialog
    def activate(self, wizard):
        super().activate(wizard)

        self._screen._ws.klippy.gcode_script(f"SAVE_GCODE_STATE NAME=LOAD_FILAMENT")
        self._screen._ws.klippy.gcode_script(f"M83")
        if not('save_variables' in self._screen.printer.data and
                "filamentretracted" in self._screen.printer.data['save_variables']['variables'] and
                self._screen.printer.data['save_variables']['variables']['filamentretracted'] == 1):
            self._screen._ws.klippy.gcode_script(f"G0 E3.0 F300")
            self._screen._ws.klippy.gcode_script(f"_FILAMENT_RETRACT")
            self._screen._ws.klippy.gcode_script(f"G4 P4000")
        self._screen._ws.klippy.gcode_script(f"G1 E-30.0 F900 C")
        self._screen._ws.klippy.gcode_script(f"RESTORE_GCODE_STATE NAME=LOAD_FILAMENT")

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("prusament", self._screen.gtk.content_width * .9,
                                     self._screen.gtk.content_height * .5)
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
    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("unload_guide", self._screen.gtk.content_width * .9,
                                     self._screen.gtk.content_height * .5)
        self.content.add(img)
        confirm_label = self._screen.gtk.Label("")
        confirm_label.set_margin_top(20)
        confirm_label.set_markup(
            "<span size='large'>" + _("Filament unloaded successfully") + "</span>")
        self.content.add(confirm_label)
        second_label = self._screen.gtk.Label("")
        second_label.set_margin_left(40)
        second_label.set_margin_right(40)
        second_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        second_label.set_line_wrap(True)
        second_label.set_markup(
            "<span size='small'>" + _("Pull the end of the filament out of the printer and secure it against tangling.") + "</span>")
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

    def go_to_load(self, widget):
        self.wizard_manager.set_step(loadWizardSteps.SelectFilament(self._screen))


