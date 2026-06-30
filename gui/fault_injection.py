import customtkinter as ctk
import can
from core.bus import bus_manager
from core.dbc import dbc_manager
from core.logger import logger

FAULTS = {
    "Over Voltage":    {"BMS_Status": {"SOC": 80, "BMS_State": 4, "Error_Flags": 1, "Counter": 0, "Checksum": 0}},
    "Under Voltage":   {"BMS_Status": {"SOC": 5,  "BMS_State": 4, "Error_Flags": 2, "Counter": 0, "Checksum": 0}},
    "Over Temperature":{"BMS_Temps":  {"Temp_Max": 75, "Temp_Min": 40, "Temp_Avg": 58}},
    "Clear Faults":    {"BMS_Status": {"SOC": 70, "BMS_State": 1, "Error_Flags": 0, "Counter": 0, "Checksum": 0}},
}


class FaultInjectionPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        # ─── HEADER ───
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(20, 12))

        title_label = ctk.CTkLabel(
            header_frame,
            text="Fault Injection",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            anchor="w"
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Inject simulated database faults or errant raw frames directly onto the active bus",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("gray50", "gray40"),
            anchor="w"
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # ─── MAIN PANE SPLIT (2 Columns) ───
        pane_grid = ctk.CTkFrame(self, fg_color="transparent")
        pane_grid.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        pane_grid.columnconfigure(0, weight=1, uniform="fault_cols")
        pane_grid.columnconfigure(1, weight=1, uniform="fault_cols")

        # Left Column: Predefined & Custom Controls
        left_col = ctk.CTkFrame(pane_grid, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_col.columnconfigure(0, weight=1)

        # Right Column: Console Activity Log
        right_col = ctk.CTkFrame(pane_grid, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_col.columnconfigure(0, weight=1)

        # ─── PREDEFINED FAULTS CARD (Left Column) ───
        faults_card = ctk.CTkFrame(
            left_col,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        faults_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        faults_inner = ctk.CTkFrame(faults_card, fg_color="transparent")
        faults_inner.pack(padx=16, pady=16, fill="both", expand=True)
        faults_inner.columnconfigure(0, weight=1)
        faults_inner.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            faults_inner,
            text="PREDEFINED FAULT PAYLOADS",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        divider1 = ctk.CTkFrame(faults_inner, height=1, fg_color=("gray90", "gray28"))
        divider1.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        for idx, (fault_name, payload) in enumerate(FAULTS.items()):
            is_clear = "Clear" in fault_name
            color = "#ef4444" if not is_clear else "#6b7280"
            hover = "#dc2626" if not is_clear else "#4b5563"
            
            btn = ctk.CTkButton(
                faults_inner,
                text=fault_name,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                fg_color=color,
                hover_color=hover,
                command=lambda fn=fault_name, p=payload: self._inject(fn, p),
                height=38
            )
            btn.grid(row=idx // 2 + 2, column=idx % 2, padx=6, pady=6, sticky="ew")

        # ─── CUSTOM FRAME INJECT CARD (Left Column) ───
        custom_card = ctk.CTkFrame(
            left_col,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        custom_card.grid(row=1, column=0, sticky="ew")
        custom_card.columnconfigure(0, weight=1)

        custom_inner = ctk.CTkFrame(custom_card, fg_color="transparent")
        custom_inner.pack(padx=16, pady=16, fill="both", expand=True)

        ctk.CTkLabel(
            custom_inner,
            text="CUSTOM RAW FRAME INJECTION",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        divider2 = ctk.CTkFrame(custom_inner, height=1, fg_color=("gray90", "gray28"))
        divider2.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        # ID Row
        ctk.CTkLabel(custom_inner, text="CAN ID (hex):", font=ctk.CTkFont(family="Segoe UI", size=13)).grid(row=2, column=0, sticky="w", pady=6)
        self._id_entry = ctk.CTkEntry(custom_inner, placeholder_text="0x100", font=ctk.CTkFont(family="Consolas", size=13), width=100)
        self._id_entry.grid(row=2, column=1, sticky="w", pady=6, padx=(12, 0))

        # Data Row
        ctk.CTkLabel(custom_inner, text="Data (hex bytes):", font=ctk.CTkFont(family="Segoe UI", size=13)).grid(row=3, column=0, sticky="w", pady=6)
        self._data_entry = ctk.CTkEntry(custom_inner, placeholder_text="80 04 01 00 FF 00 00 00", font=ctk.CTkFont(family="Consolas", size=13))
        self._data_entry.grid(row=3, column=1, sticky="ew", pady=6, padx=(12, 0))

        custom_inner.columnconfigure(1, weight=1)

        # Inject Button
        self.inject_raw_btn = ctk.CTkButton(
            custom_inner,
            text="Inject Raw Frame",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=("#1f538d", "#60a5fa"),
            command=self._inject_raw,
            height=34
        )
        self.inject_raw_btn.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        # ─── CONSOLE ACTIVITY LOG (Right Column) ───
        log_card = ctk.CTkFrame(
            right_col,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        log_card.pack(fill="both", expand=True)

        log_inner = ctk.CTkFrame(log_card, fg_color="transparent")
        log_inner.pack(padx=16, pady=16, fill="both", expand=True)

        ctk.CTkLabel(
            log_inner,
            text="INJECTION ACTIVITY LOG",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 6))

        self._log_box = ctk.CTkTextbox(
            log_inner,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=("gray95", "gray17"),
            border_width=1,
            border_color=("gray80", "gray30"),
            border_spacing=6,
            corner_radius=6,
            state="disabled"
        )
        self._log_box.pack(fill="both", expand=True)

    def _inject(self, name: str, payload: dict):
        if not bus_manager.connected:
            self._log(f"[ABORT] Bus not connected — cannot inject {name}")
            return
        if not dbc_manager.loaded:
            self._log(f"[ABORT] DBC not loaded — cannot encode {name}")
            return
        try:
            for msg_name, signals in payload.items():
                data = dbc_manager.encode(msg_name, signals)
                msg_def = dbc_manager._db.get_message_by_name(msg_name)
                msg = can.Message(arbitration_id=msg_def.frame_id, data=data, is_extended_id=False)
                bus_manager.send(msg)
            logger.fault(f"Fault injected: {name}", payload)
            self._log(f"[INJECTED] {name}")
        except Exception as e:
            self._log(f"[ERROR] Injecting {name}: {e}")

    def _inject_raw(self):
        if not bus_manager.connected:
            self._log("[ABORT] Bus not connected")
            return
        try:
            raw_id = self._id_entry.get().strip()
            can_id = int(raw_id, 16) if raw_id.lower().startswith("0x") else int(raw_id, 10)
            data = bytes(int(b, 16) for b in self._data_entry.get().strip().split())
            msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=False)
            bus_manager.send(msg)
            self._log(f"[RAW INJECT] ID: 0x{can_id:03X}  Data: {data.hex(' ').upper()}")
        except Exception as e:
            self._log(f"[ERROR] Raw Injection: {e}")

    def _log(self, text: str):
        self._log_box.configure(state="normal")
        self._log_box.insert("end", text + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")
