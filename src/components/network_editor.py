import customtkinter as ctk
from tkinter import messagebox
# Import the Conductor from your fragmented tools folder
from .editor_tool.editor_manager import EditorManager

class NetworkEditor(ctk.CTkToplevel):
    def __init__(self, master, workspace=None):
        super().__init__(master)
        self.workspace = workspace
        
        # --- 1. Window Configuration ---
        self.title("RescueNet v3 | Road Network Editor")
        self.after(0, lambda: self.state('zoomed')) 
        
        # Ensure focus and visibility
        self.lift()
        self.attributes("-topmost", True)
        self.after(500, lambda: self.attributes("-topmost", False))
        self.focus_force()
        
        # Intercept the 'X' button to check for unsaved changes
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # --- 2. Layout Distribution ---
        # Column 0: Sidebar (Fixed Width) | Column 1: Map (Expands)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # The Sidebar (Left Panel)
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#2b2b2b")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # The Canvas Viewport (Right Panel)
        self.canvas_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.canvas_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # --- 3. Initialize the Brain ---
        # We initialize the Manager and give it access to this UI and the canvas frame
        self.manager = EditorManager(self, self.workspace, self.canvas_frame)

        # --- 4. Build the UI Components ---
        self.setup_sidebar_content()

    def setup_sidebar_content(self):
        """Organizes the sidebar into Tools, Filters, and Actions."""
        # Header
        ctk.CTkLabel(self.sidebar, text="NETWORK EDITOR", 
                     font=("Arial", 22, "bold"), text_color="#ffffff").pack(pady=25)
        
        # --- TOOLBOX SECTION ---
        ctk.CTkLabel(self.sidebar, text="TOOLS", font=("Arial", 11, "bold"), text_color="gray").pack(anchor="w", padx=20)
        
        self.btn_nodes = ctk.CTkButton(self.sidebar, text="📍 Edit Nodes", 
                                       fg_color="#3d3d3d", hover_color="#4d4d4d")
        self.btn_nodes.pack(fill="x", padx=15, pady=5)
        
        self.btn_roads = ctk.CTkButton(self.sidebar, text="🛣️ Edit Roads", 
                                       fg_color="#3d3d3d", hover_color="#4d4d4d")
        self.btn_roads.pack(fill="x", padx=15, pady=5)

        # --- VISIBILITY SECTION ---
        # The Shell provides the container, the Manager fills it with checkboxes
        ctk.CTkLabel(self.sidebar, text="LAYER VISIBILITY", 
                     font=("Arial", 11, "bold"), text_color="gray").pack(pady=(25, 5), anchor="w", padx=20)
        
        self.filter_container = ctk.CTkScrollableFrame(self.sidebar, height=250, fg_color="#1e1e1e")
        self.filter_container.pack(fill="x", padx=10, pady=5)
        
        self.manager.setup_filter_ui(self.filter_container)

        # --- SYSTEM ACTIONS (Bottom) ---
        # Exit Button (Absolute Bottom)
        self.exit_btn = ctk.CTkButton(
            self.sidebar, text="❌ Exit Editor", 
            fg_color="#3d3d3d", hover_color="#c0392b", 
            command=self.on_close
        )
        self.exit_btn.pack(side="bottom", fill="x", padx=20, pady=(0, 20))

        # Save Button (Above Exit)
        self.save_btn = ctk.CTkButton(
            self.sidebar, text="💾 Save Changes", 
            fg_color="#28a745", hover_color="#218838",
            font=("Arial", 13, "bold"),
            command=self.confirm_save
        )
        self.save_btn.pack(side="bottom", fill="x", padx=20, pady=10)

    def confirm_save(self):
        """Final verification before the Manager touches the CSVs."""
        if messagebox.askyesno("Confirm Save", "Are you sure you want to write changes to disk?\nThis will update your nodes and edges CSV files."):
            self.manager.save_to_disk()

    def on_close(self):
        """Graceful shutdown with a check for unsaved work."""
        if hasattr(self, 'manager') and self.manager.has_unsaved_changes:
            res = messagebox.askyesnocancel("Unsaved Changes", "You have pending changes. Save them before leaving?")
            if res is True: 
                self.manager.save_to_disk()
                self.destroy()
            elif res is False: 
                self.destroy()
        else:
            self.destroy()