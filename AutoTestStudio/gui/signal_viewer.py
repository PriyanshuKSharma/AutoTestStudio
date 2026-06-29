import threading
import customtkinter as ctk
import can
from core.bus import bus_manager
from core.dbc import dbc_manager


class SignalViewerPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._running = False
        self._labels: dict[str, ctk.CTkLabel] = {}
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(top, text="Signal Viewer", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        self._stop_btn = ctk.CTkButton(top, text="Stop", width=80, command=self._stop, state="disabled")
        self._stop_btn.pack(side="right", padx=4)
        self._start_btn = ctk.CTkButton(top, text="Start", width=80, command=self._start)
        self._start_btn.pack(side="right", padx=4)

        self._grid_frame = ctk.CTkScrollableFrame(self)
        self._grid_frame.pack(fill="both", expand=True, padx=16, pady=8)
        ctk.CTkLabel(self._grid_frame, text="Connect bus and load DBC, then press Start.",
                     text_color="gray").pack(pady=40)

    def _start(self):
        if not bus_manager.connected or not dbc_manager.loaded:
            return
        self._running = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._build_signal_grid()
        t = threading.Thread(target=self._recv_loop, daemon=True)
        t.start()

    def _stop(self):
        self._running = False
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")

    def _build_signal_grid(self):
        for w in self._grid_frame.winfo_children():
            w.destroy()
        self._labels.clear()
        row = 0
        for msg_def in dbc_manager.messages():
            ctk.CTkLabel(self._grid_frame, text=f"0x{msg_def.frame_id:03X}  {msg_def.name}",
                         font=ctk.CTkFont(weight="bold")).grid(row=row, column=0, columnspan=4, padx=8, pady=(10, 2), sticky="w")
            row += 1
            for sig in msg_def.signals:
                ctk.CTkLabel(self._grid_frame, text=sig.name, anchor="w", width=180).grid(row=row, column=0, padx=16, pady=2, sticky="w")
                val_lbl = ctk.CTkLabel(self._grid_frame, text="—", anchor="w", width=120)
                val_lbl.grid(row=row, column=1, padx=8, pady=2, sticky="w")
                ctk.CTkLabel(self._grid_frame, text=sig.unit or "", text_color="gray", width=60).grid(row=row, column=2, padx=4)
                self._labels[f"{msg_def.frame_id}:{sig.name}"] = val_lbl
                row += 1

    def _recv_loop(self):
        while self._running:
            msg = bus_manager.recv(timeout=0.5)
            if msg:
                decoded = dbc_manager.decode(msg.arbitration_id, bytes(msg.data))
                if decoded:
                    self.after(0, self._update_labels, msg.arbitration_id, decoded)

    def _update_labels(self, can_id: int, decoded: dict):
        for name, value in decoded.items():
            key = f"{can_id}:{name}"
            if key in self._labels:
                text = f"{value:.3f}" if isinstance(value, float) else str(value)
                self._labels[key].configure(text=text, text_color="cyan")
