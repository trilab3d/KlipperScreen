import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from WizardSteps.baseWizardStep import BaseWizardStep

class ConfirmNoPrintPressent(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.next_step = MoveToServicePosition
        self.cancel_step = None

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("is_bed_clear", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Make sure the print volume is empty.") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)
        continue_button = self._screen.gtk.Button(label=_("Print volume empty, continue"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)
        if not self.cancel_step:
            cancel_button = self._screen.gtk.Button(label=_("Cancel"), style=f"color1")
            cancel_button.set_vexpand(False)
            cancel_button.connect("clicked", self.cancel_pressed)
            self.content.add(cancel_button)
        else:
            cancel_button = self._screen.gtk.Button(label=_("Continue in current position"), style=f"color1")
            cancel_button.set_vexpand(False)
            cancel_button.connect("clicked", self.cancel_step_pressed)
            self.content.add(cancel_button)

    def cancel_pressed(self, widget):
        self._screen._menu_go_back()

    def cancel_step_pressed(self, widget):
        self.wizard_manager.set_step(self.cancel_step(self._screen))

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
        self._screen._ws.klippy.gcode_script(f"M84")  # disable steppers

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("printhead_is_moving", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup("<span size='large'>" + _("Printhead is moving...") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)

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
        img = self._screen.gtk.Image("service_position", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Printhead has been moved to the service position.") + "</span>")
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_line_wrap(True)
        self.content.add(label)
        continue_button = self._screen.gtk.Button(label=_("Close"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self._screen._menu_go_back)
        self.content.add(continue_button)
        continue_button = self._screen.gtk.Button(label=_("Home Printhead and Close"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.home_and_close)
        self.content.add(continue_button)

    def home_and_close(self, widget):
        self._screen._ws.klippy.gcode_script(f"G28")
        self._screen._menu_go_back()