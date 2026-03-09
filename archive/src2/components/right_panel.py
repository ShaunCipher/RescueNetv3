import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import pandas as pd
import os

class RightPanel(ctk.CTkFrame):
    def __init__(self, master, toggle_cmd, accident_manager=None, **kwargs):
        super().__init__(master, width=320, corner_radius=0, fg_color="#2b2b2b", **kwargs)

        self.accident_manager = accident_manager
        self.acc_file  = 'data/accidents.csv'
        self.hist_file = 'data/accident_history.csv'

        # Close/open toggle strip
        self.close_btn = ctk.CTkButton(
            self, text="<", width=20, height=60,
            fg_color="#3d3d3d", hover_color="#555555",
            command=toggle_cmd
        )
        self.close_btn.place(relx=0.0, rely=0.5, anchor="w")

        # Main scrollable content area
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=(30, 6), pady=8)

        # Header
        ctk.CTkLabel(
            content, text="INCIDENT SUMMARY",
            font=("Arial", 13, "bold"), text_color="#e74c3c"
        ).pack(pady=(10, 2))

        self.counter_label = ctk.CTkLabel(
            content, text="Active Incidents: 0",
            font=("Arial", 11), text_color="#f0f0f0"
        )
        self.counter_label.pack()

        ctk.CTkFrame(content, height=1, fg_color="#444444").pack(fill="x", pady=8)

        # Active incidents list
        ctk.CTkLabel(
            content, text="Active Incidents",
            font=("Arial", 11, "bold"), text_color="#aaaaaa"
        ).pack(anchor="w")

        self.incident_list = ctk.CTkFrame(content, fg_color="#1e1e1e", corner_radius=6)
        self.incident_list.pack(fill="x", pady=(4, 8))

        ctk.CTkFrame(content, height=1, fg_color="#444444").pack(fill="x", pady=4)

        # Recent history
        ctk.CTkLabel(
            content, text="Recent History",
            font=("Arial", 11, "bold"), text_color="#aaaaaa"
        ).pack(anchor="w")

        self.history_list = ctk.CTkFrame(content, fg_color="#1e1e1e", corner_radius=6)
        self.history_list.pack(fill="x", pady=(4, 8))

        # Action buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=6)

        ctk.CTkButton(
            btn_frame, text="Refresh", width=130, height=30,
            fg_color="#2c3e50", hover_color="#34495e",
            command=self.refresh
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame, text="Open Dispatch", width=130, height=30,
            fg_color="#c0392b", hover_color="#a93226",
            command=self.open_dispatch
        ).pack(side="right", padx=2)

        # Initial data load
        self.refresh()

    SEVERITY_COLORS = {
        "critical": "#e74c3c",
        "moderate": "#e67e22",
        "minor":    "#27ae60",
    }

    def refresh(self):
        self._populate_incidents()
        self._populate_history()

    def open_dispatch(self):
        if self.accident_manager:
            self.accident_manager.open_report_window()
        else:
            import tkinter.messagebox as mb
            mb.showinfo("Info", "Accident Manager is not linked to this panel.")

    def _clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def _populate_incidents(self):
        self._clear_frame(self.incident_list)

        if not os.path.exists(self.acc_file):
            ctk.CTkLabel(
                self.incident_list, text="No active incidents.",
                font=("Arial", 10), text_color="#777777"
            ).pack(pady=10)
            self.counter_label.configure(text="Active Incidents: 0")
            return

        try:
            df = pd.read_csv(self.acc_file)
        except Exception:
            self.counter_label.configure(text="Active Incidents: --")
            return

        count = len(df)
        self.counter_label.configure(
            text=f"Active Incidents: {count}",
            text_color="#e74c3c" if count > 0 else "#f0f0f0"
        )

        if df.empty:
            ctk.CTkLabel(
                self.incident_list, text="No active incidents.",
                font=("Arial", 10), text_color="#777777"
            ).pack(pady=10)
            return

        for _, row in df.iterrows():
            sev   = str(row.get('severity', 'minor')).lower()
            color = self.SEVERITY_COLORS.get(sev, "#aaaaaa")

            card = ctk.CTkFrame(self.incident_list, fg_color="#2a2a2a", corner_radius=6)
            card.pack(fill="x", pady=3, padx=4)

            # Left colour strip
            ctk.CTkFrame(card, width=4, fg_color=color, corner_radius=3).pack(
                side="left", fill="y", padx=(4, 8)
            )

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, pady=6)

            ctk.CTkLabel(
                info,
                text=str(row.get('name', 'Unknown')),
                font=("Arial", 11, "bold"), anchor="w"
            ).pack(anchor="w")

            ctk.CTkLabel(
                info,
                text=(
                    f"{sev.capitalize()}  |  "
                    f"{row.get('num_victims', 0)} victim(s)  |  "
                    f"{row.get('status', 'REPORTED')}"
                ),
                font=("Arial", 9), text_color="#aaaaaa", anchor="w"
            ).pack(anchor="w")

            # Quick dispatch button
            ctk.CTkButton(
                card, text="Dispatch", width=60, height=26,
                fg_color="#2980b9", hover_color="#1f618d",
                font=("Arial", 9),
                command=lambda r=row: self._quick_dispatch(r)
            ).pack(side="right", padx=6)

    def _populate_history(self):
        self._clear_frame(self.history_list)

        if not os.path.exists(self.hist_file):
            ctk.CTkLabel(
                self.history_list, text="No history records.",
                font=("Arial", 10), text_color="#777777"
            ).pack(pady=6)
            return

        try:
            h_df   = pd.read_csv(self.hist_file)
            recent = h_df.sort_values('timestamp', ascending=False).head(5)

            for _, row in recent.iterrows():
                outcome = str(row.get('outcome', '')).upper()
                icon    = "[OK]" if outcome == "COMPLETED" else "[DEL]"

                card = ctk.CTkFrame(self.history_list, fg_color="#252525", corner_radius=4)
                card.pack(fill="x", pady=2, padx=4)

                ctk.CTkLabel(
                    card,
                    text=f"{icon} {row.get('name', 'Unknown')}",
                    font=("Arial", 10, "bold"), anchor="w"
                ).pack(anchor="w", padx=8, pady=(4, 0))

                ctk.CTkLabel(
                    card,
                    text=f"{row.get('severity', '')}  |  {row.get('timestamp', '')}",
                    font=("Arial", 9), text_color="#777777", anchor="w"
                ).pack(anchor="w", padx=8, pady=(0, 4))

        except Exception:
            ctk.CTkLabel(
                self.history_list, text="Error loading history.",
                font=("Arial", 10), text_color="#e74c3c"
            ).pack(pady=6)

    def _quick_dispatch(self, acc_row):
        if not self.accident_manager:
            return
        self.accident_manager.open_report_window()
        try:
            name = str(acc_row.get('name', ''))
            self.after(200, lambda: self._select_incident(name))
        except Exception:
            pass

    def _select_incident(self, name):
        try:
            self.accident_manager.acc_dropdown.set(name)
            self.accident_manager.on_accident_selected(name)
        except Exception:
            pass
