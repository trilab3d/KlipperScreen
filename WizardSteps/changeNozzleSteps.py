import logging
import contextlib

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from WizardSteps.baseWizardStep import BaseWizardStep
from WizardSteps import loadWizardSteps, unloadWizardSteps

class CooldownPrompt(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)

        extruder = self._screen.printer.data['extruder']
        if extruder["temperature"] < 60 and extruder["target"] == 0:
            self.wizard_manager.set_step(UnscrewNozzle(self._screen))
            return
        if extruder["target"] == 0:
            self.wizard_manager.set_step(Cooling(self._screen))
            return

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("warning", self._screen.gtk.content_width * .9,
                                     self._screen.gtk.content_height * .5)
        self.content.add(img)
        confirm_label = self._screen.gtk.Label("")
        confirm_label.set_margin_top(20)
        confirm_label.set_markup(
            "<span size='large'>" + _("Nozzle is Hot!") + "</span>")
        self.content.add(confirm_label)
        second_label = self._screen.gtk.Label("")
        second_label.set_margin_top(20)
        second_label.set_margin_left(10)
        second_label.set_margin_right(10)
        second_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        second_label.set_line_wrap(True)
        second_label.set_markup(
            "<span size='small'>" + _("Nozzle has to be cooled down before changing procedure.") + "</span>")
        self.content.add(second_label)
        self.continue_button = self._screen.gtk.Button(label=_("Cooldown and continue"), style=f"color1")
        self.continue_button.set_vexpand(False)
        self.continue_button.connect("clicked", self._cooldown)
        self.content.add(self.continue_button)
        self.cancel_back = self._screen.gtk.Button(label=_("Go back"), style=f"color1")
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
        pass

class Cooling(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder", self._screen.gtk.content_width * .9,
                                     self._screen.gtk.content_height * .5)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Wait for nozzle cooldown") + "</span>")
        self.content.add(heating_label)
        extruder = self._screen.printer.data['extruder']
        self.actual_temperature = self._screen.gtk.Label(f"Temperature: {extruder['temperature']:.1f} °C")
        self.actual_temperature.set_hexpand(True)
        self.content.add(self.actual_temperature)
        cancel_button = self._screen.gtk.Button(label=_("Cancel"), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.cancel_pressed)
        self.content.add(cancel_button)

    def update_loop(self):
        extruder = self._screen.printer.data['extruder']
        self.actual_temperature.set_label(f"{extruder['temperature']:.1f} °C")

        if extruder['temperature'] < 60:
            self.wizard_manager.set_step(UnscrewNozzle(self._screen))

    def cancel_pressed(self, widget):
        self._screen._menu_go_back()

class UnscrewNozzle(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder", self._screen.gtk.content_width * .9,
                                     self._screen.gtk.content_height * .5)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Unscrew Nozzle") + "</span>")
        self.content.add(heating_label)
        extruder = self._screen.printer.data['extruder']
        self.actual_temperature = self._screen.gtk.Label(f"Temperature: {extruder['temperature']:.1f} °C")
        self.actual_temperature.set_hexpand(True)
        self.content.add(self.actual_temperature)
        continue_button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)
        cancel_button = self._screen.gtk.Button(label=_("Cancel"), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.cancel_pressed)
        self.content.add(cancel_button)

    def update_loop(self):
        extruder = self._screen.printer.data['extruder']
        self.actual_temperature.set_label(f"{extruder['temperature']:.1f} °C")

    def cancel_pressed(self, widget):
        self._screen._menu_go_back()

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(SelectNozzleType(self._screen))

class SelectNozzleType(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.nozzle_types = self._screen._config.get_nozzle_types()

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder", self._screen.gtk.content_width * .9,
                                     self._screen.gtk.content_height * .5)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Select Nozzle Type") + "</span>")
        self.content.add(heating_label)

        preheat_grid = self._screen.gtk.HomogeneousGrid()
        i = 0
        for option in self.nozzle_types:
            option_btn = self._screen.gtk.Button(label=option, style=f"color{(i % 4) + 1}")
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
        self.wizard_manager.set_step(SelectNozzleDiameter(self._screen,option))


class SelectNozzleDiameter(BaseWizardStep):
    def __init__(self, screen, nozzle_type):
        super().__init__(screen)
        self.nozzle_type = nozzle_type
        self.nozzle_types = self._screen._config.get_nozzle_types()
        self.nozzle_diameters = self.nozzle_types[nozzle_type]['diameters']

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder", self._screen.gtk.content_width * .9,
                                     self._screen.gtk.content_height * .5)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Select Nozzle Diameter") + "</span>")
        self.content.add(heating_label)

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

        back_button = self._screen.gtk.Button(label=_("Select Different Type") + f" ({self.nozzle_type})", style=f"color1")
        back_button.set_vexpand(False)
        back_button.connect("clicked", self.back_pressed)
        self.content.add(back_button)

    def option_selected(self, widget, option):
        print(f"{option} {self.nozzle_type}")
        self.wizard_manager.set_step(ScrewNozzleIn(self._screen, self.nozzle_type, option))

    def back_pressed(self, widget):
        self.wizard_manager.set_step(SelectNozzleType(self._screen))


class ScrewNozzleIn(BaseWizardStep):
    def __init__(self, screen, nozzle_type, nozzle_diameter):
        super().__init__(screen)
        self.nozzle_type = nozzle_type
        self.nozzle_diameter = nozzle_diameter

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder", self._screen.gtk.content_width * .9,
                                     self._screen.gtk.content_height * .5)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Screw The Nozzle In") + "</span>")
        self.content.add(heating_label)
        second_label = self._screen.gtk.Label("")
        second_label.set_margin_top(20)
        second_label.set_margin_left(10)
        second_label.set_margin_right(10)
        second_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        second_label.set_line_wrap(True)
        second_label.set_markup(
            "<span size='small'>" + _("Nozzle") + f" {self.nozzle_diameter} {self.nozzle_type}" + "</span>")
        self.content.add(second_label)

        continue_button = self._screen.gtk.Button(label=_("Save and Close"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)
        back_button = self._screen.gtk.Button(label=_("Select Different Nozzle"), style=f"color1")
        back_button.set_vexpand(False)
        back_button.connect("clicked", self.back_pressed)
        self.content.add(back_button)

    def continue_pressed(self, widget):
        self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=nozzle VALUE='\"{self.nozzle_diameter} {self.nozzle_type}\"'")
        self._screen._menu_go_back()

    def back_pressed(self, widget):
        self.wizard_manager.set_step(SelectNozzleDiameter(self._screen,self.nozzle_type))


