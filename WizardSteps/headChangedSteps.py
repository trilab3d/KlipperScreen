import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from threading import Thread
import os
import logging
import requests

from panels.privacy import PRESET_FIELDS

from WizardSteps.baseWizardStep import BaseWizardStep
from WizardSteps import changeNozzleSteps

class HeadChangeDetected(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_exit = False

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("head-swap", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Printer needs to know a few information about the new PrintHead.") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)
        continue_button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)
        cancel_button = self._screen.gtk.Button(label=_("False trigger, PrintHead was not changed."), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.cancel_clicked)
        self.content.add(cancel_button)

    def continue_pressed(self, widget):
        self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=printhead_init VALUE=True")
        self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=last_filament VALUE='\"NONE\"'")
        self.wizard_manager.set_step(SelectNozzleType(self._screen))

    def cancel_clicked(self, widget):
        self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=printhead_init VALUE=True")
        self._screen._menu_go_back()


class SelectNozzleType(changeNozzleSteps.SelectNozzleType):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = SelectNozzleDiameter

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("revos", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Select nozzle type installed in the PrintHead") + "</span>")
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
            elif option == "Standart":
                option_pretty = "Standart (Brass)"
            option_btn = self._screen.gtk.Button(label=option_pretty, style=f"color{(i % 4) + 1}")
            option_btn.connect("clicked", self.option_selected, option)
            option_btn.set_vexpand(False)
            preheat_grid.attach(option_btn, (i % 2), int(i / 2), 1, 1)
            i += 1
        scroll = self._screen.gtk.ScrolledWindow()
        scroll.add(preheat_grid)
        self.content.add(scroll)


class SelectNozzleDiameter(changeNozzleSteps.SelectNozzleDiameter):
    def on_back(self):
        self.wizard_manager.set_step(SelectNozzleType(self._screen))
        return True