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
        # Main scroll container to prevent sizing issues
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
            text="Signal Viewer",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            anchor="w"
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Display real-time signal values decoded from active CAN messages",
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

        self.view_dot = ctk.CTkFrame(status_card, width=10, height=10, corner_radius=5, fg_color="gray")
        self.view_dot.pack(side="left", padx=(16, 8), pady=8)
        
        self.view_text = ctk.CTkLabel(
            status_card,
            text="Viewer: Stopped",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("gray50", "gray40")
        )
        self.view_text.pack(side="left", padx=(0, 16), pady=8)

        # ─── CONTROLS CARD ───
        ctrl_card = ctk.CTkFrame(
            self.scroll_container,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        ctrl_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        ctrl_inner = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        ctrl_inner.pack(padx=20, pady=16, fill="both", expand=True)

        ctk.CTkLabel(
            ctrl_inner,
            text="Controls",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=("#1f538d", "#60a5fa")
        ).pack(side="left")

        self._start_btn = ctk.CTkButton(
            ctrl_inner,
            text="Start",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=("#1f538d", "#60a5fa"),
            command=self._start,
            width=80,
            height=32
        )
        self._start_btn.pack(side="right", padx=4)

        self._stop_btn = ctk.CTkButton(
            ctrl_inner,
            text="Stop",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self._stop,
            state="disabled",
            width=80,
            height=32
        )
        self._stop_btn.pack(side="right", padx=4)

        # ─── SIGNAL GRID CARD ───
        self.grid_card = ctk.CTkFrame(
            self.scroll_container,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        self.grid_card.grid(row=2, column=0, sticky="nsew")
        self.grid_card.columnconfigure(0, weight=1)

        self._grid_frame = ctk.CTkScrollableFrame(self.grid_card, height=450, fg_color="transparent")
        self._grid_frame.pack(fill="both", expand=True, padx=16, pady=16)
        self._grid_frame.columnconfigure(0, weight=1)

        self.placeholder_lbl = ctk.CTkLabel(
            self._grid_frame,
            text="Connect the bus and load a DBC file, then press Start.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("gray50", "gray40")
        )
        self.placeholder_lbl.pack(pady=60)

    def _start(self):
        if not bus_manager.connected or not dbc_manager.loaded:
            return
        
        self.placeholder_lbl.pack_forget()
        self._running = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal", fg_color="#dc2626", hover_color="#ef4444")
        
        self.view_dot.configure(fg_color="#10b981")
        self.view_text.configure(text="Viewer: Active", text_color="#10b981")

        self._build_signal_grid()
        t = threading.Thread(target=self._recv_loop, daemon=True)
        t.start()

    def _stop(self):
        self._running = False
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled", fg_color=None, hover_color=None)
        
        self.view_dot.configure(fg_color="gray")
        self.view_text.configure(text="Viewer: Stopped", text_color=("gray50", "gray40"))

    def _build_signal_grid(self):
        for w in self._grid_frame.winfo_children():
            w.destroy()
        self._labels.clear()

        # Configure columns inside scrollable area for table layout
        self._grid_frame.columnconfigure(0, weight=2)  # Name
        self._grid_frame.columnconfigure(1, weight=1)  # Value
        self._grid_frame.columnconfigure(2, weight=1)  # Unit

        row = 0
        for msg_def in dbc_manager.messages():
            # Message Group Header Row
            group_frame = ctk.CTkFrame(self._grid_frame, fg_color=("gray95", "gray25"), corner_radius=6)
            group_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(10, 4), padx=4)

            group_lbl = ctk.CTkLabel(
                group_frame,
                text=f"Frame ID: 0x{msg_def.frame_id:03X}   Message: {msg_def.name}",
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                text_color=("#1f538d", "#60a5fa")
            )
            group_lbl.pack(side="left", padx=10, pady=6)
            row += 1

            for sig in msg_def.signals:
                # Signal Row
                sig_row_bg = ("gray98", "gray24") if row % 2 == 0 else "transparent"
                sig_frame = ctk.CTkFrame(self._grid_frame, fg_color=sig_row_bg, corner_radius=4)
                sig_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=1, padx=4)
                
                sig_frame.columnconfigure(0, weight=2)
                sig_frame.columnconfigure(1, weight=1)
                sig_frame.columnconfigure(2, weight=1)

                name_lbl = ctk.CTkLabel(
                    sig_frame,
                    text=sig.name,
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                    anchor="w"
                )
                name_lbl.grid(row=0, column=0, padx=12, pady=4, sticky="w")

                val_lbl = ctk.CTkLabel(
                    sig_frame,
                    text="—",
                    font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                    text_color=("gray40", "gray60"),
                    anchor="w"
                )
                val_lbl.grid(row=0, column=1, padx=8, pady=4, sticky="w")

                unit_lbl = ctk.CTkLabel(
                    sig_frame,
                    text=sig.unit or "",
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                    text_color=("gray50", "gray40"),
                    anchor="w"
                )
                unit_lbl.grid(row=0, column=2, padx=12, pady=4, sticky="w")

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
                # Use a nice theme-compatible blue/light-blue highlight color on change
                self._labels[key].configure(text=text, text_color=("#1d4ed8", "#60a5fa"))
