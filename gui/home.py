import os
import customtkinter as ctk
from core.project import project
from core.bus import bus_manager


class HomePanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _get_main_window(self):
        curr = self
        while curr:
            if hasattr(curr, "_show_panel"):
                return curr
            curr = getattr(curr, "master", None)
        return None

    def _navigate_to(self, label: str):
        mw = self._get_main_window()
        if mw:
            mw._show_panel(label)

    def _build(self):
        # Create a scrollable container to prevent cropping
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=24, pady=20)
        self.scroll_container.columnconfigure(0, weight=1)

        # ─── HEADER ───
        header_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=0)

        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            title_frame,
            text="AutoTest Studio",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            anchor="w"
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Automotive CAN Diagnostic and Test Automation Platform",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=("gray50", "gray40"),
            anchor="w"
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # System Status Badge (Top Right)
        sys_status_card = ctk.CTkFrame(
            header_frame,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=10
        )
        sys_status_card.grid(row=0, column=1, sticky="e")

        self.sys_dot = ctk.CTkFrame(sys_status_card, width=10, height=10, corner_radius=5, fg_color="#10b981")
        self.sys_dot.pack(side="left", padx=(16, 8), pady=8)
        
        self.sys_text = ctk.CTkLabel(
            sys_status_card,
            text="System: Ready",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#10b981", "#10b981")
        )
        self.sys_text.pack(side="left", padx=(0, 16), pady=8)

        # ─── MAIN CONTENT GRID ───
        grid_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        grid_frame.grid(row=1, column=0, sticky="nsew")
        grid_frame.columnconfigure(0, weight=1, uniform="cols")
        grid_frame.columnconfigure(1, weight=1, uniform="cols")

        # Left Column
        left_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left_col.columnconfigure(0, weight=1)

        # Right Column
        right_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        right_col.columnconfigure(0, weight=1)

        # ─── LEFT COLUMN CARDS ───
        
        # 1. CAN Bus Controller Card
        bus_card = ctk.CTkFrame(
            left_col,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        bus_card.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        bus_card.columnconfigure(0, weight=1)

        bus_inner = ctk.CTkFrame(bus_card, fg_color="transparent")
        bus_inner.pack(padx=20, pady=20, fill="both", expand=True)
        bus_inner.columnconfigure(0, weight=1)

        bus_title = ctk.CTkLabel(
            bus_inner,
            text="CAN BUS CONTROLLER",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        )
        bus_title.grid(row=0, column=0, sticky="w", pady=(0, 4))

        divider1 = ctk.CTkFrame(bus_inner, height=1, fg_color=("gray90", "gray28"))
        divider1.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        # Status row
        status_row = ctk.CTkFrame(bus_inner, fg_color="transparent")
        status_row.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        
        status_lbl = ctk.CTkLabel(
            status_row,
            text="Connection Status: ",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("gray50", "gray40")
        )
        status_lbl.pack(side="left")

        self.bus_status_dot = ctk.CTkFrame(status_row, width=10, height=10, corner_radius=5, fg_color="#ef4444")
        self.bus_status_dot.pack(side="left", padx=(6, 6))

        self.bus_status_text = ctk.CTkLabel(
            status_row,
            text="Disconnected",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#ef4444"
        )
        self.bus_status_text.pack(side="left")

        # Config Info row
        self.bus_info_lbl = ctk.CTkLabel(
            bus_inner,
            text="Interface: virtual  |  Channel: vcan0  |  Bitrate: 500,000 bps",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            anchor="w",
            text_color=("gray40", "gray50")
        )
        self.bus_info_lbl.grid(row=3, column=0, sticky="w", pady=(0, 16))

        # Action Buttons
        btn_row = ctk.CTkFrame(bus_inner, fg_color="transparent")
        btn_row.grid(row=4, column=0, sticky="ew")

        self.connect_btn = ctk.CTkButton(
            btn_row,
            text="Connect Bus",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self._toggle_connection,
            height=36
        )
        self.connect_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.refresh_btn = ctk.CTkButton(
            btn_row,
            text="Sync Status",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._refresh,
            height=36,
            width=100
        )
        self.refresh_btn.pack(side="right", padx=(6, 0))

        # Error display label
        self.bus_err_lbl = ctk.CTkLabel(
            bus_inner,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#f97316",
            anchor="w"
        )
        self.bus_err_lbl.grid(row=5, column=0, sticky="w", pady=(6, 0))
        self.bus_err_lbl.grid_remove()  # hide initially

        # 2. Quick Actions Card
        actions_card = ctk.CTkFrame(
            actions_card_parent := left_col,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        actions_card.grid(row=1, column=0, sticky="ew")
        actions_card.columnconfigure(0, weight=1)

        actions_inner = ctk.CTkFrame(actions_card, fg_color="transparent")
        actions_inner.pack(padx=20, pady=20, fill="both", expand=True)
        actions_inner.columnconfigure(0, weight=1)

        actions_title = ctk.CTkLabel(
            actions_inner,
            text="QUICK SHORTCUTS",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        )
        actions_title.grid(row=0, column=0, sticky="w", pady=(0, 4))

        divider2 = ctk.CTkFrame(actions_inner, height=1, fg_color=("gray90", "gray28"))
        divider2.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        btn_grid = ctk.CTkFrame(actions_inner, fg_color="transparent")
        btn_grid.grid(row=2, column=0, sticky="ew")
        btn_grid.columnconfigure(0, weight=1, uniform="act_btn")
        btn_grid.columnconfigure(1, weight=1, uniform="act_btn")

        # Shortcuts: CAN Monitor, CAN Sender, Test Builder, Test Runner
        actions = [
            ("Monitor CAN Bus", "◎  CAN Monitor", 0, 0, (0, 4), (0, 4)),
            ("Transmit Frames", "▷  CAN Sender", 0, 1, (4, 0), (0, 4)),
            ("Write Test Scripts", "⊞  Test Builder", 1, 0, (0, 4), (4, 0)),
            ("Execute Test Suites", "▶  Test Runner", 1, 1, (4, 0), (4, 0))
        ]

        for text, target_tab, r, c, px, py in actions:
            btn = ctk.CTkButton(
                btn_grid,
                text=text,
                font=ctk.CTkFont(family="Segoe UI", size=13),
                command=lambda tab=target_tab: self._navigate_to(tab),
                fg_color=("gray95", "gray25"),
                hover_color=("gray90", "gray30"),
                text_color=("#1a202c", "#f7fafc"),
                border_width=1,
                border_color=("gray85", "gray28"),
                height=40
            )
            btn.grid(row=r, column=c, padx=px, pady=py, sticky="ew")

        # ─── RIGHT COLUMN CARDS ───

        # 1. Project Overview Card
        proj_card = ctk.CTkFrame(
            right_col,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        proj_card.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        proj_card.columnconfigure(0, weight=1)

        proj_inner = ctk.CTkFrame(proj_card, fg_color="transparent")
        proj_inner.pack(padx=20, pady=20, fill="both", expand=True)
        proj_inner.columnconfigure(0, weight=1)

        proj_title = ctk.CTkLabel(
            proj_inner,
            text="PROJECT PROFILE",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        )
        proj_title.grid(row=0, column=0, sticky="w", pady=(0, 4))

        divider3 = ctk.CTkFrame(proj_inner, height=1, fg_color=("gray90", "gray28"))
        divider3.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        # Project Info
        self.proj_name_lbl = ctk.CTkLabel(
            proj_inner,
            text=f"Active Project: {project.name}",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            anchor="w"
        )
        self.proj_name_lbl.grid(row=2, column=0, sticky="w", pady=(0, 6))

        # DBC Path Info
        dbc_basename = os.path.basename(project.dbc_path) if project.dbc_path else "None loaded"
        self.dbc_lbl = ctk.CTkLabel(
            proj_inner,
            text=f"DBC Database: {dbc_basename}",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            anchor="w",
            text_color=("gray50", "gray40")
        )
        self.dbc_lbl.grid(row=3, column=0, sticky="w", pady=(0, 12))

        # We will build buttons for settings navigation
        self.view_settings_btn = ctk.CTkButton(
            proj_inner,
            text="Configure in Settings",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            command=lambda: self._navigate_to("◧  Settings"),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            height=28
        )
        self.view_settings_btn.grid(row=4, column=0, sticky="w")

        # 2. Interactive Setup Guide Card
        guide_card = ctk.CTkFrame(
            right_col,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        guide_card.grid(row=1, column=0, sticky="ew")
        guide_card.columnconfigure(0, weight=1)

        guide_inner = ctk.CTkFrame(guide_card, fg_color="transparent")
        guide_inner.pack(padx=20, pady=20, fill="both", expand=True)
        guide_inner.columnconfigure(0, weight=1)

        guide_title = ctk.CTkLabel(
            guide_inner,
            text="GUIDED SETUP",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        )
        guide_title.grid(row=0, column=0, sticky="w", pady=(0, 4))

        divider4 = ctk.CTkFrame(guide_inner, height=1, fg_color=("gray90", "gray28"))
        divider4.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        # Create step rows
        steps = [
            ("Step 1: Set Interface and Load DBC", "Configure connections and databases.", "◧  Settings", "Configure"),
            ("Step 2: Start CAN Traffic Monitor", "View real-time messages on the bus.", "◎  CAN Monitor", "Monitor"),
            ("Step 3: Transmit CAN Messages", "Define and send custom payloads.", "▷  CAN Sender", "Transmit"),
            ("Step 4: Script Test Automation", "Build Python scripts to run test runs.", "⊞  Test Builder", "Build"),
            ("Step 5: Execute and Run Suites", "Run automated test files and log outcomes.", "▶  Test Runner", "Execute")
        ]

        for i, (step_title, step_desc, target_tab, btn_text) in enumerate(steps):
            step_row = ctk.CTkFrame(guide_inner, fg_color="transparent")
            step_row.grid(row=i+2, column=0, sticky="ew", pady=6)
            step_row.columnconfigure(0, weight=1)
            step_row.columnconfigure(1, weight=0)

            text_frame = ctk.CTkFrame(step_row, fg_color="transparent")
            text_frame.grid(row=0, column=0, sticky="w")

            s_title = ctk.CTkLabel(
                text_frame,
                text=step_title,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                anchor="w"
            )
            s_title.pack(anchor="w")

            s_desc = ctk.CTkLabel(
                text_frame,
                text=step_desc,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=("gray50", "gray40"),
                anchor="w"
            )
            s_desc.pack(anchor="w")

            s_btn = ctk.CTkButton(
                step_row,
                text=btn_text,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                command=lambda tab=target_tab: self._navigate_to(tab),
                width=80,
                height=26,
                fg_color=("gray95", "gray25"),
                hover_color=("gray90", "gray30"),
                border_width=1,
                border_color=("gray85", "gray28"),
                text_color=("#1f538d", "#60a5fa")
            )
            s_btn.grid(row=0, column=1, sticky="e", padx=(10, 0))

        # Initial refresh to show correct status
        self._refresh()

    def _toggle_connection(self):
        if bus_manager.connected:
            bus_manager.disconnect()
            self.bus_err_lbl.grid_remove()
            self._refresh()
        else:
            try:
                bus_manager.connect(
                    interface=project.bus_interface,
                    channel=project.channel,
                    bitrate=project.bitrate
                )
                self.bus_err_lbl.grid_remove()
                self._refresh()
            except Exception as e:
                self.bus_err_lbl.configure(text=f"Connection Error: {e}")
                self.bus_err_lbl.grid()
                self._refresh()

    def _refresh(self):
        connected = bus_manager.connected
        
        # Update connection badge & button
        if connected:
            self.bus_status_dot.configure(fg_color="#10b981")
            self.bus_status_text.configure(text="Connected", text_color="#10b981")
            self.connect_btn.configure(
                text="Disconnect Bus",
                fg_color="#dc2626",
                hover_color="#ef4444"
            )
        else:
            self.bus_status_dot.configure(fg_color="#ef4444")
            self.bus_status_text.configure(text="Disconnected", text_color="#ef4444")
            self.connect_btn.configure(
                text="Connect Bus",
                fg_color=("#1f538d", "#1f538d"),
                hover_color=("#14375e", "#14375e")
            )

        # Update configuration text
        rate_str = f"{project.bitrate:,}"
        self.bus_info_lbl.configure(
            text=f"Interface: {project.bus_interface}  |  Channel: {project.channel}  |  Bitrate: {rate_str} bps"
        )

        # Update project profile labels
        self.proj_name_lbl.configure(text=f"Active Project: {project.name}")
        dbc_name = os.path.basename(project.dbc_path) if project.dbc_path else "None loaded"
        self.dbc_lbl.configure(text=f"DBC Database: {dbc_name}")
