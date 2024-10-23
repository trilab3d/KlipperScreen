import logging

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango
from datetime import datetime

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return StatisticsPanel(*args)


class StatisticsPanel(ScreenPanel):
    def __init__(self, screen, title):
        super().__init__(screen, title)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

        self.total_grid = Gtk.Grid()
        self.total_grid.set_column_spacing(20)
        self.total_grid.set_margin_top(10)
        self.total_grid.set_margin_bottom(10)
        self.total_grid.set_margin_start(10)
        self.total_grid.set_margin_end(10)
        self.total_grid.set_hexpand(True)
        #self.total_grid.get_style_context().add_class("frame-item")
        self.list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        lbl = Gtk.Label()
        lbl.set_markup("<span size='x-large'>" + _("Printer statistics") + "</span>")
        self.main_box.add(lbl)
        self.main_box.add(self.total_grid)
        lbl = Gtk.Label()
        lbl.set_markup("<span size='x-large'>" + _("Last prints") + "</span>")
        lbl.set_margin_top(10)
        self.main_box.add(lbl)
        scroll = self._gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.list_box)
        self.main_box.add(scroll)

        self.total_jobs_lbl = Gtk.Label(label=_("Total jobs:"))
        self.total_jobs_lbl.set_hexpand(True)
        self.total_jobs_lbl.set_halign(Gtk.Align.START)
        self.total_jobs_val = Gtk.Label(label="---")
        self.total_jobs_val.set_hexpand(True)
        self.total_jobs_val.set_halign(Gtk.Align.END)
        self.total_grid.attach(self.total_jobs_lbl, 0, 0, 1, 1)
        self.total_grid.attach(self.total_jobs_val, 1, 0, 1, 1)

        self.total_time_lbl = Gtk.Label(label=_("Total time:"))
        self.total_time_lbl.set_halign(Gtk.Align.START)
        self.total_time_val = Gtk.Label(label="---")
        self.total_time_val.set_halign(Gtk.Align.END)
        self.total_grid.attach(self.total_time_lbl, 0, 1, 1, 1)
        self.total_grid.attach(self.total_time_val, 1, 1, 1, 1)

        self.total_print_time_lbl = Gtk.Label(label=_("Total print time:"))
        self.total_print_time_lbl.set_halign(Gtk.Align.START)
        self.total_print_time_val = Gtk.Label(label="---")
        self.total_print_time_val.set_halign(Gtk.Align.END)
        self.total_grid.attach(self.total_print_time_lbl, 0, 2, 1, 1)
        self.total_grid.attach(self.total_print_time_val, 1, 2, 1, 1)

        self.total_filament_lbl = Gtk.Label(label=_("Filament consumed:"))
        self.total_filament_lbl.set_hexpand(True)
        self.total_filament_lbl.set_halign(Gtk.Align.START)
        self.total_filament_val = Gtk.Label(label="---")
        self.total_filament_val.set_halign(Gtk.Align.END)
        self.total_filament_val.set_hexpand(True)
        self.total_grid.attach(self.total_filament_lbl, 0, 3, 1, 1)
        self.total_grid.attach(self.total_filament_val, 1, 3, 1, 1)

        self.longest_job_lbl = Gtk.Label(label=_("Longest job:"))
        self.longest_job_lbl.set_halign(Gtk.Align.START)
        self.longest_job_val = Gtk.Label(label="---")
        self.longest_job_val.set_halign(Gtk.Align.END)
        self.total_grid.attach(self.longest_job_lbl, 0, 4, 1, 1)
        self.total_grid.attach(self.longest_job_val, 1, 4, 1, 1)

        self.longest_print_lbl = Gtk.Label(label=_("Longest print:"))
        self.longest_print_lbl.set_halign(Gtk.Align.START)
        self.longest_print_val = Gtk.Label(label="---")
        self.longest_print_val.set_halign(Gtk.Align.END)
        self.total_grid.attach(self.longest_print_lbl, 0, 5, 1, 1)
        self.total_grid.attach(self.longest_print_val, 1, 5, 1, 1)

        self.fetch_statistics()

        self.content.add(self.main_box)
        self.content.show_all()

    def activate(self):
        self.fetch_statistics()

    def fetch_statistics(self):
        self._screen._ws.send_method(
            "server.history.list",
            {},
            self.history_list_cb
        )
        self._screen._ws.send_method(
            "server.history.totals",
            {},
            self.history_total_cb
        )

    def history_list_cb(self, data, action, params):
        logging.info(f"history_list_cb action:{action}, data:{data}, param:{params}")
        for child in self.list_box.get_children():
            self.list_box.remove(child)
        for job in data["result"]["jobs"]:
            self._create_row(job)
        self.content.show_all()

    def history_total_cb(self, data, action, params):
        logging.info(f"history_total_cb action:{action}, data:{data}, param:{params}")
        totals = data["result"]["job_totals"]
        self.total_jobs_val.set_label(str(int(totals["total_jobs"])))
        self.total_time_val.set_label(self.format_time(totals["total_time"]))
        self.total_print_time_val.set_label(self.format_time(totals["total_print_time"]))
        self.total_filament_val.set_label(self.format_length(totals["total_filament_used"]))
        self.longest_job_val.set_label(self.format_time(totals["longest_job"]))
        self.longest_print_val.set_label(self.format_time(totals["longest_print"]))

    def _create_row(self, job):
        name = Gtk.Label()
        #name.get_style_context().add_class("print-filename")
        name.set_markup(f'<big><b>{job["filename"]}</b></big>')
        name.set_hexpand(True)
        name.set_halign(Gtk.Align.START)
        name.set_line_wrap(True)
        name.set_line_wrap_mode(Pango.WrapMode.CHAR)

        info = Gtk.Label()
        info.set_hexpand(True)
        info.set_halign(Gtk.Align.START)
        info.get_style_context().add_class("print-info")

        info_str = f'{_("Started")}: <b>{datetime.fromtimestamp(job["start_time"]):%Y-%m-%d %H:%M}</b>\n'
        info_str += f'{_("Status")}: <b>{job["status"]}</b>'
        info.set_markup(info_str)

        pixbuf = self.get_file_image(job["filename"])
        if pixbuf:
            thumb = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            thumb = self._gtk.Image("file")

        thumb.set_margin_end(10)

        if job["status"] == "completed":
            icon = self._gtk.Image("success",32,32)
        else:
            icon = self._gtk.Image("failed",32,32)

        row = Gtk.Grid()
        row.get_style_context().add_class("frame-item")
        row.set_hexpand(True)
        row.set_vexpand(False)
        row.attach(thumb, 0, 0, 1, 2)
        row.attach(name, 1, 0, 3, 1)
        row.attach(info, 1, 1, 1, 1)
        row.attach(icon, 4, 0, 1, 2)

        self.list_box.add(row)

    def format_length(self, l):
        if l < 1000:
            return f"{int(l)} mm"
        elif l < 9_999_000:
            return f"{int(l/1000)} m"
        else:
            return f"{int(l/100_000)/10} km"

    def format_time(self, t):
        parts = [0] * 6
        parts[0] = int(t / 31_556_926)  # years
        t = t % 31_556_926
        parts[1] = int(t / 2_629_743)  # months
        t = t % 2_629_743
        parts[2] = int(t / 86_400)  # days
        t = t % 86_400
        parts[3] = int(t / 3600)  # hours
        t = t % 3600
        parts[4] = int(t / 60)  # minutes
        t = t % 60
        parts[5] = int(t)  # seconds

        if parts[0] != 0:
            return f"{parts[0]}y {parts[1]}m"
        elif parts[1] != 0:
            return f"{parts[1]}m {parts[2]}d"
        elif parts[2] != 0:
            return f"{parts[2]}d {parts[3]}h"
        elif parts[3] != 0:
            return f"{parts[3]}h {parts[4]}m"
        elif parts[4] != 0:
            return f"{parts[4]}m {parts[5]}s"