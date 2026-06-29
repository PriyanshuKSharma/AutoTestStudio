import customtkinter as ctk
from tkinter import filedialog
from core.bus import bus_manager
from core.dbc import dbc_manager
from core.project import project

BUS_INTERFACES = ["virtual", "socketcan", "pcan", "vector", "kvaser", "usb2can"]


class SettingsPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))

        form = ctk.CTkFrame(self)
        form.pack(padx=16, pady=8, fill="x")

        # Project name
        ctk.CTkLabel(form, text="Project Name").grid(row=0, column=0, padx=12, pady=10, sticky="w")
        self._proj_name = ctk.CTkEntry(form, width=260)
        self._proj_name.insert(0, project.name)
        self._proj_name.grid(row=0, column=1, padx=8)

        # Bus interface
        ctk.CTkLabel(form, text="Bus Interface").grid(row=1, column=0, padx=12, pady=10, sticky="w")
        self._iface_var = ctk.StringVar(value=project.bus_interface)
        ctk.CTkOptionMenu(form, values=BUS_INTERFACES, variable=self._iface_var, width=180).grid(row=1, column=1, padx=8, sticky="w")

        # Channel
        ctk.CTkLabel(form, text="Channel").grid(row=2, column=0, padx=12, pady=10, sticky="w")
        self._channel = ctk.CTkEntry(form, width=180)
        self._channel.insert(0, project.channel)
        self._channel.grid(row=2, column=1, padx=8, sticky="w")

        # Bitrate
        ctk.CTkLabel(form, text="Bitrate").grid(row=3, column=0, padx=12, pady=10, sticky="w")
        self._bitrate_var = ctk.StringVar(value=str(project.bitrate))
        ctk.CTkOptionMenu(form, values=["125000", "250000", "500000", "1000000"],
                          variable=self._bitrate_var, width=140).grid(row=3, column=1, padx=8, sticky="w")

        # DBC file
        ctk.CTkLabel(form, text="DBC File").grid(row=4, column=0, padx=12, pady=10, sticky="w")
        dbc_row = ctk.CTkFrame(form, fg_color="transparent")
        dbc_row.grid(row=4, column=1, padx=8, sticky="w")
        self._dbc_label = ctk.CTkLabel(dbc_row, text=project.dbc_path or "Not loaded", text_color="gray", width=220, anchor="w")
        self._dbc_label.pack(side="left")
        ctk.CTkButton(dbc_row, text="Browse", width=80, command=self._browse_dbc).pack(side="left", padx=4)

        # Buttons
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(padx=16, pady=12, anchor="w")
        ctk.CTkButton(btn_row, text="Connect Bus", fg_color="green", command=self._connect).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Disconnect", command=self._disconnect).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Save Project", command=self._save_project).pack(side="left", padx=16)

        self._status = ctk.CTkLabel(self, text="", text_color="gray")
        self._status.pack(padx=16)

    def _browse_dbc(self):
        path = filedialog.askopenfilename(filetypes=[("DBC", "*.dbc"), ("All", "*.*")])
        if not path:
            return
        try:
            dbc_manager.load(path)
            project.dbc_path = path
            self._dbc_label.configure(text=path, text_color="white")
            self._status.configure(text=f"DBC loaded: {path}", text_color="green")
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
            self._status.configure(text=f"Connected: {iface} / {channel}", text_color="green")
        except Exception as e:
            self._status.configure(text=f"Connect failed: {e}", text_color="red")

    def _disconnect(self):
        bus_manager.disconnect()
        self._status.configure(text="Disconnected", text_color="gray")

    def _save_project(self):
        project.name = self._proj_name.get().strip()
        project.save()
        self._status.configure(text="Project saved.", text_color="green")
