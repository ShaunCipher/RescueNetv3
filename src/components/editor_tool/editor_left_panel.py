import customtkinter as ctk

# Assuming EditorExitButton is in the same file or imported
class EditorExitButton(ctk.CTkFrame):
    def __init__(self, parent, exit_command, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.exit_btn = ctk.CTkButton(
            self, 
            text="✕ Return to Dashboard", 
            width=180, # Made slightly wider to fit the panel better
            height=35,
            fg_color="#4a4a4a",
            hover_color="#5a5a5a",
            command=exit_command
        )
        self.exit_btn.pack(padx=5, pady=10)

class EditorLeftPanel(ctk.CTkFrame):
    def __init__(self, master, toggle_cmd, **kwargs):
        super().__init__(master, width=250, corner_radius=0, fg_color="#2b2b2b", **kwargs)
        self.pack_propagate(False)

        # --- RESIZE HANDLE ---
        self.resizer = ctk.CTkFrame(self, width=8, fg_color="transparent", cursor="sb_h_double_arrow")
        self.resizer.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")
        self.resizer.bind("<B1-Motion>", self.do_resize)

        # --- TOGGLE BUTTON ---
        self.close_btn = ctk.CTkButton(
            self, text="<", width=20, height=60,
            fg_color="#3d3d3d", hover_color="#4d4d4d",
            command=toggle_cmd
        )
        self.close_btn.place(relx=1.0, rely=0.5, anchor="e")

        # --- EXIT BUTTON (Bottom Anchored) ---
        # master.master refers back to the NetworkEditor instance
        self.exit_section = EditorExitButton(self, exit_command=master.master.close_editor)
        self.exit_section.pack(side="bottom", fill="x", pady=20)

    def do_resize(self, event):
        new_width = event.x_root - self.winfo_rootx()
        if 40 < new_width < 800:
            self.configure(width=new_width)
            self.master.master.current_width = new_width

    def update_toggle_icon(self, is_open):
        self.close_btn.configure(text="<" if is_open else ">")