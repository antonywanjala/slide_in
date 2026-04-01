import csv
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, timedelta

# --- Modern Visual Constants ---
BG_MAIN = "#0f172a"  # Deep Midnight
BG_CARD = "#1e293b"  # Slate Blue-Grey
ACCENT = "#38bdf8"  # Sky Blue
TEXT_COLOR = "#f8fafc"
DANGER = "#ef4444"
WARNING = "#f59e0b"

# Global format constant for consistency
DT_FORMAT = "%Y-%m-%d %H:%M"


class Activity:
    def __init__(self, name, act_type, start, end):
        self.name = name
        self.act_type = act_type
        self.start = start
        self.end = end


class ActivitySchedulerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Activity Scheduler Pro")
        self.root.geometry("1100x800")
        self.root.configure(bg=BG_MAIN)
        self.root.minsize(900, 700)

        self.activities = []
        self.sort_column = None
        self.sort_clicks = 0

        self.type_colors = {}
        self.color_palette = ["#1e3a8a", "#581c87", "#064e3b", "#7c2d12", "#4c1d95", "#831843"]

        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=BG_CARD,
                        foreground=TEXT_COLOR,
                        fieldbackground=BG_CARD,
                        rowheight=35,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background="#334155",
                        foreground=ACCENT,
                        relief="flat",
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[('selected', ACCENT)], foreground=[('selected', "black")])

    def create_widgets(self):
        self.main_container = tk.Frame(self.root, bg=BG_MAIN)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)

        tk.Label(self.main_container, text="ACTIVITY SCHEDULER PRO", font=("Segoe UI", 26, "bold"),
                 bg=BG_MAIN, fg=ACCENT).pack(pady=(10, 20))

        tk.Label(self.main_container, text="ADD NEW ACTIVITY", font=("Segoe UI", 12, "bold"),
                 bg=BG_MAIN, fg=TEXT_COLOR).pack(pady=5)

        input_frame = tk.Frame(self.main_container, bg=BG_CARD, padx=20, pady=20,
                               highlightthickness=1, highlightbackground="#334155")
        input_frame.pack(fill="x", pady=10)

        labels = ["NAME", "TYPE", "START (YYYY-MM-DD HH:MM)", "END (YYYY-MM-DD HH:MM)"]
        self.entries = {}
        vars_map = ["ent_name", "ent_type", "ent_start", "ent_end"]

        for i in range(4):
            input_frame.columnconfigure(i, weight=1)
            f = tk.Frame(input_frame, bg=BG_CARD)
            f.grid(row=0, column=i, padx=10, sticky="ew")

            tk.Label(f, text=labels[i], bg=BG_CARD, fg="#94a3b8", font=("Segoe UI", 8, "bold")).pack(anchor="w")
            ent = tk.Entry(f, bg="#0f172a", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 11))
            ent.pack(fill="x", pady=5)
            self.entries[vars_map[i]] = ent

        self.btn_add = tk.Button(input_frame, text="ADD TO TIMELINE", command=self.add_activity,
                                 bg=ACCENT, fg="black", font=("Segoe UI", 10, "bold"),
                                 relief="flat", cursor="hand2", padx=20, pady=5)
        self.btn_add.grid(row=1, column=0, columnspan=4, pady=(15, 0))

        filter_frame = tk.Frame(self.main_container, bg=BG_MAIN)
        filter_frame.pack(fill="x", pady=10)

        tk.Label(filter_frame, text="Filter by Type:", bg=BG_MAIN, fg="#94a3b8", font=("Segoe UI", 10)).pack(
            side="left")
        self.filter_var = tk.StringVar(value="All")
        self.filter_menu = ttk.Combobox(filter_frame, textvariable=self.filter_var, state="readonly", width=20)
        self.filter_menu.pack(side="left", padx=10)
        self.filter_menu.bind("<<ComboboxSelected>>", lambda e: self.update_table())

        self.table_frame = tk.Frame(self.main_container, bg=BG_MAIN)
        self.table_frame.pack(fill="both", expand=True)

        columns = ("NAME", "TYPE", "START", "END")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col))
            self.tree.column(col, anchor="center", width=150)

        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_bar = tk.Frame(self.main_container, bg=BG_MAIN, pady=20)
        btn_bar.pack(fill="x")
        for i in range(4): btn_bar.columnconfigure(i, weight=1)

        tk.Button(btn_bar, text="Find Free Slot", command=self.open_free_slot_window, bg="#334155", fg="white",
                  relief="flat", font=("Segoe UI", 10), pady=10).grid(row=0, column=0, padx=5, sticky="ew")

        tk.Button(btn_bar, text="Import Activities", command=self.import_csv, bg="#334155", fg="white",
                  relief="flat", font=("Segoe UI", 10), pady=10).grid(row=0, column=1, padx=5, sticky="ew")

        tk.Button(btn_bar, text="Export Activities", command=self.export_csv, bg="#334155", fg="white",
                  relief="flat", font=("Segoe UI", 10), pady=10).grid(row=0, column=2, padx=5, sticky="ew")

        tk.Button(btn_bar, text="Purge All", command=self.purge_all, bg=DANGER, fg="white",
                  relief="flat", font=("Segoe UI", 10, "bold"), pady=10).grid(row=0, column=3, padx=5, sticky="ew")

    def flexible_date_parse(self, date_str):
        """Attempts to parse dates using various formats to gracefully handle seconds or slight variations."""
        formats = [
            "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S",  # 2026-04-01 15:30
            "%m/%d/%Y %H:%M", "%m/%d/%Y %H:%M:%S",  # 4/11/2026 12:00
            "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S",  # 11/04/2026 12:00
            "%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S",  # 2026/04/01 15:30
            "%m-%d-%Y %H:%M", "%m-%d-%Y %H:%M:%S",  # 4-11-2026 12:00
            "%d-%m-%Y %H:%M", "%d-%m-%Y %H:%M:%S",  # 11-4-2026 12:00
            "%Y.%m.%d %H:%M", "%Y.%m.%d %H:%M:%S"  # 2026.04.01 15:30
        ]
        date_str = date_str.strip()
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                pass

        # If none of the formats match, raise an error
        raise ValueError(f"Cannot parse date: {date_str}")

    def add_activity(self):
        vals = {k: v.get().strip() for k, v in self.entries.items()}
        if not all(vals.values()):
            messagebox.showwarning("Incomplete Data", "All fields must be entered.")
            return

        try:
            start_dt = self.flexible_date_parse(vals['ent_start'])
            end_dt = self.flexible_date_parse(vals['ent_end'])

            if end_dt <= start_dt:
                messagebox.showerror("Time Error", "End time must be after Start time.")
                return

            conflicts = [a for a in self.activities if not (end_dt <= a.start or start_dt >= a.end)]
            if conflicts:
                msg = f"Conflict detected with {len(conflicts)} activities. Add anyway?"
                if not messagebox.askyesno("Conflict", msg): return

            new_act = Activity(vals['ent_name'], vals['ent_type'], start_dt, end_dt)
            self.activities.append(new_act)
            self.update_filter_list()
            self.update_table()
            for ent in self.entries.values(): ent.delete(0, tk.END)

        except ValueError:
            messagebox.showerror("Format Error", f"Please use {DT_FORMAT} format.")

    def update_table(self):
        self.tree.delete(*self.tree.get_children())
        filter_val = self.filter_var.get()

        for act in self.activities:
            if filter_val == "All" or act.act_type == filter_val:
                tag = act.act_type
                if tag not in self.type_colors:
                    self.type_colors[tag] = self.color_palette[len(self.type_colors) % len(self.color_palette)]

                self.tree.tag_configure(tag, background=self.type_colors[tag])
                self.tree.insert("", "end", values=(
                    act.name,
                    act.act_type,
                    act.start.strftime(DT_FORMAT),
                    act.end.strftime(DT_FORMAT)
                ), tags=(tag,))

    def update_filter_list(self):
        types = sorted(list(set(a.act_type for a in self.activities)))
        self.filter_menu['values'] = ["All"] + types

    def sort_by_column(self, col):
        if self.sort_column == col:
            self.sort_clicks += 1
        else:
            self.sort_column, self.sort_clicks = col, 1

        reverse = (self.sort_clicks % 2 == 0)
        sort_map = {"NAME": "name", "TYPE": "act_type", "START": "start", "END": "end"}
        self.activities.sort(key=lambda x: getattr(x, sort_map[col]), reverse=reverse)
        self.update_table()

    def purge_all(self):
        if not self.activities: return
        if messagebox.askyesno("Confirm Purge", "Purge all activities?"):
            self.activities = []
            self.update_filter_list()
            self.filter_var.set("All")
            self.update_table()

    def export_csv(self):
        if not self.activities: return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if path:
            try:
                # Add utf-8 to ensure no character encoding issues on export
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["NAME", "TYPE", "START", "END"])
                    for a in self.activities:
                        writer.writerow([
                            a.name,
                            a.act_type,
                            a.start.strftime(DT_FORMAT),
                            a.end.strftime(DT_FORMAT)
                        ])
                messagebox.showinfo("Success", "Export successful.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {e}")

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path: return
        new_list = []
        try:
            # Using utf-8-sig ensures any hidden BOM bytes (from Excel) are stripped automatically
            with open(path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)

                # Check headers ignoring case
                headers = [str(h).strip().upper() for h in reader.fieldnames]
                if not set(['NAME', 'TYPE', 'START', 'END']).issubset(headers):
                    raise ValueError("Missing Required Columns (NAME, TYPE, START, END)")

                # Re-map Dictionary Keys to strictly upper-case to avoid mis-matches
                for row in reader:
                    upper_row = {k.strip().upper(): v for k, v in row.items()}

                    s = self.flexible_date_parse(upper_row['START'])
                    e = self.flexible_date_parse(upper_row['END'])
                    new_list.append(Activity(upper_row['NAME'], upper_row['TYPE'], s, e))

            if new_list:
                self.activities = new_list
                self.update_filter_list()
                self.filter_var.set("All")
                self.update_table()
                messagebox.showinfo("Success", "Import successful.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import file.\nDetail: {e}")

    def open_free_slot_window(self):
        if not self.activities: return
        win = tk.Toplevel(self.root)
        win.title("Find Free Slots")
        win.geometry("600x650")
        win.configure(bg=BG_CARD)

        tk.Label(win, text="FIND FREE SLOTS", font=("Segoe UI", 18, "bold"), bg=BG_CARD, fg=ACCENT).pack(pady=20)
        p_frame = tk.Frame(win, bg=BG_CARD)
        p_frame.pack(fill="x", padx=40)

        def create_field(parent, label):
            tk.Label(parent, text=label, bg=BG_CARD, fg="white", font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 0))
            e = tk.Entry(parent, bg="#0f172a", fg="white", insertbackground="white", relief="flat",
                         font=("Segoe UI", 11))
            e.pack(fill="x", pady=5)
            return e

        e_win_s = create_field(p_frame, f"Start Window ({DT_FORMAT})")
        e_win_e = create_field(p_frame, f"End Window ({DT_FORMAT})")
        e_len = create_field(p_frame, "Required Length (Minutes)")

        res_box = tk.Text(win, height=10, bg="#0f172a", fg=ACCENT, font=("Consolas", 10), padx=10, pady=10)
        res_box.pack(pady=20, padx=40, fill="both", expand=True)

        def generate():
            try:
                search_s = self.flexible_date_parse(e_win_s.get())
                search_e = self.flexible_date_parse(e_win_e.get())
                min_dur = timedelta(minutes=int(e_len.get()))

                relevant = sorted(
                    [(a.start, a.end) for a in self.activities if a.end > search_s and a.start < search_e])
                free_slots, current_time = [], search_s

                for b_start, b_end in relevant:
                    if b_start > current_time and (b_start - current_time) >= min_dur:
                        free_slots.append((current_time, b_start))
                    current_time = max(current_time, b_end)

                if search_e > current_time and (search_e - current_time) >= min_dur:
                    free_slots.append((current_time, search_e))

                res_box.delete("1.0", tk.END)
                if not free_slots:
                    res_box.insert(tk.END, "No free slots found.")
                else:
                    for s, e in free_slots:
                        res_box.insert(tk.END,
                                       f"SLOT: {s.strftime(DT_FORMAT)} TO {e.strftime(DT_FORMAT)}\n{'-' * 30}\n")
            except ValueError:
                messagebox.showerror("Error", "Check date format and numeric length.")

        tk.Button(win, text="GENERATE SLOTS", command=generate, bg=ACCENT, fg="black",
                  font=("Segoe UI", 11, "bold"), relief="flat", padx=30, pady=10).pack(pady=(0, 20))


if __name__ == "__main__":
    root = tk.Tk()
    app = ActivitySchedulerPro(root)
    root.mainloop()
