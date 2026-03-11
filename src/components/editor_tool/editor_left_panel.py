import customtkinter as ctk
from .edit_facilities import EditFacilities

class EditorExitButton(ctk.CTkFrame):
    def __init__(self, parent, exit_command, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.exit_btn = ctk.CTkButton(
            self, 
            text="✕ Return to Dashboard", 
            width=180,
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
        self.exit_section = EditorExitButton(self, exit_command=master.master.close_editor)
        self.exit_section.pack(side="bottom", fill="x", pady=20)

        # --- EDIT FACILITIES DROPDOWN SECTION ---
        self.is_edit_open = False  # Default to closed
        
        self.edit_menu_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.edit_menu_frame.pack(fill="x", padx=10, pady=(20, 5))

        self.edit_toggle_btn = ctk.CTkButton(
            self.edit_menu_frame, 
            text="▶ Edit Facilities",
            height=35, 
            fg_color="#3d3d3d", 
            hover_color="#4d4d4d",
            anchor="w", 
            command=self.toggle_edit_menu
        )
        self.edit_toggle_btn.pack(fill="x")

        # The actual content container from edit_facilities.py
        self.edit_content = ctk.CTkFrame(self.edit_menu_frame, fg_color="#333333")
        # Initialize the logic inside the container
        self.facility_logic = EditFacilities(
            self.edit_content, 
            map_handler=master.master.editor_workspace.map_handler
        )
        self.facility_logic.pack(fill="x", padx=5, pady=5)

    def toggle_edit_menu(self):
        """Toggles the visibility of the Edit Facilities content."""
        if self.is_edit_open:
            self.edit_content.pack_forget()
            self.edit_toggle_btn.configure(text="▶ Edit Facilities")
        else:
            self.edit_content.pack(fill="x", pady=(2, 0))
            self.edit_toggle_btn.configure(text="▼ Edit Facilities")
        
        self.is_edit_open = not self.is_edit_open

    def do_resize(self, event):
        new_width = event.x_root - self.winfo_rootx()
        if 40 < new_width < 800:
            self.configure(width=new_width)
            self.master.master.current_width = new_width

    def update_toggle_icon(self, is_open):
        self.close_btn.configure(text="<" if is_open else ">")