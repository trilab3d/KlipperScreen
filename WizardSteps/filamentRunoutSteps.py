import logging
import contextlib

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from WizardSteps.baseWizardStep import BaseWizardStep
from WizardSteps import loadWizardSteps


class RemoveFilamentDialog(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.filament_sensor = self._screen.printer.data['filament_switch_sensor fil_sensor'] \
            if 'filament_switch_sensor fil_sensor' in self._screen.printer.data else None
    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("unload_guide_disassembled", self._screen.gtk.content_width * .9,
                                     self._screen.gtk.content_height * .5)
        self.content.add(img)
        confirm_label = self._screen.gtk.Label("")
        confirm_label.set_margin_top(20)
        confirm_label.set_markup(
            "<span size='large'>" + _("Remove remaining filament.") + "</span>")
        confirm_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        confirm_label.set_line_wrap(True)
        self.content.add(confirm_label)
        second_label = self._screen.gtk.Label("")
        second_label.set_margin_top(20)
        second_label.set_margin_left(10)
        second_label.set_margin_right(10)
        second_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        second_label.set_line_wrap(True)
        second_label.set_markup(
            "<span size='small'>" + _("If you cannot reach the filament end, disconnect the magnetic bowden coupler. "
                                      "Do not forget to put it back before the next filament load.") + "</span>")
        self.content.add(second_label)
        self.continue_button = self._screen.gtk.Button(label=_("Filament unloaded, continue"), style=f"color1")
        self.continue_button.set_vexpand(False)
        self.continue_button.set_sensitive(False)
        self.continue_button.connect("clicked", self.go_to_load)
        self.content.add(self.continue_button)

    def update_loop(self):
        if self.filament_sensor and self.filament_sensor["enabled"] and self.filament_sensor["filament_detected"]:
            self.continue_button.set_sensitive(False)
        else:
            self.continue_button.set_sensitive(True)

    def go_to_load(self, widget):
        self.wizard_manager.set_step(SelectFilament(self._screen))


class SelectFilament(loadWizardSteps.SelectFilament):
    def __init__(self, screen, load_var = True):
        super().__init__(screen, load_var)
        self.next_step = WaitForTemperature
        self.label = _("Which material would you like to load?")
        self.label2 = _("Would you like to load ")


class WaitForTemperature(loadWizardSteps.WaitForTemperature):
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
        img = self._screen.gtk.Image("purging", self._screen.gtk.content_width * .9,
                                     self._screen.gtk.content_height * .5)
        self.content.add(img)
        confirm_label = self._screen.gtk.Label("")
        confirm_label.set_margin_top(20)
        confirm_label.set_markup(
            "<span size='large'>" + _("Is the color clean?") + "</span>")
        confirm_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        confirm_label.set_line_wrap(True)
        self.content.add(confirm_label)
        purge_button = self._screen.gtk.Button(label=_("No, purge more"), style=f"color1")
        purge_button.set_vexpand(False)
        purge_button.connect("clicked", self.purge_filament_pressed)
        self.content.add(purge_button)
        back_button = self._screen.gtk.Button(label=_("Yes, continue"), style=f"color1")
        back_button.set_vexpand(False)
        back_button.connect("clicked", self.continue_dialog)
        self.content.add(back_button)

    def purge_filament_pressed(self, widget):
        self.wizard_manager.set_step(Purging(self._screen, False))

    def continue_dialog(self, widget):
        self.wizard_manager.set_step(ContinuePrintDialog(self._screen))


class ContinuePrintDialog(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("clean_extrusion", self._screen.gtk.content_width * .9,
                                     self._screen.gtk.content_height * .5)
        self.content.add(img)
        confirm_label = self._screen.gtk.Label("")
        confirm_label.set_margin_top(20)
        confirm_label.set_markup(
            "<span size='large'>" + _("Clean extruded material and close the door.") + "</span>")
        confirm_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        confirm_label.set_line_wrap(True)
        self.content.add(confirm_label)
        second_label = self._screen.gtk.Label("")
        second_label.set_margin_top(5)
        second_label.set_markup(
            "<span size='small'>" + _("Then click Resume print") + "</span>")
        second_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        second_label.set_line_wrap(True)
        self.content.add(second_label)
        continue_button = self._screen.gtk.Button(label=_("Resume Print"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.restore)
        self.content.add(continue_button)

    def restore(self, wizard):
        self._screen._ws.klippy.print_resume()
        self._screen.show_panel('job_status', "job_status", _("Printing"), 2)

