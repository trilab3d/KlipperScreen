import time

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango
import os
import logging
import subprocess
import configparser
from WizardSteps.baseWizardStep import BaseWizardStep

SEARCH_PATH = "/mnt/part4/opt/gcodes/usb/"
#SEARCH_PATH = "/home/thugmek/Desktop/usb-mockup/"

class ExportSlicerProfiles(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        if not os.path.exists(SEARCH_PATH):
           self.wizard_manager.set_step(NoUSB(self._screen))
           return

        img = self._screen.gtk.Image("slicer-profiles", self._screen.gtk.content_width * .945, -1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Export slicer profiles to USB") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)

        self.continue_button = self._screen.gtk.Button(label=_("continue"), style=f"color1")
        self.continue_button.set_vexpand(False)
        self.continue_button.connect("clicked", self.export_pressed)
        self.content.add(self.continue_button)
    def export_pressed(self, widget):
        self.can_back = False
        self.can_exit = False
        self.wizard_manager._screen.base_panel.show_back(self.can_back, self.can_exit)
        self.continue_button.set_sensitive(False)

        GLib.timeout_add(200,self.export_job)

    def export_job(self):
        logging.info("export job started")
        logging.info(f"exporting to /opt/gcodes/usb/")
        stdout, stderr = subprocess.Popen("cp /home/trilab/printer_data/profiles/prusa-pro-ht90-profiles.zip /opt/gcodes/usb/".split(" "),
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        logging.info(f"stdout: {stdout}, stderr: {stderr}")
        if len(stderr) == 0:
            stdout, stderr = subprocess.Popen("sync".split(" "),  stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE).communicate()
            logging.info(f"stdout: {stdout}, stderr: {stderr}")
        if len(stderr) != 0:
            self._screen.show_popup_message(_("Export failed"))
            self.wizard_manager.set_step(ExportSlicerProfiles(self._screen))
            return
        logging.info("Export done")
        time.sleep(3)
        self.wizard_manager.set_step(Exported(self._screen))
class NoUSB(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("warning43", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("No USB disk found") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)
        label = self._screen.gtk.Label("")
        #label.set_margin_top(20)
        label.set_markup(
            "<span size='small'>" + _("Insert USB disk where slicer profiles can be exported.") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)
        continue_button = self._screen.gtk.Button(label=_("Retry"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(ExportSlicerProfiles(self._screen))

class Exported(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.can_back = True

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("success_combined", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        label = self._screen.gtk.Label("")
        label.set_margin_top(20)
        label.set_markup(
            "<span size='large'>" + _("Slicer profiles was exported to USB") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)
        label = self._screen.gtk.Label("")
        # label.set_margin_top(20)
        label.set_markup(
            "<span size='small'>" + _("You can now remove USB disk and continue with importing in PrusaSlicer.") + "</span>")
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(label)
        close_button = self._screen.gtk.Button(label=_("Close"), style=f"color1")
        close_button.set_vexpand(False)
        close_button.connect("clicked", self.close_pressed)
        self.content.add(close_button)

    def close_pressed(self, widget):
        self._screen._menu_go_back()