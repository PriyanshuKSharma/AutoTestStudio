import customtkinter as ctk
import can
from core.bus import bus_manager
from core.dbc import dbc_manager


class SenderPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="CAN Sender", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))

        form = ctk.CTkFrame(self)
        form.pack(padx=16, pady=8, fill="x")

        # CAN ID
        ctk.CTkLabel(form, text="CAN ID (hex)").grid(row=0, column=0, padx=12, pady=8, sticky="w")
        self._id_entry = ctk.CTkEntry(form, placeholder_text="0x180", width=120)
        self._id_entry.grid(row=0, column=1, padx=12, pady=8, sticky="w")

        # Extended ID
        self._ext_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(form, text="Extended ID", variable=self._ext_var).grid(row=0, column=2, padx=12)

        # DLC
        ctk.CTkLabel(form, text="DLC").grid(row=1, column=0, padx=12, pady=8, sticky="w")
        self._dlc_var = ctk.StringVar(value="8")
        ctk.CTkOptionMenu(form, values=[str(i) for i in range(9)], variable=self._dlc_var, width=80).grid(row=1, column=1, padx=12, sticky="w")

        # Data
        ctk.CTkLabel(form, text="Data (hex bytes)").grid(row=2, column=0, padx=12, pady=8, sticky="w")
        self._data_entry = ctk.CTkEntry(form, placeholder_text="80 31 90 45 12 00 00 00", width=320)
        self._data_entry.grid(row=2, column=1, columnspan=3, padx=12, pady=8, sticky="w")

        # Cyclic
        ctk.CTkLabel(form, text="Cyclic (ms, 0=single)").grid(row=3, column=0, padx=12, pady=8, sticky="w")
        self._cyclic_entry = ctk.CTkEntry(form, placeholder_text="0", width=80)
        self._cyclic_entry.grid(row=3, column=1, padx=12, sticky="w")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(padx=16, pady=8, anchor="w")
        ctk.CTkButton(btn_row, text="Send Once", command=self._send_once).pack(side="left", padx=4)
        self._cyclic_btn = ctk.CTkButton(btn_row, text="Start Cyclic", command=self._toggle_cyclic)
        self._cyclic_btn.pack(side="left", padx=4)

        # DBC signal encode helper
        sep = ctk.CTkFrame(self, height=2, fg_color="gray40")
        sep.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(self, text="DBC Signal Encoder", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16)

        dbc_form = ctk.CTkFrame(self)
        dbc_form.pack(padx=16, pady=8, fill="x")
        ctk.CTkLabel(dbc_form, text="Message Name").grid(row=0, column=0, padx=12, pady=8, sticky="w")
        self._msg_name_entry = ctk.CTkEntry(dbc_form, placeholder_text="BMS_Status", width=180)
        self._msg_name_entry.grid(row=0, column=1, padx=12)
        ctk.CTkLabel(dbc_form, text="Signals JSON").grid(row=1, column=0, padx=12, pady=8, sticky="w")
        self._signals_entry = ctk.CTkEntry(dbc_form, placeholder_text='{"SOC": 80, "BMS_State": 3}', width=360)
        self._signals_entry.grid(row=1, column=1, padx=12, pady=8)
        ctk.CTkButton(dbc_form, text="Encode & Fill", command=self._encode_fill).grid(row=1, column=2, padx=8)

        self._status = ctk.CTkLabel(self, text="", text_color="gray")
        self._status.pack(padx=16, pady=4)

        self._cyclic_running = False
        self._cyclic_after = None

    def _build_message(self) -> can.Message:
        raw_id = self._id_entry.get().strip()
        can_id = int(raw_id, 16) if raw_id.startswith("0x") or raw_id.startswith("0X") else int(raw_id, 16)
        data_str = self._data_entry.get().strip()
        data = bytes(int(b, 16) for b in data_str.split()) if data_str else b'\x00' * int(self._dlc_var.get())
        return can.Message(arbitration_id=can_id, data=data, is_extended_id=self._ext_var.get())

    def _send_once(self):
        try:
            bus_manager.send(self._build_message())
            self._status.configure(text="Sent ✓", text_color="green")
        except Exception as e:
            self._status.configure(text=f"Error: {e}", text_color="red")

    def _toggle_cyclic(self):
        if self._cyclic_running:
            self._cyclic_running = False
            if self._cyclic_after:
                self.after_cancel(self._cyclic_after)
            self._cyclic_btn.configure(text="Start Cyclic")
        else:
            interval = int(self._cyclic_entry.get() or "100")
            if interval <= 0:
                return
            self._cyclic_running = True
            self._cyclic_btn.configure(text="Stop Cyclic")
            self._do_cyclic(interval)

    def _do_cyclic(self, interval: int):
        if not self._cyclic_running:
            return
        self._send_once()
        self._cyclic_after = self.after(interval, self._do_cyclic, interval)

    def _encode_fill(self):
        import json
        try:
            name = self._msg_name_entry.get().strip()
            signals = json.loads(self._signals_entry.get().strip())
            data = dbc_manager.encode(name, signals)
            msg_def = dbc_manager._db.get_message_by_name(name)
            self._id_entry.delete(0, "end")
            self._id_entry.insert(0, hex(msg_def.frame_id))
            self._data_entry.delete(0, "end")
            self._data_entry.insert(0, data.hex(" ").upper())
            self._status.configure(text="Encoded ✓", text_color="green")
        except Exception as e:
            self._status.configure(text=f"Encode error: {e}", text_color="red")
