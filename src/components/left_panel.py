import customtkinter as ctk

class LeftPanel(ctk.CTkFrame):
    def __init__(self, master, toggle_cmd, **kwargs):
        super().__init__(master, width=250, corner_radius=0, fg_color="#2b2b2b", **kwargs)
        
        # Close button inside the panel (on the right edge)
        self.close_btn = ctk.CTkButton(
            self, text="<", width=20, height=60, 
            fg_color="#3d3d3d", command=toggle_cmd
        )
        self.close_btn.place(relx=1.0, rely=0.5, anchor="e")
        
        # Header for the panel
        self.label = ctk.CTkLabel(self, text="FILE EXPLORER", font=("Arial", 12, "bold"))
        self.label.pack(pady=20, padx=20)
        
        # This is where we will eventually put the data file list