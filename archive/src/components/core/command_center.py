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
        # Prevent multiple windows from opening
        if self.window is not None and tk.Toplevel.winfo_exists(self.window):
            self.window.lift()
            self.window.focus_force()
            return

        self.window = tk.Toplevel()
        self.window.title("RescueNet | Emergency Command Center")
        
        # --- FULLSCREEN / MAXIMIZE LOGIC ---
        # This maximizes the window while keeping the taskbar visible
        try:
            self.window.state('zoomed')
        except tk.TclError:
            # Fallback for systems that don't support 'zoomed'
            self.window.geometry("1100x800")
            
        self.window.configure(bg="#f0f2f5")
        
        # Ensure the window comes to the front
        self.window.lift()
        self.window.focus_force()

        # --- SIDE NAVIGATION ---
        side_panel = tk.Frame(self.window, width=220, bg="#2c3e50")
        side_panel.pack(side="left", fill="y")
        
        self.main_content = tk.Frame(self.window, bg="white", padx=20, pady=20)
        self.main_content.pack(side="right", expand=True, fill="both")

        tk.Label(side_panel, text="COMMAND\nCENTER", fg="white", bg="#2c3e50", 
                 font=("Helvetica", 14, "bold"), pady=30).pack()

        # --- CATEGORY FILTERING ---
        valid_cats = []
        for d in self.registry.values():
            cat = d.get('category')
            if cat and str(cat).lower() not in ['none', 'road', 'nan']:
                valid_cats.append(str(cat))
        
        found_categories = sorted(list(set(valid_cats)))

        # Create buttons for each valid facility category
        for cat in found_categories:
            btn = tk.Button(
                side_panel, 
                text=cat.upper(), 
                font=("Helvetica", 10, "bold"),
                bg="#34495e", 
                fg="white", 
                activebackground="#1abc9c",
                relief="flat", 
                pady=12, 
                cursor="hand2",
                command=lambda c=cat: self.update_view(c)
            )
            btn.pack(fill="x", padx=15, pady=5)

        # Show the first category by default if available
        if found_categories:
            self.update_view(found_categories[0])

    def update_view(self, category):
        """Refreshes the dashboard content with charts and tables."""
        # 1. Clear current view
        for widget in self.main_content.winfo_children():
            widget.destroy()

        # 2. Filter registry for selected category
        items = [d for d in self.registry.values() if str(d.get('category')) == category]
        if not items:
            return

        # 3. Header
        header_frame = tk.Frame(self.main_content, bg="white")
        header_frame.pack(fill="x", pady=(0, 20))
        tk.Label(header_frame, text=f"{category.upper()} OVERVIEW", 
                 font=("Helvetica", 24, "bold"), bg="white", fg="#2c3e50").pack(side="left")

        # 4. Logic to determine chart type
        first_item = items[0]
        is_responder = 'staff_present' in first_item
        is_facility = 'occupants' in first_item

        # --- PIE CHART SECTION ---
        chart_frame = tk.Frame(self.main_content, bg="white")
        chart_frame.pack(fill="x", pady=10)

        # Increased figsize slightly for the larger screen
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        fig.patch.set_facecolor('white')

        try:
            if is_responder:
                active = sum(int(i.get('staff_present', 0)) for i in items)
                total = sum(int(i.get('number_of_staff', 0)) for i in items)
                if total > 0:
                    ax.pie([active, max(0, total-active)], labels=['Active', 'Offline'], 
                            colors=['#2ecc71', '#95a5a6'], autopct='%1.1f%%', startangle=90)
                else:
                    ax.text(0.5, 0.5, "No Staff Data", ha='center')
            elif is_facility:
                occ = sum(int(i.get('occupants', 0)) for i in items)
                cap = sum(int(i.get('capacity', 0)) for i in items)
                if cap > 0:
                    ax.pie([occ, max(0, cap-occ)], labels=['Occupied', 'Empty'], 
                            colors=['#e74c3c', '#3498db'], autopct='%1.1f%%', startangle=90)
                else:
                    ax.text(0.5, 0.5, "No Capacity Data", ha='center')
            else:
                ax.text(0.5, 0.5, "General Statistics", ha='center')
                ax.axis('off')

            ax.set_title(f"Cumulative {category.capitalize()} Availability", fontsize=12)
        except (ValueError, TypeError):
            ax.text(0.5, 0.5, "Data Formatting Error", ha='center')

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

        # --- DATA TABLE SECTION ---
        tree_frame = tk.Frame(self.main_content)
        tree_frame.pack(expand=True, fill="both", pady=10)

        cols = ("ID", "Name", "Status", "Load/Staffing")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        
        # Style the table for better visibility on a large screen
        style = ttk.Style()
        style.configure("Treeview", rowheight=30, font=("Helvetica", 11))
        style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")

        for item in items:
            if is_responder:
                val = f"{item.get('staff_present', 0)} / {item.get('number_of_staff', 0)} Staff"
            elif is_facility:
                val = f"{item.get('occupants', 0)} / {item.get('capacity', 0)} Capacity"
            else:
                val = "N/A"

            tree.insert("", "end", values=(
                item.get('id', 'N/A'), 
                item.get('name', 'Unknown'), 
                item.get('status', 'Unknown'), 
                val
            ))
        
        tree.pack(side="left", expand=True, fill="both")
        
        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")