import os
import json
import customtkinter as ctk
import can
from core.bus import bus_manager
from core.dbc import dbc_manager

class SenderPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._cyclic_running = False
        self._cyclic_after = None
        self._build()

    def _build(self):
        # Scroll container to keep layout cohesive
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_container.pack(fill="both", expand=True, padx=24, pady=20)
        self.scroll_container.columnconfigure(0, weight=1)

        # ─── HEADER ───
        header_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=0)

        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            title_frame,
            text="CAN Sender",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            anchor="w"
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Transmit custom raw CAN frames or encode signals via DBC",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("gray50", "gray40"),
            anchor="w"
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # Status Badge (Top Right)
        status_card = ctk.CTkFrame(
            header_frame,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=10
        )
        status_card.grid(row=0, column=1, sticky="e")

        self.snd_dot = ctk.CTkFrame(status_card, width=10, height=10, corner_radius=5, fg_color="gray")
        self.snd_dot.pack(side="left", padx=(16, 8), pady=8)
        
        self.snd_text = ctk.CTkLabel(
            status_card,
            text="Cyclic: Inactive",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("gray50", "gray40")
        )
        self.snd_text.pack(side="left", padx=(0, 16), pady=8)

        # ─── TWO-COLUMN / GRID LAYOUT ───
        grid_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        grid_frame.grid(row=1, column=0, sticky="nsew")
        grid_frame.columnconfigure(0, weight=1, uniform="cols")
        grid_frame.columnconfigure(1, weight=1, uniform="cols")

        # Left Column: Raw CAN Sender Card
        left_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left_col.columnconfigure(0, weight=1)

        # Right Column: DBC Signal Encoder Card
        right_col = ctk.CTkFrame(grid_frame, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        right_col.columnconfigure(0, weight=1)

        # ─── LEFT COLUMN: RAW CAN SENDER ───
        raw_card = ctk.CTkFrame(
            left_col,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        raw_card.grid(row=0, column=0, sticky="ew")
        raw_card.columnconfigure(0, weight=1)

        raw_inner = ctk.CTkFrame(raw_card, fg_color="transparent")
        raw_inner.pack(padx=20, pady=20, fill="both", expand=True)

        raw_title = ctk.CTkLabel(
            raw_inner,
            text="RAW FRAME TRANSMITTER",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        )
        raw_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        divider1 = ctk.CTkFrame(raw_inner, height=1, fg_color=("gray90", "gray28"))
        divider1.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        # CAN ID Row
        ctk.CTkLabel(raw_inner, text="CAN ID (hex):", font=ctk.CTkFont(family="Segoe UI", size=13)).grid(row=2, column=0, padx=(0, 12), pady=8, sticky="w")
        
        id_input_frame = ctk.CTkFrame(raw_inner, fg_color="transparent")
        id_input_frame.grid(row=2, column=1, sticky="ew", pady=8)
        
        self._id_entry = ctk.CTkEntry(id_input_frame, placeholder_text="0x180", font=ctk.CTkFont(family="Consolas", size=13), width=100)
        self._id_entry.pack(side="left")

        self._ext_var = ctk.BooleanVar(value=False)
        self.ext_chk = ctk.CTkCheckBox(id_input_frame, text="Extended ID", font=ctk.CTkFont(family="Segoe UI", size=12), variable=self._ext_var)
        self.ext_chk.pack(side="left", padx=12)

        # DLC Row
        ctk.CTkLabel(raw_inner, text="DLC:", font=ctk.CTkFont(family="Segoe UI", size=13)).grid(row=3, column=0, padx=(0, 12), pady=8, sticky="w")
        self._dlc_var = ctk.StringVar(value="8")
        self.dlc_menu = ctk.CTkOptionMenu(
            raw_inner,
            values=[str(i) for i in range(9)],
            variable=self._dlc_var,
            width=80,
            font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        self.dlc_menu.grid(row=3, column=1, sticky="w", pady=8)

        # Data Hex Row
        ctk.CTkLabel(raw_inner, text="Data (hex bytes):", font=ctk.CTkFont(family="Segoe UI", size=13)).grid(row=4, column=0, padx=(0, 12), pady=8, sticky="w")
        self._data_entry = ctk.CTkEntry(
            raw_inner,
            placeholder_text="80 31 90 45 12 00 00 00",
            font=ctk.CTkFont(family="Consolas", size=13)
        )
        self._data_entry.grid(row=4, column=1, sticky="ew", pady=8)

        # Cyclic Interval Row
        ctk.CTkLabel(raw_inner, text="Interval (ms, 0=once):", font=ctk.CTkFont(family="Segoe UI", size=13)).grid(row=5, column=0, padx=(0, 12), pady=8, sticky="w")
        self._cyclic_entry = ctk.CTkEntry(
            raw_inner,
            placeholder_text="0",
            font=ctk.CTkFont(family="Consolas", size=13),
            width=80
        )
        self._cyclic_entry.grid(row=5, column=1, sticky="w", pady=8)

        raw_inner.columnconfigure(1, weight=1)

        # Buttons
        btn_row = ctk.CTkFrame(raw_inner, fg_color="transparent")
        btn_row.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(16, 0))

        self.send_once_btn = ctk.CTkButton(
            btn_row,
            text="Send Once",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._send_once,
            height=34
        )
        self.send_once_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self._cyclic_btn = ctk.CTkButton(
            btn_row,
            text="Start Cyclic",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self._toggle_cyclic,
            height=34
        )
        self._cyclic_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))

        # ─── RIGHT COLUMN: DBC SIGNAL ENCODER ───
        dbc_card = ctk.CTkFrame(
            right_col,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        dbc_card.grid(row=0, column=0, sticky="ew")
        dbc_card.columnconfigure(0, weight=1)

        dbc_inner = ctk.CTkFrame(dbc_card, fg_color="transparent")
        dbc_inner.pack(padx=20, pady=20, fill="both", expand=True)

        dbc_title = ctk.CTkLabel(
            dbc_inner,
            text="DBC SIGNAL ENCODER",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        )
        dbc_title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        divider2 = ctk.CTkFrame(dbc_inner, height=1, fg_color=("gray90", "gray28"))
        divider2.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        # Message Name Row
        ctk.CTkLabel(dbc_inner, text="Message Name:", font=ctk.CTkFont(family="Segoe UI", size=13)).grid(row=2, column=0, padx=(0, 12), pady=8, sticky="w")
        self._msg_name_entry = ctk.CTkEntry(
            dbc_inner,
            placeholder_text="BMS_Status",
            font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        self._msg_name_entry.grid(row=2, column=1, sticky="ew", pady=8)

        # Signals JSON Row
        ctk.CTkLabel(dbc_inner, text="Signals JSON:", font=ctk.CTkFont(family="Segoe UI", size=13)).grid(row=3, column=0, padx=(0, 12), pady=8, sticky="w")
        self._signals_entry = ctk.CTkEntry(
            dbc_inner,
            placeholder_text='{"SOC": 80, "BMS_State": 3}',
            font=ctk.CTkFont(family="Consolas", size=13)
        )
        self._signals_entry.grid(row=3, column=1, sticky="ew", pady=8)

        dbc_inner.columnconfigure(1, weight=1)

        # Action Button
        self.encode_btn = ctk.CTkButton(
            dbc_inner,
            text="Encode and Fill Form",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=("#1f538d", "#60a5fa"),
            command=self._encode_fill,
            height=34
        )
        self.encode_btn.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(16, 0))

        # ─── STATUS FOOTER ───
        self._status = ctk.CTkLabel(
            self.scroll_container,
            text="Ready.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("gray50", "gray40"),
            anchor="w"
        )
        self._status.grid(row=2, column=0, sticky="w", padx=4, pady=12)

    def _build_message(self) -> can.Message:
        raw_id = self._id_entry.get().strip()
        can_id = int(raw_id, 16) if raw_id.lower().startswith("0x") else int(raw_id, 16)
        data_str = self._data_entry.get().strip()
        data = bytes(int(b, 16) for b in data_str.split()) if data_str else b'\x00' * int(self._dlc_var.get())
        return can.Message(arbitration_id=can_id, data=data, is_extended_id=self._ext_var.get())

    def _send_once(self):
        try:
            bus_manager.send(self._build_message())
            self._status.configure(text="[Sent] Frame successfully transmitted.", text_color="green")
        except Exception as e:
            self._status.configure(text=f"Error: {e}", text_color="red")

    def _toggle_cyclic(self):
        if self._cyclic_running:
            self._cyclic_running = False
            if self._cyclic_after:
                self.after_cancel(self._cyclic_after)
            self._cyclic_btn.configure(text="Start Cyclic", fg_color=None, hover_color=None)
            self.snd_dot.configure(fg_color="gray")
            self.snd_text.configure(text="Cyclic: Inactive", text_color=("gray50", "gray40"))
            self._status.configure(text="Stopped cyclic transmission.", text_color=("gray50", "gray40"))
        else:
            try:
                interval = int(self._cyclic_entry.get() or "100")
                if interval <= 0:
                    self._status.configure(text="[Warning] Interval must be greater than 0 ms.", text_color="orange")
                    return
                self._cyclic_running = True
                self._cyclic_btn.configure(text="Stop Cyclic", fg_color="#dc2626", hover_color="#ef4444")
                self.snd_dot.configure(fg_color="#10b981")
                self.snd_text.configure(text="Cyclic: Active", text_color="#10b981")
                self._status.configure(text=f"Sending cyclic frames every {interval} ms...", text_color="green")
                self._do_cyclic(interval)
            except Exception as e:
                self._status.configure(text=f"Error: {e}", text_color="red")

    def _do_cyclic(self, interval: int):
        if not self._cyclic_running:
            return
        self._send_once()
        self._cyclic_after = self.after(interval, self._do_cyclic, interval)

    def _encode_fill(self):
        try:
            name = self._msg_name_entry.get().strip()
            signals = json.loads(self._signals_entry.get().strip())
            data = dbc_manager.encode(name, signals)
            msg_def = dbc_manager._db.get_message_by_name(name)
            self._id_entry.delete(0, "end")
            self._id_entry.insert(0, hex(msg_def.frame_id))
            self._data_entry.delete(0, "end")
            self._data_entry.insert(0, data.hex(" ").upper())
            self._status.configure(text="[Encoded] DBC encoding successful. Form filled.", text_color="green")
        except Exception as e:
            self._status.configure(text=f"Encode error: {e}", text_color="red")
