import logging
import contextlib

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from WizardSteps.baseWizardStep import BaseWizardStep
from WizardSteps import loadWizardSteps, unloadWizardSteps


class ConfirmPause(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("pause-circle", self._screen.gtk.content_width * .9,
                                     self._screen.gtk.content_height * .5)
        self.content.add(img)
        confirm_label = self._screen.gtk.Label("")
        confirm_label.set_margin_top(20)
        confirm_label.set_markup(
            "<span size='large'>" + _("Pause print") + "</span>")
        self.content.add(confirm_label)
        second_label = self._screen.gtk.Label("")
        second_label.set_margin_top(20)
        second_label.set_margin_left(10)
        second_label.set_margin_right(10)
        second_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        second_label.set_line_wrap(True)
        second_label.set_markup(
            "<span size='small'>" + _("Print must be paused to change filament. Do you want to continue?") + "</span>")
        self.content.add(second_label)
        self.continue_button = self._screen.gtk.Button(label=_("Pause print and continue"), style=f"color1")
        self.continue_button.set_vexpand(False)
        self.continue_button.connect("clicked", self._do_pause)
        self.content.add(self.continue_button)
        self.cancel_back = self._screen.gtk.Button(label=_("Go back"), style=f"color1")
        self.cancel_back.set_vexpand(False)
        self.cancel_back.connect("clicked", self._go_back)
        self.content.add(self.cancel_back)

    def update_loop(self):
        if self._screen.printer.data['idle_timeout']['state'] != "Printing":
            self.wizard_manager.set_step(SelectFilament(self._screen))

    def _do_pause(self, widget):
        pass

    def _go_back(self, widget):
        pass


class SelectFilament(unloadWizardSteps.SelectFilament):
    def __init__(self, screen, load_var = True):
        super().__init__(screen, load_var)
        self.next_step = WaitForTemperature


class WaitForTemperature(unloadWizardSteps.WaitForTemperature):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = Unloading


class Unloading(unloadWizardSteps.Unloading):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = UnloadedDialog


class UnloadedDialog(BaseWizardStep):
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
        load_button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        load_button.set_vexpand(False)
        load_button.connect("clicked", self.go_to_load)
        self.content.add(load_button)

    def go_to_load(self, widget):
        self.wizard_manager.set_step(SelectFilamentLoad(self._screen))


class SelectFilamentLoad(loadWizardSteps.SelectFilament):
    def __init__(self, screen, load_var = True):
        super().__init__(screen, load_var)
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
            "<span size='large'>" + _("Is color clean?") + "</span>")
        self.content.add(confirm_label)
        purge_button = self._screen.gtk.Button(label=_("No, purge More"), style=f"color1")
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
        self.content.add(confirm_label)
        second_label = self._screen.gtk.Label("")
        second_label.set_margin_top(5)
        second_label.set_markup(
            "<span size='small'>" + _("Then click Resume print or Close.") + "</span>")
        self.content.add(second_label)
        resume_button = self._screen.gtk.Button(label=_("Resume Print"), style=f"color1")
        resume_button.set_vexpand(False)
        resume_button.connect("clicked", self._resume)
        self.content.add(resume_button)
        close_button = self._screen.gtk.Button(label=_("Close"), style=f"color1")
        close_button.set_vexpand(False)
        close_button.connect("clicked", self._close)
        self.content.add(close_button)

    def _resume(self, wizard):
        self._screen._ws.klippy.print_resume()
        self._screen.show_panel('job_status', "job_status", _("Printing"), 2)

    def _close(self, wizard):
        pass


