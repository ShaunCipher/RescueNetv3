import customtkinter as ctk
from src.theme import Theme  # Import our central theme
import tkinter as tk
from tkinter import filedialog

class TerminalPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        # Use Theme.BG_DARKER for that deep terminal background
        super().__init__(master, corner_radius=0, fg_color=Theme.BG_DARKER, **kwargs)
        
        # Header frame for terminal
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.header_frame.pack(side="top", fill="x", padx=10, pady=(10, 0))
        
        # Header label on the left
        self.header = ctk.CTkLabel(
            self.header_frame, 
            text="ANALYSIS TERMINAL", 
            font=("Arial", 11, "bold"), 
            text_color=Theme.TEXT_DIM  # Muted header text
        )
        self.header.pack(side="left", padx=(5, 0))
        
        # PDF export button on the right
        self.pdf_button = ctk.CTkButton(
            self.header_frame,
            text="📄 PDF",
            width=60,
            height=25,
            font=("Arial", 10),
            fg_color=Theme.RESCUE_GREEN,
            text_color="black",
            command=self.export_to_pdf
        )
        self.pdf_button.pack(side="right", padx=(0, 5))
        
        # The actual Terminal Textbox
        self.text_area = ctk.CTkTextbox(
            self, 
            fg_color="transparent", 
            text_color=Theme.RESCUE_GREEN, # Our signature Matrix/Rescue green
            font=("Consolas", 12),
            activate_scrollbars=True
        )
        self.text_area.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.logger = None  # Will be set later
        
        # Initial boot message
        self.log("RescueNet Terminal Initialized...")

    def set_logger(self, logger):
        """Set the logger instance for PDF export."""
        self.logger = logger

    def export_to_pdf(self):
        """Export terminal history to PDF."""
        if self.logger:
            try:
                # Create a hidden root for filedialog
                root = tk.Tk()
                root.withdraw()
                filename = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                    title="Save Terminal History as PDF"
                )
                root.destroy()
                if filename:
                    self.logger.export_history_to_pdf(filename)
                    self.log(f"Terminal history exported to {filename}")
                else:
                    self.log("PDF export cancelled")
            except Exception as e:
                self.log(f"Failed to export PDF: {e}")
        else:
            self.log("Logger not set, cannot export PDF")

    def log(self, message):
        """Standardized method to write to the terminal"""
        self.text_area.insert("end", f"\n> {message}")
        self.text_area.see("end")

    def clear(self):
        """Utility to clear the screen"""
        self.text_area.delete("1.0", "end")