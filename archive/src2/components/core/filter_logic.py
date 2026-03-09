import customtkinter as ctk
from src.components.core.map_utils import get_colors

class FilterLogic:
    def __init__(self, categories, plots, canvas):
        self.categories = categories
        self.plots = plots
        self.canvas = canvas
        # Track visibility: { 'hospital': True, 'firestation': True ... }
        self.visibility_states = {cat.lower(): True for cat in categories}
        self.dropdown_container = None

    def build_dropdown_ui(self, parent_frame):
        """Builds the facility visibility checkboxes inside a collapsible frame."""
        self.dropdown_container = parent_frame
        colors = get_colors()
        
        # Clear existing
        for widget in self.dropdown_container.winfo_children():
            widget.destroy()

        for cat in self.categories:
            cat_lower = cat.lower()
            cat_color = colors.get(cat_lower, "white")
            
            # 1. Row Container
            row = ctk.CTkFrame(self.dropdown_container, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)

            # 2. Checkbox
            cb = ctk.CTkCheckBox(
                row, 
                text="", 
                width=24,
                checkbox_width=18,
                checkbox_height=18,
                command=lambda c=cat_lower: self.toggle_category(c)
            )
            # Set initial state based on visibility_states
            if self.visibility_states.get(cat_lower, True):
                cb.select()
            cb.pack(side="left")

            # 3. Color Swatch (Visual key for the map)
            color_swatch = ctk.CTkFrame(
                row, width=12, height=12, corner_radius=2, fg_color=cat_color
            )
            color_swatch.pack(side="left", padx=(0, 10))

            # 4. Label
            label = ctk.CTkLabel(
                row, text=cat.capitalize(), font=("Arial", 12), text_color="#DCE4EE"
            )
            label.pack(side="left")

    def toggle_category(self, category_name):
        cat = category_name.lower()
        if cat in self.plots:
            current_state = self.plots[cat].get_visible()
            new_state = not current_state
            
            self.plots[cat].set_visible(new_state)
            self.visibility_states[cat] = new_state
            
            self.canvas.draw_idle()
            return new_state
        return False