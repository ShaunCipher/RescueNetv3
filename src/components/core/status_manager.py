import customtkinter as ctk

class StatusManager:
    def __init__(self, fig, ax, master_registry):
        self.fig = fig
        self.ax = ax
        self.registry = master_registry
        self.status_labels = [] 
        self.vars = {} 
        self.dropdown_container = None
        
        # Maps the 'category' found in your CSV to the checkbox keys
        self.category_map = {
            "church": "churches",
            "drrm": "drrm",
            "firestation": "firestations",
            "hospital": "hospitals",
            "policestation": "policestations",
            "school": "schools"
        }

    def build_dropdown_ui(self, parent, categories):
        """Builds the actual checkbox widgets inside the left panel frame."""
        self.dropdown_container = parent
        
        for widget in self.dropdown_container.winfo_children():
            widget.destroy()

        if not categories:
            lbl = ctk.CTkLabel(self.dropdown_container, text="No Categories Found", font=("Arial", 10, "italic"))
            lbl.pack(pady=5)
            return

        for cat in categories:
            cat_key = cat.lower()
            if cat_key not in self.vars:
                self.vars[cat_key] = ctk.BooleanVar(value=False)
            
            cb = ctk.CTkCheckBox(
                self.dropdown_container, 
                text=cat.capitalize(), 
                variable=self.vars[cat_key],
                command=self.update_map,
                font=("Arial", 11),
                checkbox_width=18, 
                checkbox_height=18
            )
            cb.pack(anchor="w", padx=15, pady=3)

        clear_btn = ctk.CTkButton(
            self.dropdown_container, text="Clear Labels", 
            fg_color="#a93226", hover_color="#7b241c",
            height=22, font=("Arial", 10),
            command=self.clear_all
        )
        clear_btn.pack(fill="x", padx=10, pady=10)

    def clear_all(self):
        for var in self.vars.values():
            var.set(False)
        self.update_map()

    def update_map(self):
        # 1. Remove old labels from the map
        for lbl in self.status_labels:
            try: lbl.remove()
            except: pass
        self.status_labels.clear()

        # 2. Iterate through the master registry
        for item in self.registry.values():
            # Get category from CSV (e.g., "Church") and normalize it
            raw_cat = str(item.get('category', '')).lower().strip()
            
            # Translate "church" -> "churches" to match self.vars
            lookup_key = self.category_map.get(raw_cat, raw_cat)
            
            # 3. Check if this category is currently toggled ON in the UI
            if lookup_key in self.vars and self.vars[lookup_key].get():
                raw_status = str(item.get('status', 'Available'))
                display_text = f"Status: {raw_status}"
                
                # Dynamic Coloring based on your status values
                if raw_status == "Available":
                    box_color = '#2ecc71' # Green
                elif raw_status in ["Full", "Closed"]:
                    box_color = '#e74c3c' # Red
                else:
                    box_color = '#3498db' # Blue

                # 4. Add text label to the Matplotlib axis
                txt = self.ax.text(
                    item['x'] + 8, item['y'] - 8, display_text, 
                    fontsize=8, fontweight='bold', color='white',
                    bbox=dict(facecolor=box_color, alpha=0.8, edgecolor='white', boxstyle='round,pad=0.2'),
                    zorder=25 # High z-order to stay on top
                )
                self.status_labels.append(txt)

        # 5. Refresh the canvas
        self.fig.canvas.draw()