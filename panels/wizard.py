import logging
import contextlib
from importlib import import_module
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel
from WizardSteps.baseWizardStep import BaseWizardStep


def create_panel(*args, **kvargs):
    return WizardPanel(*args, **kvargs)


class WizardPanel(ScreenPanel):
    def __init__(self, screen, title, **kvargs):
        super().__init__(screen, title)

        parts = kvargs['wizard'].split('.')
        name = kvargs['wizard_name']
        module = import_module(f"WizardSteps.{parts[0]}")

        self.name_label = self._gtk.Label("")
        #self.name_label.set_margin_top(10)
        self.name_label.set_margin_bottom(10)
        self.set_heading(name)

        if "data" in kvargs and kvargs["data"]:
            logging.info(f"Using wizard data: {kvargs['data']}")
            self.first_step_data = kvargs["data"]
        else:
            self.first_step_data = {}

        self.data_store = self.first_step_data

        self.first_step: BaseWizardStep = getattr(module,parts[1])(screen)
        self.current_step: BaseWizardStep = self.first_step
        self.current_step.activate(self)
        self.content.add(self.name_label)
        self.content.add(self.current_step.content)

    def activate(self, is_back=False, **kvargs):
        if not is_back:
            self.data_store = self.first_step_data
            self.set_step(self.first_step)
        self._screen.base_panel.show_back(self.current_step.can_back, self.current_step.can_exit)
        self.do_schedule_refresh = True
        GLib.timeout_add_seconds(1, self._update_loop)

    def deactivate(self):
        self.do_schedule_refresh = False

    def on_home(self):
        self.current_step.on_cancel()

    def get_wizard_data(self, key):
        if key in self.data_store:
            return self.data_store[key]
        else:
            return None

    def set_wizard_data(self, key, value):
        self.data_store[key] = value

    def _update_loop(self):
        if self.do_schedule_refresh:
            self.current_step.update_loop()
        return self.do_schedule_refresh

    def set_heading(self, name):
        self.name_label.set_markup(
            "<span size='xx-large'>" + name + "</span>")

    def set_step(self, step):
        logging.info(f"Setting wizard step {step}")
        self.current_step = step
        self.current_step.activate(self)
        for ch in self.content.get_children():
            self.content.remove(ch)
        self.content.add(self.name_label)
        self.content.add(self.current_step.content)
        self.content.show_all()

    def back(self):
        return self.current_step.on_back()
