import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class CommandCenter:
    def __init__(self, master_registry, fig, ax):
        self.registry = master_registry
        self.fig = fig
        self.ax = ax
        self.window = None
        self.main_content = None

    def open_dashboard(self):
        if self.window is not None and tk.Toplevel.winfo_exists(self.window):
            self.window.lift()
            return

        self.window = tk.Toplevel()
        self.window.title("RescueNet | Emergency Command Center")
        self.window.geometry("1100x800")
        self.window.configure(bg="#f0f2f5")

        side_panel = tk.Frame(self.window, width=220, bg="#2c3e50")
        side_panel.pack(side="left", fill="y")
        
        self.main_content = tk.Frame(self.window, bg="white", padx=20, pady=20)
        self.main_content.pack(side="right", expand=True, fill="both")

        tk.Label(side_panel, text="COMMAND\nCENTER", fg="white", bg="#2c3e50", 
                 font=("Helvetica", 14, "bold"), pady=30).pack()

        found_categories = sorted(list(set(str(d.get('category')) for d in self.registry.values())))

        for cat in found_categories:
            btn = tk.Button(side_panel, text=cat.upper(), font=("Helvetica", 10, "bold"),
                            bg="#34495e", fg="white", activebackground="#1abc9c",
                            relief="flat", pady=12, cursor="hand2",
                            command=lambda c=cat: self.update_view(c))
            btn.pack(fill="x", padx=15, pady=5)

    def update_view(self, category):
        for widget in self.main_content.winfo_children():
            widget.destroy()

        items = [d for d in self.registry.values() if str(d.get('category')) == category]
        if not items: return

        header_frame = tk.Frame(self.main_content, bg="white")
        header_frame.pack(fill="x", pady=(0, 20))
        tk.Label(header_frame, text=f"{category.upper()} OVERVIEW", 
                 font=("Helvetica", 20, "bold"), bg="white", fg="#2c3e50").pack(side="left")

        # --- PIE CHART ---
        fig, ax = plt.subplots(figsize=(6, 3), dpi=100)
        fig.patch.set_facecolor('white')

        first_item = items[0]
        is_responder = 'staff_present' in first_item

        if is_responder:
            active = sum(int(i.get('staff_present', 0)) for i in items)
            total = sum(int(i.get('number_of_staff', 0)) for i in items)
            ax.pie([active, max(0, total-active)], labels=['Active', 'Offline'], 
                   colors=['#2ecc71', '#95a5a6'], autopct='%1.1f%%', startangle=90)
        else:
            occ = sum(int(i.get('occupants', 0)) for i in items)
            cap = sum(int(i.get('capacity', 0)) for i in items)
            ax.pie([occ, max(0, cap-occ)], labels=['Occupied', 'Empty'], 
                   colors=['#e74c3c', '#3498db'], autopct='%1.1f%%', startangle=90)

        canvas = FigureCanvasTkAgg(fig, master=self.main_content)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10, fill="x")

        # --- DATA TABLE ---
        tree_frame = tk.Frame(self.main_content)
        tree_frame.pack(expand=True, fill="both")

        cols = ("ID", "Name", "Status", "Value")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")

        for item in items:
            val = f"{item.get('staff_present', 0)}/{item.get('number_of_staff', 0)}" if is_responder else f"{item.get('occupants', 0)}/{item.get('capacity', 0)}"
            tree.insert("", "end", values=(item.get('id'), item.get('name'), item.get('status'), val))
        
        tree.pack(side="left", expand=True, fill="both")
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")