import json
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, simpledialog
import tkinter.messagebox as messagebox
import datetime
import os
import sys
import copy
import textwrap

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("System Logger - by firecooking")
        self.window_geometry = "1000x800"
        
        # Set window icon and taskbar icon
        try:
            favicon_path = self.resource_path(os.path.join("images", "logo.ico"))
            self.iconbitmap(default=favicon_path)
        except Exception as e:
            print(f"Warning: Could not load icons: {e}")

        self.bg_color = "#CACACA"
        self.fg_color = "#000000"
        self.entry_bg_color = "#ffffff"
        self.style = ttk.Style(self)
        self.style.theme_use("default")

        # default alter columns
        self.alter_columns = ["Name", "Birthday", "Pronouns", "Bio"]
        self.front_collapsed = False
        self.front_sort_order = "oldest"
        self.word_wrap_enabled = False
        self.wrap_update_after_id = None
        self.dragged_alter_item = None
        self.history = []
        self.redo_history = []
        self.restoring_history = False
        # input widths (pixels) and focus
        self.input_widths = {}
        self.input_widths_by_index = []
        self.last_focused_col = None

        self.load_settings()
        self.geometry(self.window_geometry)
        self.front_sort_variable = tk.StringVar(self, value=self.front_sort_order)
        self.word_wrap_variable = tk.BooleanVar(self, value=self.word_wrap_enabled)

        self.create_menu_bar()
        self.create_toolbar()
        self.bind_all("<Control-z>", self.handle_global_undo)
        self.bind_all("<Control-y>", self.handle_global_redo)

        # Alters frame with editable headings
        self.alters_frame = tk.Frame(self)
        self.alters_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        header_frame = tk.Frame(self.alters_frame)
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="Alters").pack(side=tk.LEFT, anchor=tk.W)
        tk.Button(header_frame, text="Edit Headings", command=self.open_edit_headings, padx=4, pady=2).pack(side=tk.LEFT, padx=6)
        self.tree = None
        self.build_alters_tree(self.alter_columns)

        # Frame for inputs (built dynamically from alter_columns)
        self.input_frame = tk.Frame(self)
        self.input_frame.pack(pady=10)
        self.editing_item = None
        self.input_entries = {}
        self.build_input_frame()

        # Front frame (moved below inputs)
        self.front_frame = tk.Frame(self)
        self.front_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        tk.Label(self.front_frame, text="Front").pack(anchor=tk.W)
        self.front_tree = ttk.Treeview(self.front_frame, columns=("Alter Name", "Timestamp"), show="headings", style="Custom.Treeview")
        self.front_tree.heading("Alter Name", text="Alter Name")
        self.front_tree.heading("Timestamp", text="Timestamp")
        self.front_tree.pack(fill=tk.BOTH, expand=True)
        self.front_tree.bind("<Configure>", self.schedule_word_wrap_update)
        self.front_tree.bind("<Double-1>", self.on_front_double_click)
        self.create_context_menus()

        self.load_entries_auto()

        self.configure_widget_colors(self)
        self.update_treeview_style()
        self.history = [self.get_current_data()]

        # restore front collapsed state
        if self.front_collapsed:
            self.collapse_front()

    def load_settings(self):
        settings_file = "settings.json"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                self.bg_color = settings.get("bg_color", self.bg_color)
                self.fg_color = settings.get("fg_color", self.fg_color)
                self.entry_bg_color = settings.get("entry_bg_color", self.entry_bg_color)
                # load saved alter column configuration and front collapsed state
                self.alter_columns = settings.get("alter_columns", self.alter_columns)
                self.front_collapsed = settings.get("front_collapsed", self.front_collapsed)
                self.front_sort_order = settings.get("front_sort_order", self.front_sort_order)
                if self.front_sort_order not in ("oldest", "newest"):
                    self.front_sort_order = "oldest"
                self.word_wrap_enabled = settings.get("word_wrap_enabled", self.word_wrap_enabled)
                self.window_geometry = settings.get("window_geometry", self.window_geometry)
                self.input_widths = settings.get("input_widths", self.input_widths)
                self.input_widths_by_index = settings.get("input_widths_by_index", self.input_widths_by_index)
                self.last_focused_col = settings.get("last_focused_col", self.last_focused_col)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load settings:\n{e}")

    def save_settings(self):
        settings_file = "settings.json"
        settings = {
            "bg_color": self.bg_color,
            "fg_color": self.fg_color,
            "entry_bg_color": self.entry_bg_color,
            "alter_columns": self.alter_columns,
            "front_collapsed": self.front_collapsed,
            "front_sort_order": self.front_sort_order,
            "word_wrap_enabled": self.word_wrap_enabled,
            "window_geometry": self.geometry(),
            "input_widths": self.input_widths,
            "input_widths_by_index": self.input_widths_by_index,
            "last_focused_col": self.last_focused_col,
        }
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

    def load_entries_auto(self):
        data_file = "data.json"
        if os.path.exists(data_file):
            try:
                with open(data_file, "r", encoding="utf-8") as file:
                    data = json.load(file)
                normalized = self.normalize_loaded_json(data)
                self.apply_normalized_data(normalized)

                # save normalized data back to data.json if it was legacy
                if not (isinstance(data, dict) and "alter_columns" in data and "alters" in data and "front" in data):
                    self.save_normalized_file(data_file, normalized)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load data:\n{e}")

    def save_entries_auto(self):
        self.sort_front_tree()
        self.apply_word_wrap()
        if self.save_data_to_file("data.json", "save data") and not self.restoring_history:
            self.record_history()

    def record_history(self):
        state = copy.deepcopy(self.get_current_data())
        if not self.history or state != self.history[-1]:
            self.history.append(state)
            self.redo_history.clear()

    def undo(self):
        if len(self.history) < 2:
            return
        self.redo_history.append(self.history.pop())
        self.restore_history(self.history[-1])

    def redo(self):
        if not self.redo_history:
            return
        state = self.redo_history.pop()
        self.history.append(state)
        self.restore_history(state)

    def handle_global_undo(self, event):
        if isinstance(self.focus_get(), (tk.Entry, tk.Text)):
            return
        self.undo()
        return "break"

    def handle_global_redo(self, event):
        if isinstance(self.focus_get(), (tk.Entry, tk.Text)):
            return
        self.redo()
        return "break"

    def restore_history(self, state):
        self.restoring_history = True
        try:
            self.apply_normalized_data(copy.deepcopy(state))
            self.save_data_to_file("data.json", "save data")
        finally:
            self.restoring_history = False

    def get_current_data(self):
        alters = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            alters.append({col: self.unwrap_value(values[i]) if i < len(values) else "" for i, col in enumerate(self.alter_columns)})

        front = []
        for item in self.front_tree.get_children():
            values = self.front_tree.item(item, "values")
            front.append({"Alter Name": self.unwrap_value(values[0]), "Timestamp": self.unwrap_value(values[1])})

        return {"alters": alters, "front": front, "alter_columns": self.alter_columns}

    def save_data_to_file(self, file_path, description):
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(self.get_current_data(), file, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to {description}:\n{e}")
            return False

    def apply_normalized_data(self, normalized):
        self.alter_columns = normalized["alter_columns"]
        self.build_alters_tree(self.alter_columns)
        self.tree.delete(*self.tree.get_children())
        for entry in normalized["alters"]:
            values = [entry.get(col, "") for col in self.alter_columns]
            self.tree.insert("", tk.END, values=tuple(values))

        self.front_tree.delete(*self.front_tree.get_children())
        for entry in normalized["front"]:
            self.front_tree.insert("", tk.END, values=(entry.get("Alter Name", ""), entry.get("Timestamp", "")))
        self.sort_front_tree()
        self.apply_word_wrap()

    def normalize_loaded_json(self, data):
        """Normalize loaded JSON into current schema: alters, front, alter_columns."""
        normalized = {
            "alters": [],
            "front": [],
            "alter_columns": self.alter_columns.copy(),
        }

        def extract_columns(entries):
            cols = []
            for entry in entries:
                if isinstance(entry, dict):
                    for key in entry.keys():
                        if key not in cols:
                            cols.append(key)
            return cols

        def normalize_entries(entries, columns):
            normalized_entries = []
            for entry in entries:
                if isinstance(entry, dict):
                    normalized_entries.append({col: entry.get(col, "") for col in columns})
            return normalized_entries

        if isinstance(data, list):
            if len(data) == 0:
                return normalized
            if all(isinstance(item, dict) for item in data):
                cols = extract_columns(data)
                normalized["alter_columns"] = cols or normalized["alter_columns"]
                normalized["alters"] = normalize_entries(data, normalized["alter_columns"])
                return normalized
        elif isinstance(data, dict):
            # Direct schema
            if "alters" in data or "front" in data:
                alters = data.get("alters", []) or []
                front = data.get("front", []) or []
                cols = data.get("alter_columns")
                if not cols and isinstance(alters, list) and alters:
                    cols = extract_columns(alters)
                normalized["alter_columns"] = cols if isinstance(cols, list) and cols else normalized["alter_columns"]
                normalized["alters"] = normalize_entries(alters or [], normalized["alter_columns"])
                normalized["front"] = [
                    {"Alter Name": item.get("Alter Name", ""), "Timestamp": item.get("Timestamp", "")} if isinstance(item, dict) else {}
                    for item in (front or [])
                ]
                return normalized
            # common alternate keys
            for key in ("entries", "data", "items", "characters", "alters_list"):
                if key in data and isinstance(data[key], list):
                    entries = data[key]
                    if all(isinstance(item, dict) for item in entries):
                        cols = extract_columns(entries)
                        normalized["alter_columns"] = cols or normalized["alter_columns"]
                        normalized["alters"] = normalize_entries(entries, normalized["alter_columns"])
                        return normalized
            # nested list of dicts
            for value in data.values():
                if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
                    cols = extract_columns(value)
                    normalized["alter_columns"] = cols or normalized["alter_columns"]
                    normalized["alters"] = normalize_entries(value, normalized["alter_columns"])
                    return normalized
            # single object as a single alter
            if all(isinstance(v, (str, int, float)) for v in data.values()):
                cols = list(data.keys())
                normalized["alter_columns"] = cols
                normalized["alters"] = [normalize_entries([data], cols)[0]]
                return normalized
        return normalized

    def save_normalized_file(self, file_path, normalized):
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(normalized, file, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update legacy file:\n{e}")

    def create_menu_bar(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Save to Current File", command=self.save_entries_auto)
        file_menu.add_command(label="Save As...", command=self.save_entries)
        file_menu.add_command(label="Load from File", command=self.load_entries)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Set Interface Colors...", command=self.choose_colors)
        settings_menu.add_command(label="Reset Colors", command=self.reset_colors)
        settings_menu.add_separator()
        settings_menu.add_command(label="Edit Headings...", command=self.open_edit_headings)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)

        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="Toggle Front Panel", command=self.toggle_front)
        view_menu.add_separator()
        view_menu.add_radiobutton(label="Front: Oldest First", variable=self.front_sort_variable, value="oldest", command=lambda: self.set_front_sort_order("oldest"))
        view_menu.add_radiobutton(label="Front: Newest First", variable=self.front_sort_variable, value="newest", command=lambda: self.set_front_sort_order("newest"))
        view_menu.add_checkbutton(label="Wrap Display Text", command=self.toggle_word_wrap, variable=self.word_wrap_variable)
        menu_bar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.open_shortcuts_popup)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "System Log by firecooking, buy me a coffee at https://ko-fi.com/firecooking"))
        menu_bar.add_cascade(label="Help", menu=help_menu)
        self.menu_bar = menu_bar
        self.menus = (file_menu, edit_menu, settings_menu, view_menu, help_menu)

    def create_toolbar(self):
        self.toolbar = tk.Frame(self, bd=2, relief=tk.RAISED)
        self.toolbar.pack(fill=tk.X, padx=10, pady=(5, 0))

        tk.Button(self.toolbar, text="Edit Selected", command=self.open_edit_entry_popup).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(self.toolbar, text="Toggle Front", command=self.toggle_front).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(self.toolbar, text="Undo", command=self.undo).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(self.toolbar, text="Redo", command=self.redo).pack(side=tk.LEFT, padx=4, pady=4)

    def open_shortcuts_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Keyboard Shortcuts")
        popup.geometry("520x390")
        popup.transient(self)

        shortcuts = (
            ("Ctrl+C", "Copy the selected row."),
            ("Ctrl+V", "Paste the previously copied row."),
            ("Ctrl+D", "Duplicate the selected row."),
            ("Ctrl+Z", "Undo the last change."),
            ("Ctrl+Y", "Redo what was undone."),
            ("Ctrl+W", "Turn word wrapping on or off in both displays."),
            ("Enter or Tab in an input", "Move to the next input, or add the entry from the last input."),
            ("Double-click a Front row", "Edit the Front entry."),
            ("Double-click a Alter row", "Edit the Alter entry."),
            ("Double-click an Alter heading", "Rename the heading."),
            ("Right-click a row", "Open actions for that row."),
            ("Drag an Alter row", "Move it to a different position."),
        )

        tk.Label(popup, text="Shortcuts", font=("TkDefaultFont", 11, "bold")).pack(anchor=tk.W, padx=14, pady=(14, 8))
        list_frame = tk.Frame(popup)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=14)

        for shortcut, description in shortcuts:
            row = tk.Frame(list_frame)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=shortcut, width=24, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=description, anchor=tk.W, justify=tk.LEFT, wraplength=340).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(popup, text="Close", command=popup.destroy).pack(pady=12)
        self.configure_widget_colors(popup)

    def configure_widget_colors(self, widget):
        if isinstance(widget, (tk.Tk, tk.Frame, tk.LabelFrame, tk.Toplevel)):
            widget.configure(bg=self.bg_color)
        elif isinstance(widget, tk.Label):
            widget.configure(bg=self.bg_color, fg=self.fg_color)
        elif isinstance(widget, tk.Button):
            widget.configure(bg=self.bg_color, fg=self.fg_color, activebackground=self.entry_bg_color, activeforeground=self.fg_color)
        elif isinstance(widget, tk.Entry):
            widget.configure(bg=self.entry_bg_color, fg=self.fg_color, insertbackground=self.fg_color)

        if isinstance(widget, tk.Menu):
            widget.configure(bg=self.bg_color, fg=self.fg_color, activebackground=self.entry_bg_color, activeforeground=self.fg_color)

        for child in widget.winfo_children():
            self.configure_widget_colors(child)

        if widget is self:
            for menu in getattr(self, "menus", ()) + tuple(
                menu for menu in (getattr(self, "alter_context_menu", None), getattr(self, "front_context_menu", None)) if menu
            ):
                menu.configure(bg=self.bg_color, fg=self.fg_color, activebackground=self.entry_bg_color, activeforeground=self.fg_color)

    def create_context_menus(self):
        self.alter_context_menu = tk.Menu(self, tearoff=0)
        self.alter_context_menu.add_command(label="Edit Selected", command=self.open_edit_entry_popup)
        self.alter_context_menu.add_command(label="Load Selected", command=self.load_selected)
        self.alter_context_menu.add_command(label="Add to Front", command=self.add_to_front)
        self.alter_context_menu.add_command(label="Remove Selected", command=self.remove_entry)
        self.alter_context_menu.add_command(label="Paste Entry", command=lambda: self.paste_tree_rows(self.tree))
        self.alter_context_menu.add_command(label="Duplicate Entry", command=lambda: self.duplicate_tree_row(self.tree))
        self.alter_context_menu.add_separator()
        self.alter_context_menu.add_command(label="Copy Row", command=lambda: self.copy_tree_row(self.tree))

        self.front_context_menu = tk.Menu(self, tearoff=0)
        self.front_context_menu.add_command(label="Edit Selected", command=self.open_edit_front_popup)
        self.front_context_menu.add_command(label="Remove from Front", command=self.remove_from_front)
        self.front_context_menu.add_command(label="Paste Entry", command=lambda: self.paste_tree_rows(self.front_tree))
        self.front_context_menu.add_command(label="Duplicate Entry", command=lambda: self.duplicate_tree_row(self.front_tree))
        self.front_context_menu.add_separator()
        self.front_context_menu.add_command(label="Copy Row", command=lambda: self.copy_tree_row(self.front_tree))

        self.tree.bind("<Button-3>", lambda event: self.show_context_menu(event, self.tree, self.alter_context_menu))
        self.front_tree.bind("<Button-3>", lambda event: self.show_context_menu(event, self.front_tree, self.front_context_menu))
        self.bind_tree_shortcuts(self.tree)
        self.bind_tree_shortcuts(self.front_tree)

    def bind_tree_shortcuts(self, tree):
        tree.bind("<Control-c>", lambda event: self.handle_tree_shortcut(event, tree, self.copy_tree_row))
        tree.bind("<Control-v>", lambda event: self.handle_tree_shortcut(event, tree, self.paste_tree_rows))
        tree.bind("<Control-d>", lambda event: self.handle_tree_shortcut(event, tree, self.duplicate_tree_row))
        tree.bind("<Control-w>", lambda event: self.handle_tree_shortcut(event, tree, lambda _: self.toggle_word_wrap()))

    def toggle_word_wrap(self):
        self.word_wrap_enabled = not self.word_wrap_enabled
        self.word_wrap_variable.set(self.word_wrap_enabled)
        self.apply_word_wrap()
        self.save_settings()

    def unwrap_value(self, value):
        return " ".join(str(value).splitlines())

    def apply_word_wrap(self):
        if not hasattr(self, "front_tree"):
            return
        trees = (self.tree, self.front_tree)
        max_lines = 1
        for tree in trees:
            for item in tree.get_children():
                values = list(tree.item(item, "values"))
                display_values = []
                for index, value in enumerate(values):
                    raw_value = self.unwrap_value(value)
                    if self.word_wrap_enabled:
                        width = max(8, int(tree.column(tree["columns"][index], "width") / 8))
                        wrapped = textwrap.fill(raw_value, width=width, break_long_words=True, break_on_hyphens=False)
                        max_lines = max(max_lines, wrapped.count("\n") + 1)
                        display_values.append(wrapped)
                    else:
                        display_values.append(raw_value)
                tree.item(item, values=tuple(display_values))
        self.style.configure("Custom.Treeview", rowheight=20 * max_lines if self.word_wrap_enabled else 20)

    def schedule_word_wrap_update(self, event=None):
        if not self.word_wrap_enabled or self.wrap_update_after_id is not None:
            return
        self.wrap_update_after_id = self.after(100, self.update_word_wrap)

    def update_word_wrap(self):
        self.wrap_update_after_id = None
        self.apply_word_wrap()

    def set_front_sort_order(self, order):
        self.front_sort_order = order
        self.front_sort_variable.set(order)
        self.sort_front_tree()
        self.save_settings()

    def sort_front_tree(self):
        rows = [(self.front_tree.item(item, "values"), item) for item in self.front_tree.get_children()]
        rows.sort(key=lambda row: row[0][1] if len(row[0]) > 1 else "", reverse=self.front_sort_order == "newest")
        for index, (_, item) in enumerate(rows):
            self.front_tree.move(item, "", index)

    def start_alter_drag(self, event):
        self.dragged_alter_item = self.tree.identify_row(event.y)

    def finish_alter_drag(self, event):
        item = self.dragged_alter_item
        self.dragged_alter_item = None
        if not item or not self.tree.exists(item):
            return
        target = self.tree.identify_row(event.y)
        if target == item:
            return
        target_index = self.tree.index(target) if target else "end"
        if target or target_index == "end":
            self.tree.move(item, "", target_index)
            self.tree.selection_set(item)
            self.tree.focus(item)
            self.save_entries_auto()

    def show_context_menu(self, event, tree, menu):
        item = tree.identify_row(event.y)
        if not item:
            return
        tree.selection_set(item)
        tree.focus(item)
        menu.tk_popup(event.x_root, event.y_root)

    def copy_tree_row(self, tree):
        selected = tree.selection()
        if not selected:
            return
        values = tree.item(selected[0], "values")
        self.clipboard_clear()
        self.clipboard_append("\t".join(self.unwrap_value(value) for value in values))

    def paste_tree_rows(self, tree):
        try:
            text = self.clipboard_get()
        except tk.TclError:
            messagebox.showwarning("Paste", "The clipboard does not contain text")
            return

        rows = []
        for line in text.splitlines():
            values = line.split("\t")
            if any(value.strip() for value in values):
                rows.append(tuple(values[:len(tree["columns"])]))

        if not rows:
            messagebox.showwarning("Paste", "No entries found in the clipboard")
            return

        column_count = len(tree["columns"])
        inserted = 0
        for values in rows:
            padded_values = values + ("",) * (column_count - len(values))
            if not padded_values[0].strip():
                continue
            tree.insert("", tk.END, values=padded_values)
            inserted += 1

        if inserted:
            self.save_entries_auto()
        if inserted < len(rows):
            messagebox.showwarning("Paste", "Entries without a name were skipped")

    def duplicate_tree_row(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Duplicate", "No entry selected")
            return
        item = selected[0]
        copy = tree.insert("", tk.END, values=tree.item(item, "values"))
        tree.selection_set(copy)
        tree.focus(copy)
        self.save_entries_auto()

    def handle_tree_shortcut(self, event, tree, action):
        action(tree)
        return "break"

    def on_front_double_click(self, event):
        if self.front_tree.identify_region(event.x, event.y) == "cell":
            self.open_edit_front_popup()

    def update_treeview_style(self):
        self.style.configure(
            "Custom.Treeview",
            background=self.bg_color,
            fieldbackground=self.entry_bg_color,
            foreground=self.fg_color,
        )
        self.style.map(
            "Custom.Treeview",
            background=[("selected", self.entry_bg_color)],
            foreground=[("selected", self.fg_color)],
        )
        self.style.configure("Custom.Treeview.Heading", background=self.bg_color, foreground=self.fg_color)

    def build_input_frame(self):
        # destroy existing inputs
        for child in self.input_frame.winfo_children():
            child.destroy()
        self.input_entries = {}

        # create label+entry per column
        for i, col in enumerate(self.alter_columns):
            tk.Label(self.input_frame, text=f"{col}:").grid(row=i, column=0, sticky=tk.W, padx=2, pady=2)
            ent = tk.Entry(self.input_frame)
            # restore width from saved pixels (approx to chars)
            saved_px = None
            if col in self.input_widths:
                saved_px = self.input_widths.get(col)
            elif i < len(self.input_widths_by_index):
                saved_px = self.input_widths_by_index[i]
            if saved_px:
                try:
                    chars = max(6, int(saved_px / 7))
                    ent.config(width=chars)
                except Exception:
                    pass
            ent.grid(row=i, column=1, padx=2, pady=2, sticky="we")
            self.input_entries[col] = ent
            # focus and size bindings
            ent.bind("<FocusIn>", lambda e, c=col: self.on_input_focus_in(c))
            ent.bind("<FocusOut>", lambda e, c=col, idx=i: self.on_input_focus_out(c, idx))
            ent.bind("<Return>", lambda e, idx=i: self.on_input_return(idx))
        # action buttons placed after fields
        btn_row = len(self.alter_columns)
        button_frame = tk.Frame(self.input_frame)
        button_frame.grid(row=btn_row, column=0, columnspan=3, pady=(12, 4), sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)

        add_button = tk.Button(button_frame, text="Add Entry", command=self.add_entry)
        add_button.grid(row=0, column=0, padx=4, sticky="ew")

        remove_button = tk.Button(button_frame, text="Remove Selected", command=self.remove_entry)
        remove_button.grid(row=0, column=1, padx=4, sticky="ew")

        edit_button = tk.Button(button_frame, text="Load Selected", command=self.load_selected)
        edit_button.grid(row=0, column=2, padx=4, sticky="ew")

        button_frame2 = tk.Frame(self.input_frame)
        button_frame2.grid(row=btn_row+1, column=0, columnspan=3, pady=(4, 12), sticky="ew")
        button_frame2.columnconfigure(0, weight=1)
        button_frame2.columnconfigure(1, weight=1)
        button_frame2.columnconfigure(2, weight=1)

        add_front_button = tk.Button(button_frame2, text="Add to Front", command=self.add_to_front)
        add_front_button.grid(row=0, column=0, padx=4, sticky="ew")

        remove_front_button = tk.Button(button_frame2, text="Remove from Front", command=self.remove_from_front)
        remove_front_button.grid(row=0, column=1, padx=4, sticky="ew")

        update_button = tk.Button(button_frame2, text="Update Entry", command=self.update_entry)
        update_button.grid(row=0, column=2, padx=4, sticky="ew")

        # allow entries to expand
        self.input_frame.columnconfigure(1, weight=1)

        # restore focus if possible
        if self.last_focused_col and self.last_focused_col in self.input_entries:
            try:
                self.input_entries[self.last_focused_col].focus_set()
            except Exception:
                pass

    def build_alters_tree(self, columns):
        # preserve existing rows
        existing = []
        if self.tree is not None:
            for item in self.tree.get_children():
                existing.append(self.tree.item(item, "values"))
            self.tree.destroy()

        self.tree = ttk.Treeview(self.alters_frame, columns=tuple(columns), show="headings", style="Custom.Treeview")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Configure>", self.schedule_word_wrap_update)
        # bind double-clicks for header editing
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        if hasattr(self, "alter_context_menu"):
            self.tree.bind("<Button-3>", lambda event: self.show_context_menu(event, self.tree, self.alter_context_menu))
            self.bind_tree_shortcuts(self.tree)
        self.tree.bind("<ButtonPress-1>", self.start_alter_drag)
        self.tree.bind("<ButtonRelease-1>", self.finish_alter_drag)

        # re-insert existing rows mapping by index
        for vals in existing:
            # truncate or pad to new column count
            newvals = list(vals[:len(columns)]) + [""] * max(0, len(columns) - len(vals))
            self.tree.insert("", tk.END, values=tuple(newvals))
        # rebuild input frame to match columns if input_frame already exists
        if hasattr(self, 'input_frame') and self.input_frame is not None:
            try:
                self.build_input_frame()
            except Exception:
                pass

    def on_tree_double_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            col = self.tree.identify_column(event.x)
            # col is like '#1'
            try:
                index = int(col.replace('#', '')) - 1
            except Exception:
                return
            if 0 <= index < len(self.alter_columns):
                self.rename_column_prompt(index)
        elif region == "cell":
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
                self.tree.focus(item)
                self.open_edit_entry_popup()

    def on_input_focus_in(self, col):
        self.last_focused_col = col

    def on_input_focus_out(self, col, idx):
        # record pixel width by reading widget width
        ent = self.input_entries.get(col)
        if not ent:
            return
        try:
            w = ent.winfo_width()
            self.input_widths[col] = w
            # ensure by-index list is long enough
            if idx >= len(self.input_widths_by_index):
                # extend list
                for _ in range(len(self.input_widths_by_index), idx+1):
                    self.input_widths_by_index.append(None)
            self.input_widths_by_index[idx] = w
            # persist UI preferences
            self.save_settings()
        except Exception:
            pass

    def on_input_return(self, idx):
        # focus next field or add entry
        if idx < len(self.alter_columns) - 1:
            next_col = self.alter_columns[idx+1]
            ent = self.input_entries.get(next_col)
            if ent:
                ent.focus_set()
        else:
            self.add_entry()

    def open_edit_entry_popup(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No alter selected")
            return

        item = selected[0]
        values = self.tree.item(item, "values")

        popup = tk.Toplevel(self)
        popup.title("Edit Alter Entry")
        popup.geometry("450x320")

        popup_entries = {}
        for i, col in enumerate(self.alter_columns):
            tk.Label(popup, text=f"{col}:").grid(row=i, column=0, sticky=tk.W, padx=10, pady=6)
            ent = tk.Entry(popup, width=40)
            if i < len(values):
                ent.insert(0, values[i])
            ent.grid(row=i, column=1, padx=10, pady=6, sticky="we")
            popup_entries[col] = ent
            popup.columnconfigure(1, weight=1)

        def save_popup_entry():
            new_values = []
            for col in self.alter_columns:
                ent = popup_entries.get(col)
                new_values.append(ent.get() if ent else "")

            first_label = self.alter_columns[0] if self.alter_columns else "Field"
            if not new_values or not new_values[0].strip():
                messagebox.showerror("Error", f"{first_label} is required")
                return

            self.tree.item(item, values=tuple(new_values))
            self.save_entries_auto()
            popup.destroy()

        buttons_frame = tk.Frame(popup)
        buttons_frame.grid(row=len(self.alter_columns), column=0, columnspan=2, pady=12)

        tk.Button(buttons_frame, text="Save", command=save_popup_entry).pack(side=tk.LEFT, padx=4)
        tk.Button(buttons_frame, text="Cancel", command=popup.destroy).pack(side=tk.LEFT, padx=4)

    def open_edit_front_popup(self):
        selected = self.front_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No front entry selected")
            return

        item = selected[0]
        values = self.front_tree.item(item, "values")
        popup = tk.Toplevel(self)
        popup.title("Edit Front Entry")
        popup.geometry("450x150")
        popup.transient(self)
        popup.grab_set()

        tk.Label(popup, text="Alter Name:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=8)
        name_entry = tk.Entry(popup, width=40)
        name_entry.insert(0, values[0] if values else "")
        name_entry.grid(row=0, column=1, padx=10, pady=8, sticky="we")

        tk.Label(popup, text="Timestamp:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=8)
        timestamp_entry = tk.Entry(popup, width=40)
        timestamp_entry.insert(0, values[1] if len(values) > 1 else "")
        timestamp_entry.grid(row=1, column=1, padx=10, pady=8, sticky="we")
        popup.columnconfigure(1, weight=1)

        def save_front_entry():
            alter_name = name_entry.get().strip()
            if not alter_name:
                messagebox.showerror("Error", "Alter Name is required", parent=popup)
                return
            self.front_tree.item(item, values=(alter_name, timestamp_entry.get()))
            self.save_entries_auto()
            popup.destroy()

        buttons_frame = tk.Frame(popup)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=8)
        tk.Button(buttons_frame, text="Save", command=save_front_entry).pack(side=tk.LEFT, padx=4)
        tk.Button(buttons_frame, text="Cancel", command=popup.destroy).pack(side=tk.LEFT, padx=4)
        name_entry.focus_set()

    def rename_column_prompt(self, index):
        old = self.alter_columns[index]
        new = simpledialog.askstring("Rename Column", f"Rename '{old}' to:", initialvalue=old)
        if new and new.strip():
            # preserve width by index: move saved width from old name to new name
            old_width = self.input_widths.get(old)
            if old_width is not None:
                self.input_widths[new.strip()] = old_width
                # remove old key
                try:
                    del self.input_widths[old]
                except Exception:
                    pass
            # also preserve by index list
            if index < len(self.input_widths_by_index):
                # nothing to change, widths are positional
                pass
            self.alter_columns[index] = new.strip()
            # rebuild tree with new headings
            self.build_alters_tree(self.alter_columns)
            self.save_entries_auto()
            # save to settings immediately
            self.save_settings()

    def open_edit_headings(self):
        dlg = tk.Toplevel(self)
        dlg.title("Edit Alter Headings")
        dlg.geometry("400x300")

        listbox = tk.Listbox(dlg)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for col in self.alter_columns:
            listbox.insert(tk.END, col)

        btn_frame = tk.Frame(dlg)
        btn_frame.pack(fill=tk.X, padx=10, pady=6)

        def add_col():
            name = simpledialog.askstring("Add Column", "Column name:", parent=dlg)
            if name:
                self.alter_columns.append(name)
                listbox.insert(tk.END, name)
                # keep index width list in sync
                self.input_widths_by_index.insert(len(self.input_widths_by_index), None)

        def remove_col():
            sel = listbox.curselection()
            if not sel:
                return
            i = sel[0]
            listbox.delete(i)
            # remove width entries by index and name
            colname = self.alter_columns[i]
            try:
                del self.input_widths[colname]
            except Exception:
                pass
            if i < len(self.input_widths_by_index):
                del self.input_widths_by_index[i]
            del self.alter_columns[i]

        def rename_col():
            sel = listbox.curselection()
            if not sel:
                return
            i = sel[0]
            name = simpledialog.askstring("Rename Column", "New name:", initialvalue=self.alter_columns[i], parent=dlg)
            if name:
                self.alter_columns[i] = name
                listbox.delete(i)
                listbox.insert(i, name)

        def move_up():
            sel = listbox.curselection()
            if not sel:
                return
            i = sel[0]
            if i == 0:
                return
            self.alter_columns[i-1], self.alter_columns[i] = self.alter_columns[i], self.alter_columns[i-1]
            # swap by-index widths as well
            if i < len(self.input_widths_by_index):
                self.input_widths_by_index[i-1], self.input_widths_by_index[i] = self.input_widths_by_index[i], self.input_widths_by_index[i-1]
            val = listbox.get(i)
            listbox.delete(i-1, i)
            listbox.insert(i-1, val)
            listbox.selection_set(i-1)

        def move_down():
            sel = listbox.curselection()
            if not sel:
                return
            i = sel[0]
            if i >= listbox.size() - 1:
                return
            self.alter_columns[i+1], self.alter_columns[i] = self.alter_columns[i], self.alter_columns[i+1]
            # swap by-index widths as well
            if i < len(self.input_widths_by_index) - 1:
                self.input_widths_by_index[i+1], self.input_widths_by_index[i] = self.input_widths_by_index[i], self.input_widths_by_index[i+1]
            val = listbox.get(i)
            listbox.delete(i, i+1)
            listbox.insert(i+1, val)
            listbox.selection_set(i+1)

        tk.Button(btn_frame, text="Add", command=add_col).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Remove", command=remove_col).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Rename", command=rename_col).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Up", command=move_up).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Down", command=move_down).pack(side=tk.LEFT, padx=4)

        def on_ok():
            # rebuild tree with new columns
            self.build_alters_tree(self.alter_columns)
            self.save_entries_auto()
            self.save_settings()
            dlg.destroy()

        tk.Button(dlg, text="OK", command=on_ok).pack(pady=6)

    def toggle_front(self):
        if getattr(self, 'front_visible', True):
            self.collapse_front()
        else:
            self.expand_front()

    def collapse_front(self):
        # hide front frame
        try:
            self.front_frame.pack_forget()
        except Exception:
            pass
        self.front_visible = False
        self.front_collapsed = True
        self.save_settings()

    def expand_front(self):
        self.front_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        self.front_visible = True
        self.front_collapsed = False
        self.save_settings()

    def choose_colors(self):
        bg_choice = colorchooser.askcolor(title="Choose background color", initialcolor=self.bg_color)
        if not bg_choice or not bg_choice[1]:
            return
        fg_choice = colorchooser.askcolor(title="Choose text color", initialcolor=self.fg_color)
        if not fg_choice or not fg_choice[1]:
            return
        entry_choice = colorchooser.askcolor(title="Choose entry background color", initialcolor=self.entry_bg_color)
        if not entry_choice or not entry_choice[1]:
            return

        self.bg_color = bg_choice[1]
        self.fg_color = fg_choice[1]
        self.entry_bg_color = entry_choice[1]
        self.configure_widget_colors(self)
        self.update_treeview_style()
        self.save_settings()

    def reset_colors(self):
        self.bg_color = "#CACACA"
        self.fg_color = "#000000"
        self.entry_bg_color = "#ffffff"
        self.configure_widget_colors(self)
        self.update_treeview_style()
        self.save_settings()

    def add_entry(self):
        # collect values from dynamic inputs in column order
        values = []
        for i, col in enumerate(self.alter_columns):
            ent = self.input_entries.get(col)
            val = ent.get() if ent else ""
            values.append(val)

        first_label = self.alter_columns[0] if self.alter_columns else "Field"
        if values and values[0].strip():
            self.tree.insert("", tk.END, values=tuple(values))
            # clear inputs
            for ent in self.input_entries.values():
                ent.delete(0, tk.END)
            self.save_entries_auto()
        else:
            messagebox.showerror("Error", f"{first_label} is required")

    def remove_entry(self):
        selected = self.tree.selection()
        if selected:
            self.tree.delete(selected)
            self.save_entries_auto()
        else:
            messagebox.showwarning("Warning", "No entry selected")

    def load_selected(self):
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            values = self.tree.item(item, "values")
            # populate dynamic inputs
            for i, col in enumerate(self.alter_columns):
                ent = self.input_entries.get(col)
                if ent:
                    ent.delete(0, tk.END)
                    if i < len(values):
                        ent.insert(0, values[i])
            self.editing_item = item
        else:
            messagebox.showwarning("Warning", "No alter selected")

    def update_entry(self):
        if self.editing_item:
            # collect values
            values = []
            for i, col in enumerate(self.alter_columns):
                ent = self.input_entries.get(col)
                val = ent.get() if ent else ""
                values.append(val)

            first_label = self.alter_columns[0] if self.alter_columns else "Field"
            if values and values[0].strip():
                self.tree.item(self.editing_item, values=tuple(values))
                for ent in self.input_entries.values():
                    ent.delete(0, tk.END)
                self.editing_item = None
                self.save_entries_auto()
            else:
                messagebox.showerror("Error", f"{first_label} is required")
        else:
            messagebox.showwarning("Warning", "No alter loaded for editing")

    def add_to_front(self):
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            values = self.tree.item(item, "values")
            alter_name = values[0]
            if alter_name:
                timestamp = datetime.datetime.now().isoformat()
                self.front_tree.insert("", tk.END, values=(alter_name, timestamp))
                self.save_entries_auto()
            else:
                messagebox.showwarning("Warning", "Selected alter has no name")
        else:
            messagebox.showwarning("Warning", "No alter selected")

    def remove_from_front(self):
        selected = self.front_tree.selection()
        if selected:
            self.front_tree.delete(selected)
            self.save_entries_auto()
        else:
            messagebox.showwarning("Warning", "No front entry selected")

    def save_entries(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Entries",
        )
        if not file_path:
            return

        if self.save_data_to_file(file_path, "save entries"):
            messagebox.showinfo("Saved", f"Entries saved to {file_path}")

    def load_entries(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Entries",
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            normalized = self.normalize_loaded_json(data)
            self.apply_normalized_data(normalized)
            self.record_history()

            if not (isinstance(data, dict) and "alter_columns" in data and "alters" in data and "front" in data):
                self.save_normalized_file(file_path, normalized)

            messagebox.showinfo("Loaded", f"Loaded {len(normalized['alters'])} alters and {len(normalized['front'])} front entries from {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load entries:\n{e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()