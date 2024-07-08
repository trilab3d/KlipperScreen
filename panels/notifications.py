import gi
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, Pango

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args, **kvargs):
    return NotificationsPanel(*args, **kvargs)


class NotificationsPanel(ScreenPanel):

    def __init__(self, screen, title, **kvargs):
        super().__init__(screen, title)

        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.content.add(scroll)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll.add(self.box)

        heading = Gtk.Label()
        heading.set_markup(f"<span size='xx-large'>Notifications</span>")
        heading.set_margin_bottom(10)
        self.box.add(heading)

    def activate(self):
        for child in self.box.get_children():
            self.box.remove(child)
        for notification in self._screen.base_panel.notification_states:
            if not self._screen.base_panel.notification_states[notification]:
                continue
            name = Gtk.Label()
            name.set_markup(f"<big><b>{self._screen.base_panel.NOTIFICATION_NAMES[notification]}</b></big>")
            name.set_hexpand(True)
            name.set_vexpand(True)
            name.set_halign(Gtk.Align.START)
            name.set_line_wrap(True)
            name.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            name.set_justify(Gtk.Justification.LEFT)

            desc = Gtk.Label(self._screen.base_panel.NOTIFICATION_TEXTS[notification])
            desc.set_hexpand(True)
            desc.set_vexpand(True)
            name.set_halign(Gtk.Align.START)
            desc.set_line_wrap(True)
            desc.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            desc.set_justify(Gtk.Justification.FILL)

            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            labels.set_halign(Gtk.Align.START)
            labels.set_margin_end(10)
            labels.add(name)
            labels.add(desc)

            dev = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            dev.get_style_context().add_class("frame-item")
            dev.set_hexpand(True)
            dev.set_vexpand(False)
            dev.set_valign(Gtk.Align.CENTER)

            dev.add(self._gtk.Image(self._screen.base_panel.WARNING_ICONS[notification], 80, 80))
            dev.add(labels)
            self.box.add(dev)