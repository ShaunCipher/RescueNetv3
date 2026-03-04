import customtkinter as ctk
from src.theme import Theme  # Import our central theme

class TerminalPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        # Use Theme.BG_DARKER for that deep terminal background
        super().__init__(master, corner_radius=0, fg_color=Theme.BG_DARKER, **kwargs)
        
        # Header for the terminal
        self.header = ctk.CTkLabel(
            self, 
            text="ANALYSIS TERMINAL", 
            font=("Arial", 11, "bold"), 
            text_color=Theme.TEXT_DIM  # Muted header text
        )
        self.header.pack(side="top", anchor="w", padx=15, pady=(10, 0))

        # The actual Terminal Textbox
        self.text_area = ctk.CTkTextbox(
            self, 
            fg_color="transparent", 
            text_color=Theme.RESCUE_GREEN, # Our signature Matrix/Rescue green
            font=("Consolas", 12),
            activate_scrollbars=True
        )
        self.text_area.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Initial boot message
        self.log("RescueNet Terminal Initialized...")

    def log(self, message):
        """Standardized method to write to the terminal"""
        self.text_area.insert("end", f"\n> {message}")
        self.text_area.see("end")

    def clear(self):
        """Utility to clear the screen"""
        self.text_area.delete("1.0", "end")