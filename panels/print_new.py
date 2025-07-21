# -*- coding: utf-8 -*-
import logging
import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango
from datetime import datetime

from ks_includes.screen_panel import ScreenPanel


def create_panel(*args):
    return PrintPanelNew(*args)

class PrintPanelNew(ScreenPanel):
    cur_directory = "gcodes"
    filelist = {'gcodes': {'directories': [], 'files': []}}
    file_limit = True

    def __init__(self, screen, title):
        super().__init__(screen, title)
        sortdir = self._config.get_main_config().get("print_sort_dir", "date_desc")
        sortdir = sortdir.split('_')
        if sortdir[0] not in ["name", "date"] or sortdir[1] not in ["asc", "desc"]:
            sortdir = ["date", "desc"]
        self.sort_current = [sortdir[0], 0 if sortdir[1] == "asc" else 1]  # 0 for asc, 1 for desc
        self.sort_current_func = None
        self.set_sort_func(self.sort_current)
        self.sort_items = {
            "name": _("Name"),
            "date": _("Date")
        }
        self.sort_icon = ["arrow-up", "arrow-down"]
        self.scroll = self._gtk.ScrolledWindow()
        self.directories = []
        self.labels['files'] = {}
        self.time_24 = self._config.get_main_config().getboolean("24htime", True)
        logging.info(f"24h time is {self.time_24}")

        sbox = Gtk.Box(spacing=0)
        sbox.set_vexpand(False)
        for i, (name, val) in enumerate(self.sort_items.items(), start=1):
            s = self._gtk.Button(None, val, f"color{i % 4}", .5, Gtk.PositionType.RIGHT, 1)
            s.get_style_context().add_class("buttons_slim")
            if name == self.sort_current[0]:
                s.set_image(self._gtk.Image(self.sort_icon[self.sort_current[1]], self._gtk.img_scale * self.bts))
            s.connect("clicked", self.change_sort, name)
            self.labels[f'sort_{name}'] = s
            sbox.add(s)
        refresh = self._gtk.Button("refresh", style="color4", scale=self.bts)
        refresh.get_style_context().add_class("buttons_slim")
        refresh.connect('clicked', self._refresh_files)
        sbox.add(refresh)
        sbox.set_hexpand(True)
        sbox.set_vexpand(False)

        pbox = Gtk.Box(spacing=0)
        pbox.set_hexpand(True)
        pbox.set_vexpand(False)
        self.labels['path'] = Gtk.Label()
        pbox.add(self.labels['path'])
        self.labels['path_box'] = pbox

        self.main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main.set_vexpand(True)
        self.main.pack_start(sbox, False, False, 0)
        self.main.pack_start(pbox, False, False, 0)
        self.main.pack_start(self.scroll, True, True, 0)

        self.dir_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.pending_panel = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.set_vexpand(False)
        box.set_hexpand(True)
        box.set_valign(Gtk.Align.CENTER)
        self.pending_animation = self._gtk.LoadingAnimation()
        label = Gtk.Label()
        label.set_markup(f"Processing metadata...\n")
        label.set_margin_top(20)
        box.add(self.pending_animation)
        box.add(label)
        self.pending_panel.add(box)

        GLib.idle_add(self.reload_files)

        self.scroll.add(self.dir_panel)
        self.content.add(self.main)
        self._screen.files.add_file_callback(self._callback)
        self.showing_rename = False

    def activate(self):
        self.cur_directory = "gcodes"
        self.file_limit = True
        self.reload_files()

    def change_sort(self, widget, key):
        self._screen.base_panel.click_overlay_handler()  # for LED on click
        if self.sort_current[0] == key:
            self.sort_current[1] = (self.sort_current[1] + 1) % 2
        else:
            oldkey = self.sort_current[0]
            logging.info(f"Changing sort_{oldkey} to {self.sort_items[self.sort_current[0]]}")
            self.labels[f'sort_{oldkey}'].set_image(None)
            self.labels[f'sort_{oldkey}'].show_all()
            self.sort_current = [key, 0]
        self.labels[f'sort_{key}'].set_image(self._gtk.Image(self.sort_icon[self.sort_current[1]],
                                                             self._gtk.img_scale * self.bts))
        self.labels[f'sort_{key}'].show()

        self.set_sort_func(self.sort_current)
        self.file_limit = True
        self.reload_files()

        self._config.set("main", "print_sort_dir", f'{key}_{"asc" if self.sort_current[1] == 0 else "desc"}')
        self._config.save_user_config_options()

    def _refresh_files(self, widget=None):
        self._files.refresh_files()
        self.file_limit = True
        self.reload_files()
        return False
    
    def reload_files(self, widget=None):
        self.labels['files'] = {}
        dirs = []
        files = []
        flist = list(filter(lambda x: x.startswith(self.cur_directory), (f"gcodes/{x}" for x in self._screen.files.get_file_list())))
        strip_len = len(self.cur_directory)+1
        flist = list(x[strip_len:] for x in flist)

        for f in flist:
            parts = f.split("/")
            if len(parts) > 1:
                dir = parts[0]
                if dir[0] != '.' and dir not in dirs:
                    dirs.append(dir)
            else:
                file = parts[0]
                files.append(file)

        dirs.sort(reverse=(self.sort_current[1] and self.sort_current[0] == "name"))
        files.sort(reverse=self.sort_current[1], key=self.sort_current_func)

        show_more_button = self.file_limit and len(files) > 20
        if show_more_button:
            files = files[0:20]

        self.directories = dirs

        for child in self.dir_panel.get_children():
            self.dir_panel.remove(child)

        for dir in dirs:
            self.dir_panel.add(self._create_row(f"{self.cur_directory}/{dir}"))

        for file in files:
            self.dir_panel.add(self._create_row(f"{self.cur_directory}/{file}",file))

        if show_more_button:
            self.dir_panel.add(self._create_load_more_button())

        self.dir_panel.show_all()

    def update_file(self, filename):
        GLib.idle_add(self.image_load, filename)

    def change_dir(self, widget, dir):
        logging.info(f"change_dir {dir}")
        self.cur_directory = dir
        self.file_limit = True
        self.reload_files()

    def set_sort_func(self, sortdir):
        if self.sort_current[0] == "date":
            def fn(f):
                return self._screen.files.get_file_info(f"{self.cur_directory}/{f}"[7:])['modified']
        else:
            def fn(f):
                return f
        self.sort_current_func = fn

    def _callback(self, newfiles, deletedfiles, updatedfiles=None):
        strip_len = len(self.cur_directory)+1
        for file in newfiles:
            filepath = f"gcodes/{file}"
            if filepath.startswith(self.cur_directory):
                relpath = filepath[strip_len:]
                parts = relpath.split("/")
                if len(parts) > 1:
                    if parts[0] not in self.directories:
                        self.reload_files()
                        return False
                else:
                    pass  #TODO
        if len(deletedfiles):
            #logging.info(f"some file removed, reload all")
            #self.reload_files()
            #return False
            pass  #TODO - deleted files are procesed one by one, this takes too long.
        if updatedfiles is not None:
            for file in updatedfiles:
                if f"gcodes/{file}" in self.labels['files']:
                    self.update_file(f"gcodes/{file}")
                    pass  #TODO
        return False
    
    def _create_row(self, fullpath, filename=None):
        name = Gtk.Label()
        name.get_style_context().add_class("print-filename")
        if filename:
            name.set_markup(f'<big><b>{os.path.splitext(filename)[0].replace("_", " ")}</b></big>')
        else:
            name.set_markup(f"<big><b>{os.path.split(fullpath)[-1]}</b></big>")
        name.set_hexpand(True)
        name.set_halign(Gtk.Align.START)
        name.set_line_wrap(True)
        name.set_line_wrap_mode(Pango.WrapMode.CHAR)

        info = Gtk.Label()
        info.set_hexpand(True)
        info.set_halign(Gtk.Align.START)
        info.get_style_context().add_class("print-info")

        delete = self._gtk.Button("delete", style="color1", scale=self.bts)
        delete.set_hexpand(False)
        #rename = self._gtk.Button("files", style="color2", scale=self.bts)
        #rename.set_hexpand(False)

        if filename:
            action = self._gtk.Button("print", style="color3")
            action.connect("clicked", self.confirm_print, fullpath[7:])
            info.set_markup(self.get_file_info_str(fullpath))
            icon = Gtk.Button()
            icon.connect("clicked", self.confirm_print, fullpath[7:])
            #delete.connect("clicked", self.confirm_delete_file, f"gcodes/{fullpath}")
            GLib.idle_add(self.image_load, fullpath)
        else:
            action = self._gtk.Button("load", style="color3")
            action.connect("clicked", self.change_dir, fullpath)
            icon = self._gtk.Button("folder")
            icon.connect("clicked", self.change_dir, fullpath)
            #delete.connect("clicked", self.confirm_delete_directory, fullpath)
        icon.set_hexpand(False)
        action.set_hexpand(False)
        action.set_halign(Gtk.Align.END)

        #delete.connect("clicked", self.confirm_delete_file, f"gcodes/{fullpath}")

        row = Gtk.Grid()
        row.get_style_context().add_class("frame-item")
        row.set_hexpand(True)
        row.set_vexpand(False)
        row.attach(icon, 0, 0, 1, 2)
        row.attach(name, 1, 0, 3, 1)
        row.attach(info, 1, 1, 1, 1)
        #row.attach(rename, 2, 1, 1, 1)
        row.attach(delete, 2, 1, 1, 1)

        if not filename or (filename and os.path.splitext(filename)[1] in [".gcode", ".g", ".gco", ".bgcode"]):
            row.attach(action, 4, 0, 1, 2)

        if filename is not None:
            self.labels['files'][fullpath] = {
                "icon": icon,
                "info": info,
                "name": name
            }

        return row
    
    def _create_load_more_button(self):
        def fn(widget):
            self.file_limit = False
            self.reload_files()

        action = self._gtk.Button(None, "Load all", style="color3")
        action.connect("clicked", fn)
        
        row = Gtk.Grid()
        row.get_style_context().add_class("frame-item")
        row.set_hexpand(True)
        row.set_vexpand(False)
        row.attach(action, 0, 0, 1, 1)

        return row
    
    def image_load(self, filepath):
        pixbuf = self.get_file_image(filepath[7:], small=True)
        if pixbuf is not None:
            self.labels['files'][filepath]['icon'].set_image(Gtk.Image.new_from_pixbuf(pixbuf))
        else:
            self.labels['files'][filepath]['icon'].set_image(self._gtk.Image("file"))
        return False
    
    def get_file_info_str(self, filename):

        fileinfo = self._screen.files.get_file_info(filename)
        if fileinfo is None:
            return
        info = _("Uploaded")
        if self.time_24:
            info += f':<b>  {datetime.fromtimestamp(fileinfo["modified"]):\n%Y-%m-%d %H:%M}</b>\n'
        else:
            info += f':<b>  {datetime.fromtimestamp(fileinfo["modified"]):\n%Y-%m-%d %I:%M %p}</b>\n'

        if "size" in fileinfo:
            info += _("Size") + f':  <b>{self.format_size(fileinfo["size"])}</b>\n'
        if "estimated_time" in fileinfo:
            info += _("Print Time") + f':  <b>{self.format_time(fileinfo["estimated_time"])}</b>'
        return info
    
    def back(self):
        parts = self.cur_directory.split("/")
        if len(parts) > 1:
            self.cur_directory = "/".join(parts[:-1])
            self.reload_files()
            return True
        return False
    
    def confirm_print(self, widget, filename):
        self._screen.base_panel.click_overlay_handler()  # for LED on click
        self._screen.show_panel(filename, "wizard", filename, 1, False, wizard="preprintWizardSteps.CheckMaintenance", wizard_name="File detail", wizard_data={"filename": filename})

    