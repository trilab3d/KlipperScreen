import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
from ks_includes.screen_panel import ScreenPanel

OVERSAMPLE_LIMIT = 2

def create_panel(*args, **kvargs):
    return HotSurfacesPanel(*args, **kvargs)

class HotSurfacesPanel(ScreenPanel):
    def __init__(self, screen, title, **kvargs):
        super().__init__(screen, title)
        self.screen = screen
        self.do_schedule_refresh = True

        self.oversample_counter = 0

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_vexpand(True)
        self.header = Gtk.Label()
        self.header.set_margin_top(40)
        self.header.set_margin_bottom(20)
        self.header.set_line_wrap(True)
        self.header.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.header.set_markup("<span size='xx-large'>" + _("Beware of Hot Surfaces!") + "</span>")
        box.add(self.header)

        image = self._gtk.Image("hot_surfaces", self._gtk.content_width * .9, self._gtk.content_height * .9)
        box.add(image)

        label = Gtk.Label(label=_("Some surfaces inside heated chamber are still dangerously hot and can burn you. "
                                "Please, pay maximal attention during manipulation inside heated chamber."))
        label.set_margin_top(10)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        box.add(label)

        button = self._screen.gtk.Button(label=_("Ok"), style=f"color1")
        button.set_vexpand(False)
        button.connect("clicked", self._screen._menu_go_back)
        box.add(button)

        self.content.add(box)

    def activate(self):
        self._screen.base_panel.show_back(False)
        self.do_schedule_refresh = True
        GLib.timeout_add_seconds(1, self.fetch_sensors)

    def deactivate(self):
        self.do_schedule_refresh = False

    def fetch_sensors(self):
        if not self.do_schedule_refresh:
            return False

        should_close = False
        if not self._screen.check_hot_surfaces():
            logging.info(f"Should back - temperature reason")
            should_close = True

        try:
            closed = self._printer.data["door_sensor"]["door_closed_raw"]
            if closed:
                logging.info(f"Should back - door reason")
                should_close = True
        except Exception as e:
            pass

        # wea re doing oversampling to prevent glitches on fast door toggling
        if should_close:
            self.oversample_counter += 1
        else:
            self.oversample_counter = 0

        if self.oversample_counter >= OVERSAMPLE_LIMIT:
            logging.info(f"Hot surfaces closing")
            self._screen._menu_go_back()
            return False

        return self.do_schedule_refresh