import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel

has_gpio = False
try:
    import RPi.GPIO as GPIO
    has_gpio = True
    EMERGENCY_STOP_PIN = 27
except:
    pass

def create_panel(*args):
    return PostUpdatePanel(*args)

class PostUpdatePanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)
        self.screen = screen
        self.do_schedule_refresh = True
        self.last_emergency_state = False

        if has_gpio:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(EMERGENCY_STOP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.box.set_vexpand(True)
        header = Gtk.Label()
        header.set_margin_top(300)
        header.set_markup("<span size='xx-large'>"+_("Update almost done")+"</span>")
        self.box.add(header)

        self.emergency_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.emergency_box.set_vexpand(True)
        e_header = Gtk.Label()
        e_header.set_margin_top(60)
        e_header.set_markup("<span size='xx-large'>"+_("Emergency Stop Triggered!")+"</span>\n<span size='large'>Release Emerency Stop to continue.</span>")
        self.emergency_box.add(e_header)

        emergency_image_box = Gtk.Box()
        emergency_image_box.set_vexpand(True)
        image = self._gtk.Image("warning-big", self._gtk.content_width * .9, self._gtk.content_height * .9)
        emergency_image_box.add(image)
        self.emergency_box.add(emergency_image_box)

        self.fetch_post_update_status()
        GLib.timeout_add_seconds(1, self.fetch_post_update_status)

        self.content.add(self.box)

    def activate(self):
        self.fetch_post_update_status()
        GLib.timeout_add_seconds(1, self.fetch_post_update_status)

    def deactivate(self):
        self.do_schedule_refresh = False


    def fetch_post_update_status(self):
        logging.info("Called fetch_post_update_status")
        if has_gpio:
            logging.info("has gpio")
            if not GPIO.input(EMERGENCY_STOP_PIN):
                logging.info("Emergency triggered")
                if not self.last_emergency_state:
                    self.last_emergency_state = True
                    for ch in self.content.get_children():
                        self.content.remove(ch)
                    self.content.add(self.emergency_box)
                    self._screen.show_all()
                return self.do_schedule_refresh
            else:
                logging.info("Emergency NOT triggered")
                if self.last_emergency_state:
                    self.last_emergency_state = False
                    for ch in self.content.get_children():
                        self.content.remove(ch)
                    self.content.add(self.box)
                    self._screen.show_all()

        try:
            with open("/home/trilab/post-update-status","r") as f:
                status = f.readline()
                logging.info(f"Read post-update-status {status}")
                f.close()
            if status.strip() == "DONE":
                logging.info(f"post-update done, restart KS")
                self._screen.restart_ks()
        except Exception:
            pass

        return self.do_schedule_refresh

