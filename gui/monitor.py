import threading
import customtkinter as ctk
import can
from core.bus import bus_manager
from core.dbc import dbc_manager
from core.simulator import bms_simulator
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
            text="CAN Monitor",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            anchor="w",
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Analyze and log real-time CAN bus frames and signal values",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("gray50", "gray40"),
            anchor="w",
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # Status badge (Top Right)
        status_card = ctk.CTkFrame(
            header_frame,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=10,
        )
        status_card.grid(row=0, column=1, sticky="e")

        self.mon_dot = ctk.CTkFrame(
            status_card, width=10, height=10, corner_radius=5, fg_color="#ef4444"
        )
        self.mon_dot.pack(side="left", padx=(16, 8), pady=8)

        self.mon_text = ctk.CTkLabel(
            status_card,
            text="Status: Stopped",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#ef4444", "#ef4444"),
        )
        self.mon_text.pack(side="left", padx=(0, 16), pady=8)

        # ─── CONTROLS CARD ───
        ctrl_card = ctk.CTkFrame(
            self.scroll_container,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12,
        )
        ctrl_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        ctrl_inner = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        ctrl_inner.pack(padx=20, pady=16, fill="both", expand=True)

        # Left controls (simulator checkbox)
        self._sim_var = ctk.BooleanVar(value=False)
        self.sim_chk = ctk.CTkCheckBox(
            ctrl_inner,
            text="Run BMS Simulator (virtual bus)",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            variable=self._sim_var,
            command=self._toggle_simulator,
        )
        self.sim_chk.pack(side="left", pady=4)

        # Simulator status dot
        self.sim_status_inner = ctk.CTkFrame(ctrl_inner, fg_color="transparent")
        self.sim_status_inner.pack(side="left", padx=16)

        self.sim_dot = ctk.CTkFrame(
            self.sim_status_inner, width=8, height=8, corner_radius=4, fg_color="gray"
        )
        self.sim_dot.pack(side="left", padx=(0, 6))

        self.sim_lbl = ctk.CTkLabel(
            self.sim_status_inner,
            text="Simulator: Off",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("gray50", "gray40"),
        )
        self.sim_lbl.pack(side="left")

        # Right control buttons
        self._start_btn = ctk.CTkButton(
            ctrl_inner,
            text="Start",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=("#1f538d", "#60a5fa"),
            command=self._start,
            width=80,
            height=32,
        )
        self._start_btn.pack(side="right", padx=4)

        self._stop_btn = ctk.CTkButton(
            ctrl_inner,
            text="Stop",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self._stop,
            state="disabled",
            width=80,
            height=32,
        )
        self._stop_btn.pack(side="right", padx=4)

        self.clear_btn = ctk.CTkButton(
            ctrl_inner,
            text="Clear Logs",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._clear,
            width=90,
            height=32,
        )
        self.clear_btn.pack(side="right", padx=4)

        # Status text row
        self._status = ctk.CTkLabel(
            self.scroll_container,
            text="Connect the bus in Settings, then press Start.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=("gray50", "gray40"),
            anchor="w",
        )
        self._status.grid(row=2, column=0, sticky="w", padx=4, pady=(0, 10))

        # ─── DATA TABLE CARD ───
        table_card = ctk.CTkFrame(
            self.scroll_container,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12,
        )
        table_card.grid(row=3, column=0, sticky="nsew")
        table_card.columnconfigure(0, weight=1)

        # Table Header
        header = ctk.CTkFrame(
            table_card, fg_color=("gray95", "gray25"), corner_radius=10
        )
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))

        for col, w in [
            ("Time", 110),
            ("CAN ID", 80),
            ("DLC", 40),
            ("Data (hex)", 210),
            ("Decoded Signals", 0),
        ]:
            ctk.CTkLabel(
                header,
                text=col,
                width=w,
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=("#1f538d", "#60a5fa"),
            ).pack(side="left", padx=10, pady=6)

        # Scroll Frame for records
        self._scroll = ctk.CTkScrollableFrame(
            table_card, height=400, fg_color="transparent"
        )
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    # ------------------------------------------------------------------ #
    #  Start / Stop                                                      #
    # ------------------------------------------------------------------ #
    def _start(self):
        if not bus_manager.connected:
            self._status.configure(
                text="[Warning] Bus not connected — go to Settings and connect first.",
                text_color="orange",
            )
            return
        self._running = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(
            state="normal", fg_color="#dc2626", hover_color="#ef4444"
        )
        self._status.configure(
            text="[Receiving] Capturing live frames...", text_color="green"
        )

        self.mon_dot.configure(fg_color="#10b981")
        self.mon_text.configure(text="Status: Active", text_color="#10b981")

        self._thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._thread.start()

    def _stop(self):
        self._running = False
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(
            state="disabled", fg_color="transparent", hover_color="transparent"
        )
        self._status.configure(text="Stopped.", text_color=("gray50", "gray40"))

        self.mon_dot.configure(fg_color="#ef4444")
        self.mon_text.configure(text="Status: Stopped", text_color="#ef4444")

    def destroy(self):
        """Stop the recv thread before Tkinter tears down the widget tree."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        super().destroy()

    def _clear(self):
        for w in self._scroll.winfo_children():
            w.destroy()
        self._row_count = 0

    # ------------------------------------------------------------------ #
    #  Simulator                                                         #
    # ------------------------------------------------------------------ #
    def _toggle_simulator(self):
        if self._sim_var.get():
            if not bus_manager.connected:
                self._status.configure(
                    text="[Warning] Connect the bus before starting the simulator.",
                    text_color="orange",
                )
                self._sim_var.set(False)
                return
            bms_simulator.start()
            self.sim_dot.configure(fg_color="#10b981")
            self.sim_lbl.configure(text="Simulator: Active", text_color="#10b981")
        else:
            bms_simulator.stop()
            self.sim_dot.configure(fg_color="gray")
            self.sim_lbl.configure(
                text="Simulator: Off", text_color=("gray50", "gray40")
            )

    # ------------------------------------------------------------------ #
    #  Receive loop                                                      #
    # ------------------------------------------------------------------ #
    def _recv_loop(self):
        while self._running:
            try:
                msg = bus_manager.recv(timeout=0.5)
            except Exception:
                break
            if msg and self._running:
                self._log_to_db(msg)
                try:
                    self.after(0, self._add_row, msg)
                except Exception:
                    break

    def _log_to_db(self, msg: can.Message):
        db = get_db()
        db.execute(
            "INSERT INTO can_log (timestamp, can_id, dlc, data, channel) VALUES (?,?,?,?,?)",
            (
                datetime.utcnow().isoformat(),
                hex(msg.arbitration_id),
                msg.dlc,
                msg.data.hex(" ").upper(),
                bus_manager.channel,
            ),
        )
        db.commit()

    def _add_row(self, msg: can.Message):
        # Bail out if the widget has already been destroyed (e.g. window closing)
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        # Drop oldest row when cap reached
        if self._row_count >= MAX_ROWS:
            children = self._scroll.winfo_children()
            if children:
                try:
                    children[0].destroy()
                except Exception:
                    pass

        decoded = dbc_manager.decode(msg.arbitration_id, bytes(msg.data))
        decoded_str = (
            "  ".join(
                f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}"
                for k, v in decoded.items()
            )
            if decoded
            else ""
        )

        bg = ("gray95", "gray25") if self._row_count % 2 == 0 else "transparent"
        row = ctk.CTkFrame(self._scroll, fg_color=bg, corner_radius=6)
        row.pack(fill="x", pady=1, padx=4)

        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        for text, width in [
            (ts, 110),
            (f"0x{msg.arbitration_id:03X}", 80),
            (str(msg.dlc), 40),
            (msg.data.hex(" ").upper(), 210),
            (decoded_str, 0),
        ]:
            font_family = "Consolas" if width > 0 else "Segoe UI"
            ctk.CTkLabel(
                row,
                text=text,
                width=width,
                anchor="w",
                font=ctk.CTkFont(family=font_family, size=12),
            ).pack(side="left", padx=10, pady=4)

        self._row_count += 1
