import customtkinter as ctk
from src.components.core.map_utils import get_category_order, get_colors

class LeftPanel(ctk.CTkFrame):
    def __init__(self, master, toggle_cmd, workspace=None, **kwargs):
        super().__init__(master, width=250, corner_radius=0, fg_color="#2b2b2b", **kwargs)
        self.workspace = workspace
        
        # Close button
        self.close_btn = ctk.CTkButton(
            self, text="<", width=20, height=60, 
            fg_color="#3d3d3d", command=toggle_cmd
        )
        self.close_btn.place(relx=1.0, rely=0.5, anchor="e")
        
        # --- FACILITY FILTER SECTION ---
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.filter_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            self.filter_frame, 
            text="FACILITIES", 
            font=("Arial", 11, "bold"), 
            text_color="gray"
        ).pack(anchor="w", padx=10, pady=(0, 5))

        self.checkboxes = {}

    def setup_filters(self):
        """Creates checkboxes with permanent color indicators"""
        # Clear frame to prevent doubling
        for widget in self.filter_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                widget.destroy()

        categories = get_category_order()
        colors = get_colors()

        for cat in categories:
            cat_lower = cat.lower()
            cat_color = colors.get(cat_lower, "white")
            
            # 1. Create a row container
            row = ctk.CTkFrame(self.filter_frame, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=2)

            # 2. The Checkbox (Now with no text, just the box)
            cb = ctk.CTkCheckBox(
                row, 
                text="", # Text removed from checkbox to handle it manually
                width=24,
                checkbox_width=18,
                checkbox_height=18,
                command=lambda c=cat_lower: self.on_filter_change(c)
            )
            cb.select() 
            cb.pack(side="left")
            self.checkboxes[cat_lower] = cb

            # 3. The Color Indicator (Small Square)
            color_swatch = ctk.CTkFrame(
                row, 
                width=12, 
                height=12, 
                corner_radius=2,
                fg_color=cat_color
            )
            color_swatch.pack(side="left", padx=(0, 10))
            # Prevent the frame from collapsing
            color_swatch.pack_propagate(False)

            # 4. The Label (Clickable so it feels like part of the checkbox)
            label = ctk.CTkLabel(
                row, 
                text=cat, 
                font=("Arial", 12),
                text_color="#DCE4EE"
            )
            label.pack(side="left")

    def on_filter_change(self, category_key):
        if hasattr(self.workspace, 'filter_engine'):
            self.workspace.filter_engine.toggle_category(category_key)