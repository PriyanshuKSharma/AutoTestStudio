import customtkinter as ctk
from tkinter import filedialog
import config
from core.bus import bus_manager
from core.dbc import dbc_manager
from core.project import project

BUS_INTERFACES = ["virtual", "socketcan", "pcan", "vector", "kvaser", "usb2can"]


class SettingsPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        # Scroll container to keep layout cohesive
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=24, pady=20)
        self.scroll_container.columnconfigure(0, weight=1)

        # ─── HEADER ───
        header_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Settings",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            anchor="w",
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Configure hardware interface channels, DBC databases, project details, and visual themes",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("gray50", "gray40"),
            anchor="w",
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # ─── PARAMETERS CARD ───
        form_card = ctk.CTkFrame(
            self.scroll_container,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12,
        )
        form_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        form_card.columnconfigure(0, weight=1)

        form_inner = ctk.CTkFrame(form_card, fg_color="transparent")
        form_inner.pack(padx=20, pady=20, fill="both", expand=True)
        form_inner.columnconfigure(0, weight=0, minsize=140)
        form_inner.columnconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(
            form_inner,
            text="CONFIGURATION PARAMETERS",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        divider = ctk.CTkFrame(form_inner, height=1, fg_color=("gray90", "gray28"))
        divider.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        # Project name
        ctk.CTkLabel(
            form_inner,
            text="Project Name:",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        ).grid(row=2, column=0, pady=10, sticky="w")
        self._proj_name = ctk.CTkEntry(
            form_inner, width=280, font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        self._proj_name.insert(0, project.name)
        self._proj_name.grid(row=2, column=1, sticky="w")

        # Bus interface
        ctk.CTkLabel(
            form_inner,
            text="Bus Interface:",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        ).grid(row=3, column=0, pady=10, sticky="w")
        self._iface_var = ctk.StringVar(value=project.bus_interface)
        self._iface_menu = ctk.CTkOptionMenu(
            form_inner,
            values=BUS_INTERFACES,
            variable=self._iface_var,
            width=180,
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self._iface_menu.grid(row=3, column=1, sticky="w")

        # Channel
        ctk.CTkLabel(
            form_inner,
            text="Interface Channel:",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        ).grid(row=4, column=0, pady=10, sticky="w")
        self._channel = ctk.CTkEntry(
            form_inner, width=180, font=ctk.CTkFont(family="Consolas", size=13)
        )
        self._channel.insert(0, project.channel)
        self._channel.grid(row=4, column=1, sticky="w")

        # Bitrate
        ctk.CTkLabel(
            form_inner,
            text="Bitrate (bps):",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        ).grid(row=5, column=0, pady=10, sticky="w")
        self._bitrate_var = ctk.StringVar(value=str(project.bitrate))
        self._bitrate_menu = ctk.CTkOptionMenu(
            form_inner,
            values=["125000", "250000", "500000", "1000000"],
            variable=self._bitrate_var,
            width=140,
            font=ctk.CTkFont(family="Consolas", size=13),
        )
        self._bitrate_menu.grid(row=5, column=1, sticky="w")

        # DBC file
        ctk.CTkLabel(
            form_inner,
            text="DBC Database:",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        ).grid(row=6, column=0, pady=10, sticky="w")

        dbc_row = ctk.CTkFrame(form_inner, fg_color="transparent")
        dbc_row.grid(row=6, column=1, sticky="w")

        self._dbc_label = ctk.CTkLabel(
            dbc_row,
            text=project.dbc_path or "No file loaded",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=("gray50", "gray40"),
            width=240,
            anchor="w",
        )
        self._dbc_label.pack(side="left")

        self.btn_browse = ctk.CTkButton(
            dbc_row,
            text="Browse",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._browse_dbc,
            width=80,
            height=28,
        )
        self.btn_browse.pack(side="left", padx=10)

        # Theme
        ctk.CTkLabel(
            form_inner, text="Theme:", font=ctk.CTkFont(family="Segoe UI", size=13)
        ).grid(row=7, column=0, pady=10, sticky="w")
        self._theme_var = ctk.StringVar(value=config.THEME.capitalize())
        self.theme_btn = ctk.CTkSegmentedButton(
            form_inner,
            values=["Dark", "Light", "System"],
            variable=self._theme_var,
            command=self._apply_theme,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            width=240,
            height=30,
        )
        self.theme_btn.grid(row=7, column=1, sticky="w")

        # Timezone
        ctk.CTkLabel(
            form_inner,
            text="CAN Log Timezone:",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        ).grid(row=8, column=0, pady=10, sticky="w")
        self._tz_var = ctk.StringVar(value=config.TIMEZONE)
        self._tz_menu = ctk.CTkOptionMenu(
            form_inner,
            values=[
                "UTC",
                "Asia/Kolkata",
                "America/New_York",
                "America/Los_Angeles",
                "America/Chicago",
                "Europe/London",
                "Europe/Berlin",
                "Europe/Paris",
                "Asia/Tokyo",
                "Asia/Shanghai",
                "Asia/Dubai",
                "Australia/Sydney",
                "Pacific/Auckland",
            ],
            variable=self._tz_var,
            command=self._apply_timezone,
            width=220,
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self._tz_menu.grid(row=8, column=1, sticky="w")

        # ─── ACTION BUTTONS ───
        btn_card = ctk.CTkFrame(
            self.scroll_container,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12,
        )
        btn_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        btn_inner = ctk.CTkFrame(btn_card, fg_color="transparent")
        btn_inner.pack(padx=20, pady=16, fill="both")

        self.connect_btn = ctk.CTkButton(
            btn_inner,
            text="Connect Bus",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=("#1f538d", "#60a5fa"),
            command=self._connect,
            height=36,
        )
        self.connect_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.disconnect_btn = ctk.CTkButton(
            btn_inner,
            text="Disconnect",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._disconnect,
            height=36,
        )
        self.disconnect_btn.pack(side="left", fill="x", expand=True, padx=6)

        self.save_btn = ctk.CTkButton(
            btn_inner,
            text="Save Project",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._save_project,
            height=36,
        )
        self.save_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

        # Status text row
        self._status = ctk.CTkLabel(
            self.scroll_container,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("gray50", "gray40"),
            anchor="w",
        )
        self._status.grid(row=3, column=0, sticky="w", padx=4, pady=8)

    def _apply_theme(self, value: str):
        mode = value.lower()
        ctk.set_appearance_mode(mode)
        config.THEME = mode

    def _browse_dbc(self):
        path = filedialog.askopenfilename(filetypes=[("DBC", "*.dbc"), ("All", "*.*")])
        if not path:
            return
        try:
            dbc_manager.load(path)
            project.dbc_path = path
            self._dbc_label.configure(text=path, text_color=("black", "white"))
            self._status.configure(
                text=f"[Loaded] DBC database file read successfully: {path}",
                text_color="green",
            )
        except Exception as e:
            self._status.configure(text=f"DBC load error: {e}", text_color="red")

    def _connect(self):
        iface = self._iface_var.get()
        channel = self._channel.get().strip()
        bitrate = int(self._bitrate_var.get())
        try:
            bus_manager.connect(interface=iface, channel=channel, bitrate=bitrate)
            project.bus_interface = iface
            project.channel = channel
            project.bitrate = bitrate
            self._status.configure(
                text=f"[Connected] Bus active on {iface} channel {channel}",
                text_color="green",
            )
        except Exception as e:
            self._status.configure(text=f"Connect failed: {e}", text_color="red")

    def _disconnect(self):
        bus_manager.disconnect()
        self._status.configure(
            text="Disconnected from bus.", text_color=("gray50", "gray40")
        )

    def _save_project(self):
        project.name = self._proj_name.get().strip()
        project.save()
        self._status.configure(
            text="[Saved] Project file settings written to disk.", text_color="green"
        )

    def _apply_timezone(self, value: str):
        config.TIMEZONE = value
        self._status.configure(
            text=f"[Timezone] CAN log timestamps will display as {value}.",
            text_color="green",
        )
