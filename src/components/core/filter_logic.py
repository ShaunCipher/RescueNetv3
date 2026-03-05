import customtkinter as ctk
from src.components.core.map_utils import get_category_order, get_colors

class FilterLogic:
    def __init__(self, categories, plots, canvas):
        self.categories = categories
        self.plots = plots
        self.canvas = canvas
        # Track visibility: { 'hospital': True, 'firestation': True ... }
        self.visibility_states = {cat.lower(): True for cat in categories}

    def build_filter_ui(self, container_frame):
        """
        Builds the actual checkbox rows inside the LeftPanel's frame.
        Keeps the UI generation out of the main panel code.
        """
        colors = get_colors()
        
        for cat in self.categories:
            cat_lower = cat.lower()
            cat_color = colors.get(cat_lower, "white")
            
            # 1. Create a row container
            row = ctk.CTkFrame(container_frame, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=2)

            # 2. The Checkbox
            cb = ctk.CTkCheckBox(
                row, 
                text="", 
                width=24,
                checkbox_width=18,
                checkbox_height=18,
                command=lambda c=cat_lower: self.toggle_category(c)
            )
            cb.select() 
            cb.pack(side="left")

            # 3. The Color Swatch
            color_swatch = ctk.CTkFrame(
                row, width=12, height=12, corner_radius=2, fg_color=cat_color
            )
            color_swatch.pack(side="left", padx=(0, 10))

            # 4. The Label
            label = ctk.CTkLabel(
                row, text=cat, font=("Arial", 12), text_color="#DCE4EE"
            )
            label.pack(side="left")

    def toggle_category(self, category_name):
        cat = category_name.lower()
        if cat in self.plots:
            # Flip the visibility of the Matplotlib scatter object
            current_state = self.plots[cat].get_visible()
            new_state = not current_state
            
            self.plots[cat].set_visible(new_state)
            self.visibility_states[cat] = new_state
            
            # Refresh the map
            self.canvas.draw_idle()
            return new_state
        return False