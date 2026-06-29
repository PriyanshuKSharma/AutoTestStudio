import threading
import customtkinter as ctk
import can
from core.bus import bus_manager
from core.dbc import dbc_manager
from database.sqlite import get_db
from datetime import datetime

MAX_ROWS = 200


class MonitorPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._running = False
        self._thread = None
        self._row_count = 0
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(top, text="CAN Monitor", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="Clear", width=80, command=self._clear).pack(side="right", padx=4)
        self._stop_btn = ctk.CTkButton(top, text="Stop", width=80, command=self._stop, state="disabled")
        self._stop_btn.pack(side="right", padx=4)
        self._start_btn = ctk.CTkButton(top, text="Start", width=80, command=self._start)
        self._start_btn.pack(side="right", padx=4)

        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=16)
        for col, w in [("Time", 100), ("CAN ID", 80), ("DLC", 40), ("Data (hex)", 200), ("Decoded", 360)]:
            ctk.CTkLabel(header, text=col, width=w, anchor="w",
                         font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)

        self._scroll = ctk.CTkScrollableFrame(self)
        self._scroll.pack(fill="both", expand=True, padx=16, pady=8)

    def _start(self):
        if not bus_manager.connected:
            ctk.CTkMessagebox = None  # placeholder
            return
        self._running = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._thread.start()

    def _stop(self):
        self._running = False
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")

    def _clear(self):
        for widget in self._scroll.winfo_children():
            widget.destroy()
        self._row_count = 0

    def _recv_loop(self):
        while self._running:
            msg = bus_manager.recv(timeout=0.5)
            if msg:
                self._log_to_db(msg)
                self.after(0, self._add_row, msg)

    def _log_to_db(self, msg: can.Message):
        db = get_db()
        db.execute(
            "INSERT INTO can_log (timestamp, can_id, dlc, data, channel) VALUES (?,?,?,?,?)",
            (datetime.utcnow().isoformat(), hex(msg.arbitration_id), msg.dlc,
             msg.data.hex(" ").upper(), "vcan0"),
        )
        db.commit()

    def _add_row(self, msg: can.Message):
        if self._row_count >= MAX_ROWS:
            children = self._scroll.winfo_children()
            if children:
                children[0].destroy()
        decoded = dbc_manager.decode(msg.arbitration_id, bytes(msg.data))
        decoded_str = "  ".join(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}"
                                for k, v in decoded.items()) if decoded else ""
        row = ctk.CTkFrame(self._scroll, fg_color=("gray85", "gray22") if self._row_count % 2 == 0 else "transparent")
        row.pack(fill="x", pady=1)
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        for text, width in [
            (ts, 100),
            (f"0x{msg.arbitration_id:03X}", 80),
            (str(msg.dlc), 40),
            (msg.data.hex(" ").upper(), 200),
            (decoded_str, 360),
        ]:
            ctk.CTkLabel(row, text=text, width=width, anchor="w").pack(side="left", padx=4)
        self._row_count += 1
