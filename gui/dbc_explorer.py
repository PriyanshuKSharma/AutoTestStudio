import customtkinter as ctk
from core.dbc import dbc_manager


class DBCExplorerPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(top, text="DBC Explorer", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="Refresh", width=80, command=self._populate).pack(side="right")

        pane = ctk.CTkFrame(self)
        pane.pack(fill="both", expand=True, padx=16, pady=8)

        # Message list (left)
        left = ctk.CTkFrame(pane, width=240)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        ctk.CTkLabel(left, text="Messages", font=ctk.CTkFont(weight="bold")).pack(pady=8)
        self._msg_list = ctk.CTkScrollableFrame(left)
        self._msg_list.pack(fill="both", expand=True)

        # Signal detail (right)
        right = ctk.CTkFrame(pane)
        right.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(right, text="Signals", font=ctk.CTkFont(weight="bold")).pack(pady=8)
        self._sig_frame = ctk.CTkScrollableFrame(right)
        self._sig_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._populate()

    def _populate(self):
        for w in self._msg_list.winfo_children():
            w.destroy()
        for w in self._sig_frame.winfo_children():
            w.destroy()

        if not dbc_manager.loaded:
            ctk.CTkLabel(self._msg_list, text="No DBC loaded", text_color="gray").pack(pady=20)
            return

        for msg in dbc_manager.messages():
            label = f"0x{msg.frame_id:03X}  {msg.name}"
            btn = ctk.CTkButton(
                self._msg_list, text=label, anchor="w",
                fg_color="transparent", hover_color=("gray75", "gray30"),
                command=lambda m=msg: self._show_signals(m), height=32,
            )
            btn.pack(fill="x", pady=1)

    def _show_signals(self, msg_def):
        for w in self._sig_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._sig_frame,
                     text=f"{msg_def.name}  |  ID: 0x{msg_def.frame_id:03X}  |  DLC: {msg_def.length}",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(4, 8))

        header = ctk.CTkFrame(self._sig_frame)
        header.pack(fill="x", pady=2)
        for col, w in [("Signal", 180), ("Start", 60), ("Length", 60), ("Factor", 70), ("Offset", 70), ("Unit", 60), ("Min", 60), ("Max", 60)]:
            ctk.CTkLabel(header, text=col, width=w, anchor="w",
                         font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)

        for i, sig in enumerate(msg_def.signals):
            row = ctk.CTkFrame(self._sig_frame,
                               fg_color=("gray85", "gray22") if i % 2 == 0 else "transparent")
            row.pack(fill="x", pady=1)
            for text, width in [
                (sig.name, 180),
                (str(sig.start), 60),
                (str(sig.length), 60),
                (str(sig.scale), 70),
                (str(sig.offset), 70),
                (sig.unit or "", 60),
                (str(sig.minimum) if sig.minimum is not None else "", 60),
                (str(sig.maximum) if sig.maximum is not None else "", 60),
            ]:
                ctk.CTkLabel(row, text=text, width=width, anchor="w").pack(side="left", padx=4)
