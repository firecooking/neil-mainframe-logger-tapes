import json
import tkinter as tk
from tkinter import ttk, filedialog
import tkinter.messagebox as messagebox
import datetime

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Entry Tracker")
        self.geometry("1000x800")

        # Alters frame
        self.alters_frame = tk.Frame(self)
        self.alters_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tk.Label(self.alters_frame, text="Alters").pack(anchor=tk.W)
        self.tree = ttk.Treeview(self.alters_frame, columns=("Name", "Birthday", "Pronouns", "Bio"), show="headings")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Birthday", text="Birthday")
        self.tree.heading("Pronouns", text="Pronouns")
        self.tree.heading("Bio", text="Bio")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Front frame
        self.front_frame = tk.Frame(self)
        self.front_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tk.Label(self.front_frame, text="Front").pack(anchor=tk.W)
        self.front_tree = ttk.Treeview(self.front_frame, columns=("Alter Name", "Timestamp"), show="headings")
        self.front_tree.heading("Alter Name", text="Alter Name")
        self.front_tree.heading("Timestamp", text="Timestamp")
        self.front_tree.pack(fill=tk.BOTH, expand=True)

        # Frame for inputs
        frame = tk.Frame(self)
        frame.pack(pady=10)

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

        save_button = tk.Button(frame, text="Save Entries", command=self.save_entries)
        save_button.grid(row=5, column=0, pady=10)

        load_button = tk.Button(frame, text="Load Entries", command=self.load_entries)
        load_button.grid(row=5, column=1, pady=10)

        add_front_button = tk.Button(frame, text="Add to Front", command=self.add_to_front)
        add_front_button.grid(row=6, column=0, pady=10)

        remove_front_button = tk.Button(frame, text="Remove from Front", command=self.remove_from_front)
        remove_front_button.grid(row=6, column=1, pady=10)

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
        else:
            messagebox.showerror("Error", "Name is required")

    def remove_entry(self):
        selected = self.tree.selection()
        if selected:
            self.tree.delete(selected)
        else:
            messagebox.showwarning("Warning", "No entry selected")

    def add_to_front(self):
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            values = self.tree.item(item, "values")
            alter_name = values[0]
            if alter_name:
                timestamp = datetime.datetime.now().isoformat()
                self.front_tree.insert("", tk.END, values=(alter_name, timestamp))
            else:
                messagebox.showwarning("Warning", "Selected alter has no name")
        else:
            messagebox.showwarning("Warning", "No alter selected")

    def remove_from_front(self):
        selected = self.front_tree.selection()
        if selected:
            self.front_tree.delete(selected)
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