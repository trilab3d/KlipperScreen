import logging

import gi

import json

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf
from jinja2 import Template

from ks_includes.screen_panel import ScreenPanel


def create_panel(*args, **kwargs):
    return MenuPanel(*args, **kwargs)


class MenuPanel(ScreenPanel):
    j2_data = None

    def __init__(self, screen, title, items=None):
        super().__init__(screen, title)
        self.items = items
        self.create_menu_items()
        self.grid = self._gtk.HomogeneousGrid(row_homogenous=True, column_homogenous=True)
        self.grid.set_margin_left(20)
        self.grid.set_margin_right(20)
        self.grid.set_column_spacing(20)
        self.grid.set_row_spacing(20)
        self.grid.set_vexpand(False)
        self.scroll = self._gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.show_bg = True

    def activate(self):
        self.add_content()

    def add_content(self):
        for child in self.scroll.get_children():
            self.scroll.remove(child)
        if self._screen.vertical_mode:
            # self.scroll.add(self.arrangeMenuItems(self.items, 3))
            self.content.add(self.arrangeMenuItems(self.items, 3))
        else:
            self.scroll.add(self.arrangeMenuItems(self.items, 4))
        # if not self.content.get_children():
        #     self.content.add(self.scroll)

    def arrangeMenuItems(self, items, columns, expand_last=False):
        for child in self.grid.get_children():
            self.grid.remove(child)
        length = len(items)
        i = 0
        for item in items:
            key = list(item)[0]
            if not self.evaluate_enable(item[key]['enable']):
                logging.debug(f"X > {key}")
                continue

            if columns == 4:
                if length <= 4:
                    # Arrange 2 x 2
                    columns = 2
                elif 4 < length <= 6:
                    # Arrange 3 x 2
                    columns = 3

            col = i % columns
            row = int(i / columns)

            width = height = 1
            if expand_last is True and i + 1 == length and length % 2 == 1:
                width = 2

            self.grid.attach(self.labels[key], col, row, width, height)
            i += 1
        self.j2_data = None
        return self.grid

    def create_menu_items(self):
        for i, entry in enumerate(self.items):
            key = list(entry)[0]
            item = entry[key]
            scale = 1.1 if 12 < len(self.items) <= 16 else None  # hack to fit a 4th row

            printer = self._printer.get_printer_status_data()

            name = self._screen.env.from_string(item['name']).render(printer)
            icon = self._screen.env.from_string(item['icon']).render(printer) if item['icon'] else None
            style = self._screen.env.from_string(item['style']).render(printer) if item['style'] else None

            button = self._gtk.Button(icon, label=None, style=style or f"color{i % 4 + 1}", scale=scale)
            label = self._gtk.Label(name)
            
            grid = self._gtk.HomogeneousGrid(row_homogenous=False)
            grid.attach(button, 0, 0, 1, 1)
            grid.attach(label, 0, 1, 1, 1)

            button_width, _button_height = button.get_size_request()
            button.set_size_request(button_width, button_width) 

            if item['panel'] is not None:
                panel = self._screen.env.from_string(item['panel']).render(printer)
                button.connect("clicked", self.menu_item_clicked, panel, item)

            elif item['method'] is not None:
                params = {}

                if item['params'] is not False:
                    try:
                        p = self._screen.env.from_string(item['params']).render(printer)
                        params = json.loads(p)
                    except Exception as e:
                        logging.exception(f"Unable to parse parameters for [{name}]:\n{e}")
                        params = {}

                if item['confirm'] is not None:
                    button.connect("clicked", self._screen._confirm_send_action, item['confirm'], item['method'], params)
                else:
                    button.connect("clicked", self._screen._send_action, item['method'], params)
            else:
                button.connect("clicked", self._screen._go_to_submenu, key)
            self.labels[key] = grid

    def evaluate_enable(self, enable):
        if enable == "{{ moonraker_connected }}":
            logging.info(f"moonraker connected {self._screen._ws.connected}")
            return self._screen._ws.connected
        elif enable == "{{ camera_configured }}":
            return self.ks_printer_cfg and self.ks_printer_cfg.get("camera_url", None) is not None
        self.j2_data = self._printer.get_printer_status_data()
        try:
            j2_temp = Template(enable, autoescape=True)
            result = j2_temp.render(self.j2_data)
            return result == 'True'
        except Exception as e:
            logging.debug(f"Error evaluating enable statement: {enable}\n{e}")
            return False
