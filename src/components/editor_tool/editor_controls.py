import customtkinter as ctk

class EditorControls(ctk.CTkFrame):
    def __init__(self, parent, toolbar, refresh_cmd, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.toolbar = toolbar
        self.refresh_cmd = refresh_cmd
        self.setup_custom_controls()

    def setup_custom_controls(self):
        btns = [
            ("🔍 Zoom", self.toolbar.zoom),
            ("✋ Pan", self.toolbar.pan),
            ("🏠 Reset", self.toolbar.home),
            ("🔄 Refresh", self.refresh_cmd)
        ]
        
        for text, cmd in btns:
            ctk.CTkButton(
                self, 
                text=text, 
                width=80, 
                height=32,
                fg_color="#333333", 
                hover_color="#444444", 
                command=cmd
            ).pack(side="left", padx=5)