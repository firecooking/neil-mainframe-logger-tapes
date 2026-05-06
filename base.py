import json
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser
import tkinter.messagebox as messagebox
import datetime
import os

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("System Log - by firecooking")
        self.geometry("1000x800")

        self.bg_color = "#CACACA"
        self.fg_color = "#000000"
        self.entry_bg_color = "#ffffff"
        self.style = ttk.Style(self)
        self.style.theme_use("default")

        self.load_settings()

        self.create_menu_bar()
        self.create_toolbar()

        # Alters frame
        self.alters_frame = tk.Frame(self)
        self.alters_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tk.Label(self.alters_frame, text="Alters").pack(anchor=tk.W)
        self.tree = ttk.Treeview(self.alters_frame, columns=("Name", "Birthday", "Pronouns", "Bio"), show="headings", style="Custom.Treeview")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Birthday", text="Birthday")
        self.tree.heading("Pronouns", text="Pronouns")
        self.tree.heading("Bio", text="Bio")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Front frame
        self.front_frame = tk.Frame(self)
        self.front_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tk.Label(self.front_frame, text="Front").pack(anchor=tk.W)
        self.front_tree = ttk.Treeview(self.front_frame, columns=("Alter Name", "Timestamp"), show="headings", style="Custom.Treeview")
        self.front_tree.heading("Alter Name", text="Alter Name")
        self.front_tree.heading("Timestamp", text="Timestamp")
        self.front_tree.pack(fill=tk.BOTH, expand=True)

        self.load_entries_auto()

        # Frame for inputs
        frame = tk.Frame(self)
        frame.pack(pady=10)
        self.editing_item = None

        tk.Label(frame, text="Name:").grid(row=0, column=0)
        self.name_entry = tk.Entry(frame)
        self.name_entry.grid(row=0, column=1)

        tk.Label(frame, text="Birthday:").grid(row=1, column=0)
        self.birthday_entry = tk.Entry(frame)
        self.birthday_entry.grid(row=1, column=1)

        tk.Label(frame, text="Pronouns:").grid(row=2, column=0)
        self.pronouns_entry = tk.Entry(frame)
        self.pronouns_entry.grid(row=2, column=1)

        tk.Label(frame, text="Bio:").grid(row=3, column=0)
        self.bio_entry = tk.Entry(frame)
        self.bio_entry.grid(row=3, column=1)

        # Buttons
        add_button = tk.Button(frame, text="Add Entry", command=self.add_entry)
        add_button.grid(row=4, column=0, pady=10)

        remove_button = tk.Button(frame, text="Remove Selected", command=self.remove_entry)
        remove_button.grid(row=4, column=1, pady=10)

        edit_button = tk.Button(frame, text="Load Selected", command=self.load_selected)
        edit_button.grid(row=4, column=2, pady=10)

        add_front_button = tk.Button(frame, text="Add to Front", command=self.add_to_front)
        add_front_button.grid(row=5, column=0, pady=10)

        remove_front_button = tk.Button(frame, text="Remove from Front", command=self.remove_from_front)
        remove_front_button.grid(row=5, column=1, pady=10)

        update_button = tk.Button(frame, text="Update Entry", command=self.update_entry)
        update_button.grid(row=5, column=2, pady=10)

        self.configure_widget_colors(self)
        self.update_treeview_style()

    def load_settings(self):
        settings_file = "settings.json"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                self.bg_color = settings.get("bg_color", self.bg_color)
                self.fg_color = settings.get("fg_color", self.fg_color)
                self.entry_bg_color = settings.get("entry_bg_color", self.entry_bg_color)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load settings:\n{e}")

    def save_settings(self):
        settings_file = "settings.json"
        settings = {
            "bg_color": self.bg_color,
            "fg_color": self.fg_color,
            "entry_bg_color": self.entry_bg_color
        }
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")

    def load_entries_auto(self):
        data_file = "data.json"
        if os.path.exists(data_file):
            try:
                with open(data_file, "r", encoding="utf-8") as file:
                    data = json.load(file)

                alters = data.get("alters", [])
                front = data.get("front", [])

                self.tree.delete(*self.tree.get_children())
                for entry in alters:
                    self.tree.insert(
                        "",
                        tk.END,
                        values=(
                            entry.get("Name", ""),
                            entry.get("Birthday", ""),
                            entry.get("Pronouns", ""),
                            entry.get("Bio", ""),
                        ),
                    )

                self.front_tree.delete(*self.front_tree.get_children())
                for entry in front:
                    self.front_tree.insert(
                        "",
                        tk.END,
                        values=(
                            entry.get("Alter Name", ""),
                            entry.get("Timestamp", ""),
                        ),
                    )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load data:\n{e}")

    def save_entries_auto(self):
        alters = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            alters.append({
                "Name": values[0],
                "Birthday": values[1],
                "Pronouns": values[2],
                "Bio": values[3],
            })

        front = []
        for item in self.front_tree.get_children():
            values = self.front_tree.item(item, "values")
            front.append({
                "Alter Name": values[0],
                "Timestamp": values[1],
            })

        data = {"alters": alters, "front": front}

        try:
            with open("data.json", "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data:\n{e}")

    def create_menu_bar(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Save to File", command=self.save_entries)
        file_menu.add_command(label="Load from File", command=self.load_entries)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Set Interface Colors...", command=self.choose_colors)
        settings_menu.add_command(label="Reset Colors", command=self.reset_colors)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "System Log by firecooking, buy me a coffee at https://ko-fi.com/firecooking"))
        menu_bar.add_cascade(label="Help", menu=help_menu)

    def create_toolbar(self):
        self.toolbar = tk.Frame(self, bd=2, relief=tk.RAISED)
        self.toolbar.pack(fill=tk.X)

        toolbar_buttons = [
            ("Add Entry", self.add_entry),
            ("Remove Selected", self.remove_entry),
            ("Load Selected", self.load_selected),
            ("Update Entry", self.update_entry),
            ("Add to Front", self.add_to_front),
            ("Remove from Front", self.remove_from_front)
        ]

        for text, command in toolbar_buttons:
            button = tk.Button(self.toolbar, text=text, command=command)
            button.pack(side=tk.LEFT, padx=2, pady=2)

    def configure_widget_colors(self, widget):
        if isinstance(widget, (tk.Frame, tk.LabelFrame)):
            widget.configure(bg=self.bg_color)
        elif isinstance(widget, tk.Label):
            widget.configure(bg=self.bg_color, fg=self.fg_color)
        elif isinstance(widget, tk.Button):
            widget.configure(bg=self.bg_color, fg=self.fg_color, activebackground=self.entry_bg_color, activeforeground=self.fg_color)
        elif isinstance(widget, tk.Entry):
            widget.configure(bg=self.entry_bg_color, fg=self.fg_color, insertbackground=self.fg_color)

        for child in widget.winfo_children():
            self.configure_widget_colors(child)

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
        name = self.name_entry.get()
        birthday = self.birthday_entry.get()
        pronouns = self.pronouns_entry.get()
        bio = self.bio_entry.get()
        if name:
            self.tree.insert("", tk.END, values=(name, birthday, pronouns, bio))
            self.name_entry.delete(0, tk.END)
            self.birthday_entry.delete(0, tk.END)
            self.pronouns_entry.delete(0, tk.END)
            self.bio_entry.delete(0, tk.END)
            self.save_entries_auto()
        else:
            messagebox.showerror("Error", "Name is required")

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
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, values[0])
            self.birthday_entry.delete(0, tk.END)
            self.birthday_entry.insert(0, values[1])
            self.pronouns_entry.delete(0, tk.END)
            self.pronouns_entry.insert(0, values[2])
            self.bio_entry.delete(0, tk.END)
            self.bio_entry.insert(0, values[3])
            self.editing_item = item
        else:
            messagebox.showwarning("Warning", "No alter selected")

    def update_entry(self):
        if self.editing_item:
            name = self.name_entry.get()
            birthday = self.birthday_entry.get()
            pronouns = self.pronouns_entry.get()
            bio = self.bio_entry.get()
            if name:
                self.tree.item(self.editing_item, values=(name, birthday, pronouns, bio))
                self.name_entry.delete(0, tk.END)
                self.birthday_entry.delete(0, tk.END)
                self.pronouns_entry.delete(0, tk.END)
                self.bio_entry.delete(0, tk.END)
                self.editing_item = None
                self.save_entries_auto()
            else:
                messagebox.showerror("Error", "Name is required")
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
        alters = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            alters.append({
                "Name": values[0],
                "Birthday": values[1],
                "Pronouns": values[2],
                "Bio": values[3],
            })

        front = []
        for item in self.front_tree.get_children():
            values = self.front_tree.item(item, "values")
            front.append({
                "Alter Name": values[0],
                "Timestamp": values[1],
            })

        data = {"alters": alters, "front": front}

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Entries",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            messagebox.showinfo("Saved", f"Entries saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save entries:\n{e}")

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

            alters = data.get("alters", [])
            front = data.get("front", [])

            self.tree.delete(*self.tree.get_children())
            for entry in alters:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        entry.get("Name", ""),
                        entry.get("Birthday", ""),
                        entry.get("Pronouns", ""),
                        entry.get("Bio", ""),
                    ),
                )

            self.front_tree.delete(*self.front_tree.get_children())
            for entry in front:
                self.front_tree.insert(
                    "",
                    tk.END,
                    values=(
                        entry.get("Alter Name", ""),
                        entry.get("Timestamp", ""),
                    ),
                )

            messagebox.showinfo("Loaded", f"Loaded {len(alters)} alters and {len(front)} front entries from {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load entries:\n{e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()