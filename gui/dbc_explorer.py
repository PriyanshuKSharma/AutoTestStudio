import os
import customtkinter as ctk
from core.dbc import dbc_manager

class DBCExplorerPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
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
            text="DBC Explorer",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            anchor="w"
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_frame,
            text="Browse and inspect database message specifications and signals",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=("gray50", "gray40"),
            anchor="w"
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # Action Buttons
        self.refresh_btn = ctk.CTkButton(
            header_frame,
            text="Refresh Database",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
            hover_color=("gray90", "gray28"),
            border_width=1,
            border_color=("gray80", "gray30"),
            text_color=("#1f538d", "#60a5fa"),
            command=self._populate,
            height=32
        )
        self.refresh_btn.grid(row=0, column=1, sticky="e")

        # ─── PANE GRID ───
        pane_grid = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        pane_grid.grid(row=1, column=0, sticky="nsew")
        pane_grid.columnconfigure(0, weight=4, uniform="split")
        pane_grid.columnconfigure(1, weight=9, uniform="split")

        # Left Column Card (Messages)
        left_card = ctk.CTkFrame(
            pane_grid,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_card.columnconfigure(0, weight=1)

        left_inner = ctk.CTkFrame(left_card, fg_color="transparent")
        left_inner.pack(padx=16, pady=16, fill="both", expand=True)
        left_inner.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_inner,
            text="MESSAGES",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 10))

        self._msg_list = ctk.CTkScrollableFrame(left_inner, height=480, fg_color="transparent")
        self._msg_list.pack(fill="both", expand=True)

        # Right Column Card (Signals Detail)
        right_card = ctk.CTkFrame(
            pane_grid,
            fg_color=("white", "gray22"),
            border_width=1,
            border_color=("gray85", "gray28"),
            corner_radius=12
        )
        right_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_card.columnconfigure(0, weight=1)

        right_inner = ctk.CTkFrame(right_card, fg_color="transparent")
        right_inner.pack(padx=16, pady=16, fill="both", expand=True)
        right_inner.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right_inner,
            text="SIGNALS AND METADATA",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#1f538d", "#60a5fa"),
            anchor="w"
        ).pack(anchor="w", pady=(0, 10))

        self._sig_frame = ctk.CTkScrollableFrame(right_inner, height=480, fg_color="transparent")
        self._sig_frame.pack(fill="both", expand=True)

        self._populate()

    def _populate(self):
        for w in self._msg_list.winfo_children():
            w.destroy()
        for w in self._sig_frame.winfo_children():
            w.destroy()

        if not dbc_manager.loaded:
            ctk.CTkLabel(
                self._msg_list,
                text="No database file loaded. Go to Settings.",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=("gray50", "gray40")
            ).pack(pady=40)
            return

        for msg in dbc_manager.messages():
            label = f"0x{msg.frame_id:03X}  {msg.name}"
            btn = ctk.CTkButton(
                self._msg_list,
                text=label,
                anchor="w",
                fg_color="transparent",
                hover_color=("gray90", "gray28"),
                text_color=("#1a202c", "#f7fafc"),
                font=ctk.CTkFont(family="Segoe UI", size=12),
                command=lambda m=msg: self._show_signals(m),
                height=32,
            )
            btn.pack(fill="x", pady=1)

    def _show_signals(self, msg_def):
        for w in self._sig_frame.winfo_children():
            w.destroy()

        # Message Profile Card
        msg_card = ctk.CTkFrame(self._sig_frame, fg_color=("gray95", "gray25"), corner_radius=6)
        msg_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            msg_card,
            text=f"Frame Name: {msg_def.name}   |   ID: 0x{msg_def.frame_id:03X}   |   DLC: {msg_def.length} bytes",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=("#1f538d", "#60a5fa")
        ).pack(side="left", padx=12, pady=8)

        # Signals Table Header
        header = ctk.CTkFrame(self._sig_frame, fg_color=("gray90", "gray28"), corner_radius=4)
        header.pack(fill="x", pady=(0, 4))
        
        cols = [
            ("Signal Name", 180),
            ("Start Bit", 60),
            ("Length", 60),
            ("Factor", 70),
            ("Offset", 70),
            ("Unit", 60),
            ("Min", 60),
            ("Max", 60)
        ]
        
        for col, w in cols:
            ctk.CTkLabel(
                header,
                text=col,
                width=w,
                anchor="w",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold")
            ).pack(side="left", padx=6, pady=4)

        for i, sig in enumerate(msg_def.signals):
            row_bg = ("gray95", "gray24") if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(self._sig_frame, fg_color=row_bg, corner_radius=4)
            row.pack(fill="x", pady=1)
            
            data_cells = [
                (sig.name, 180, "Segoe UI", False),
                (str(sig.start), 60, "Consolas", True),
                (str(sig.length), 60, "Consolas", True),
                (str(sig.scale), 70, "Consolas", True),
                (str(sig.offset), 70, "Consolas", True),
                (sig.unit or "", 60, "Segoe UI", False),
                (str(sig.minimum) if sig.minimum is not None else "", 60, "Consolas", True),
                (str(sig.maximum) if sig.maximum is not None else "", 60, "Consolas", True),
            ]
            
            for text, width, font_family, is_num in data_cells:
                text_color = ("gray10", "gray90")
                if is_num and text:
                    text_color = ("gray40", "gray60")
                ctk.CTkLabel(
                    row,
                    text=text,
                    width=width,
                    anchor="w",
                    font=ctk.CTkFont(family=font_family, size=12),
                    text_color=text_color
                ).pack(side="left", padx=6, pady=3)
