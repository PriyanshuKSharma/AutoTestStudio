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
        ctk.CTkLabel(self, text="Fault Injection", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(self, text="Inject CAN fault frames directly onto the bus.", text_color="gray").pack(anchor="w", padx=16)

        grid = ctk.CTkFrame(self)
        grid.pack(padx=16, pady=16, fill="x")

        for i, (fault_name, payload) in enumerate(FAULTS.items()):
            color = "red" if "Voltage" in fault_name or "Temperature" in fault_name else "gray40"
            btn = ctk.CTkButton(
                grid, text=fault_name, width=200, height=48,
                fg_color=color,
                command=lambda fn=fault_name, p=payload: self._inject(fn, p),
            )
            btn.grid(row=i // 2, column=i % 2, padx=12, pady=8)

        # Custom raw frame injection
        sep = ctk.CTkFrame(self, height=2, fg_color="gray40")
        sep.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(self, text="Custom Frame Inject", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16)

        form = ctk.CTkFrame(self)
        form.pack(padx=16, pady=8, fill="x")
        ctk.CTkLabel(form, text="CAN ID").grid(row=0, column=0, padx=12, pady=8, sticky="w")
        self._id_entry = ctk.CTkEntry(form, placeholder_text="0x100", width=120)
        self._id_entry.grid(row=0, column=1, padx=8)
        ctk.CTkLabel(form, text="Data (hex)").grid(row=1, column=0, padx=12, pady=8, sticky="w")
        self._data_entry = ctk.CTkEntry(form, placeholder_text="80 04 01 00 FF 00 00 00", width=280)
        self._data_entry.grid(row=1, column=1, padx=8)
        ctk.CTkButton(form, text="Inject Raw", command=self._inject_raw).grid(row=1, column=2, padx=8)

        self._log_box = ctk.CTkTextbox(self, height=180, font=ctk.CTkFont(family="Courier", size=12), state="disabled")
        self._log_box.pack(fill="x", padx=16, pady=8)

    def _inject(self, name: str, payload: dict):
        if not bus_manager.connected:
            self._log(f"Bus not connected — cannot inject {name}")
            return
        if not dbc_manager.loaded:
            self._log(f"DBC not loaded — cannot encode {name}")
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
            self._log(f"Error injecting {name}: {e}")

    def _inject_raw(self):
        if not bus_manager.connected:
            self._log("Bus not connected")
            return
        try:
            raw_id = self._id_entry.get().strip()
            can_id = int(raw_id, 16)
            data = bytes(int(b, 16) for b in self._data_entry.get().strip().split())
            msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=False)
            bus_manager.send(msg)
            self._log(f"[RAW] 0x{can_id:03X}  {data.hex(' ').upper()}")
        except Exception as e:
            self._log(f"Error: {e}")

    def _log(self, text: str):
        self._log_box.configure(state="normal")
        self._log_box.insert("end", text + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")
