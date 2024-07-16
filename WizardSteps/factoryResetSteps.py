import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from threading import Thread
import os
import logging

from WizardSteps.baseWizardStep import BaseWizardStep

class ConfirmFactoryReset(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("warning", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Are you sure you wish to perform factory reset of printer?") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        continue_button = self._screen.gtk.Button(label=_("Yes, continue"), style=f"color1")
        continue_button.set_vexpand(False)
        continue_button.connect("clicked", self.continue_pressed)
        self.content.add(continue_button)
        cancel_button = self._screen.gtk.Button(label=_("No, cancel"), style=f"color1")
        cancel_button.set_vexpand(False)
        cancel_button.connect("clicked", self.cancel_pressed)
        self.content.add(cancel_button)

    def cancel_pressed(self, widget):
        self._screen._menu_go_back()

    def continue_pressed(self, widget):
        self.wizard_manager.set_step(ConfirmFactoryResetSecond(self._screen))


class ConfirmFactoryResetSecond(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("warning", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("All data will be permanently removed.") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        continue_button = self._screen.gtk.Button(label=_("I'm sure, continue"), style=f"color1")
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
        self.wizard_manager.set_step(FactoryReset(self._screen))


class FactoryReset(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)
        self.progress = 0.0
        self.thread = Thread(target=self.reset_job)

    def activate(self, wizard):
        super().activate(wizard)
        self.thread.start()
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        img = self._screen.gtk.Image("factory_reset_in_progress", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Factory reset in progress...") + "</span>")
        heating_label.set_line_wrap(True)
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.content.add(heating_label)
        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_fraction(0)
        self.progressbar.set_show_text(False)
        self.progressbar.set_hexpand(True)
        self.content.add(self.progressbar)

    def update_loop(self):
        self.progressbar.set_fraction(self.progress)
        if self.progress >= 1:
            self.wizard_manager.set_step(FactoryResetDone(self._screen))

    def reset_job(self):
        logging.info(f"Reset job started")
        os.system("rm /home/trilab/printer_data/database/*")
        self.progress = 0.1
        logging.info(f"Reset job - database removed")
        gcode_path = "/home/trilab/printer_data/gcodes/"
        num_gcodes = 0
        for f in os.listdir(gcode_path):
            if not os.path.islink(gcode_path + f):
                num_gcodes += 1
        logging.info(f"Reset job - numgcodes: {num_gcodes}")
        if num_gcodes > 0:
            for f in os.listdir(gcode_path):
                if not os.path.islink(gcode_path + f):
                    os.system(f"rm -rf \"{gcode_path + f}\"")
                    self.progress += 0.5/num_gcodes
                    logging.info(f"Reset job - removed gcode \"{gcode_path + f}\"")
        else:
            self.progress += 0.5
        logging.info(f"Reset job - all gcodes removed")

        self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=nozzle VALUE='\"NONE\"'")
        self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=loaded_filament VALUE='\"NONE\"'")
        self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=last_filament VALUE='\"NONE\"'")
        self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=disable-door-sensor VALUE=False")
        self._screen._ws.klippy.gcode_script(f"SAVE_VARIABLE VARIABLE=disable-filament-sensor VALUE=False")
        logging.info(f"Reset job - saved variables reset")

        self._screen.tpcclient.send_request(f"set_hostname", "POST", body={"hostname": ""})
        self.progress += 0.2
        logging.info(f"Reset job - hostname reset")
        self._screen.tpcclient.send_request(f"credentials", "POST", body={"user": "", "password": ""})
        logging.info(f"Reset job - credentials reset")
        self._screen.tpcclient.send_request(f"settings", "POST", body={"locked": False})
        logging.info(f"Reset job - locked reset")
        self._screen.tpcclient.send_request(f"settings", "POST", body={
            "connect": {
                "enable": True,
                "hostname": "connect.prusa3d.com",
                "port": None,
                "tls": True,
                "token": ""
            }})

        try:
            connections = self._screen.tpcclient.send_request(f"/network-manager/list-connections", "GET")["connections"]
            for connection in connections:
                if "TYPE" in connection and connection["TYPE"] in ("ethernet", "wifi"):
                    if "UUID" in connection:
                        logging.info(f"removing connection {connection}")
                        self._screen.tpcclient.send_request(f"/network-manager/delete-connection/{connection['UUID']}", "POST")
            os.system("systemctl restart NetworkManager")
        except Exception as e:
            logging.error(f"Error on removing connections: {e}")

        os.system("systemctl restart prusa-connect-ht90")
        logging.info(f"Reset job - prusaconnect reset")
        os.system("echo Welcome > /opt/init_state")
        os.system("systemctl restart klipper-screen")
        self.progress = 1


class FactoryResetDone(BaseWizardStep):
    def __init__(self, screen):
        super().__init__(screen)

    def activate(self, wizard):
        super().activate(wizard)
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        # SEM FAJKFKU
        img = self._screen.gtk.Image("success_combined", self._screen.gtk.content_width * .945,-1)
        self.content.add(img)
        heating_label = self._screen.gtk.Label("")
        heating_label.set_margin_top(20)
        heating_label.set_markup(
            "<span size='large'>" + _("Printer was reset to factory defaults.") + "</span>")
        heating_label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        heating_label.set_line_wrap(True)
        self.content.add(heating_label)
        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_fraction(0)
        self.progressbar.set_show_text(False)
        self.progressbar.set_hexpand(True)
        self.content.add(self.progressbar)