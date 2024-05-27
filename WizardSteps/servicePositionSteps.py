import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from WizardSteps.baseWizardStep import BaseWizardStep

class ConfirmNoPrintPressent(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = MoveToServicePosition

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Make sure the print volume is empty.") + "</span>")
        self.content.add(heating_label)
        continue_button = self._screen.gtk.Button(label=_("Continue"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)
        cancel_button = self._screen.gtk.Button(label=_("Cancel"), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.cancel_pressed)
        self.content.add(cancel_button)

    def cancel_pressed(self, widget):
        self._screen._menu_go_back()

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(self.next_step(self._screen))


class MoveToServicePosition(BaseWizardStep):
    def __init__(self, screen, first_purge=True):
        super().__init__(screen)
        self.first_purge = first_purge
        self.waiting_for_start = 5
        self.next_step = DoneDialog

    def activate(self, wizard):
        super().activate(wizard)

        self._screen._ws.klippy.gcode_script(f"G28")
        self._screen._ws.klippy.gcode_script(f"G0 X0 Y-100 Z250 F2000")

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        load_label = self._screen.gtk.Label("")
        load_label.set_margin_top(20)
        load_label.set_markup("<span size='large'>" + _("Printhead is moving...") + "</span>")
        self.content.add(load_label)

    def update_loop(self):
        self.waiting_for_start -= 1
        it = self._screen.printer.data['idle_timeout']
        if it["state"] not in ["Ready", "Idle"]:
            self.waiting_for_start = 0
        if self.waiting_for_start <= 0 and it["state"] in ["Ready", "Idle"]:
            self.wizard_manager.set_step(self.next_step(self._screen))


class DoneDialog(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("placeholder43", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Printhead has been moved to the service position.") + "</span>")
        self.content.add(heating_label)
        continue_button = self._screen.gtk.Button(label=_("Close"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self._screen._menu_go_back)
        self.content.add(continue_button)
        continue_button = self._screen.gtk.Button(label=_("Home and Close"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.home_and_close)
        self.content.add(continue_button)

    def home_and_close(self, widget):
        self._screen._ws.klippy.gcode_script(f"G28")
        self._screen._menu_go_back()