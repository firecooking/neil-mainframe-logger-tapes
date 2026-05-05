import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Entry Tracker")
        self.geometry("800x600")

        # Treeview for table
        self.tree = ttk.Treeview(self, columns=("Name", "Birthday", "Pronouns", "Bio"), show="headings")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Birthday", text="Birthday")
        self.tree.heading("Pronouns", text="Pronouns")
        self.tree.heading("Bio", text="Bio")
        self.tree.pack(fill=tk.BOTH, expand=True)

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

if __name__ == "__main__":
    app = App()
    app.mainloop()