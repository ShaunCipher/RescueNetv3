import customtkinter as ctk

class EditorExitButton(ctk.CTkFrame):
    def __init__(self, parent, exit_command, **kwargs):
        # We inherit from CTkFrame so we can style the background if needed
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.exit_btn = ctk.CTkButton(
            self, 
            text="✕ Return to Dashboard", 
            width=150,
            height=35,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a",
            command=exit_command
        )
        self.exit_btn.pack(padx=5, pady=5)