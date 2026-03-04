class FilterLogic:
    def __init__(self, categories, plots, canvas):
        self.categories = categories
        self.plots = plots
        self.canvas = canvas
        # Track visibility: { 'hospital': True, 'firestation': True ... }
        self.visibility_states = {cat.lower(): True for cat in categories}

    def toggle_category(self, category_name):
        cat = category_name.lower()
        if cat in self.plots:
            # Flip the visibility of the Matplotlib scatter object
            current_state = self.plots[cat].get_visible()
            new_state = not current_state
            
            self.plots[cat].set_visible(new_state)
            self.visibility_states[cat] = new_state
            
            # Refresh the map
            self.canvas.draw()
            return new_state
        return False