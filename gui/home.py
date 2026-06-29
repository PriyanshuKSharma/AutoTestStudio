import customtkinter as ctk
from core.project import project
from core.bus import bus_manager


class HomePanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="AutoTest Studio", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(40, 4))
        ctk.CTkLabel(self, text="Python Automotive Test Framework", text_color="gray").pack()

        card = ctk.CTkFrame(self)
        card.pack(pady=30, padx=60, fill="x")

        self._status_label = ctk.CTkLabel(card, text="● Bus: Disconnected", text_color="red",
                                          font=ctk.CTkFont(size=14))
        self._status_label.grid(row=0, column=0, padx=20, pady=16, sticky="w")

        self._project_label = ctk.CTkLabel(card, text=f"Project: {project.name}", font=ctk.CTkFont(size=13))
        self._project_label.grid(row=1, column=0, padx=20, pady=4, sticky="w")

        self._dbc_label = ctk.CTkLabel(card, text=f"DBC: {project.dbc_path or 'None loaded'}", font=ctk.CTkFont(size=13))
        self._dbc_label.grid(row=2, column=0, padx=20, pady=(4, 16), sticky="w")

        ctk.CTkButton(self, text="Refresh Status", command=self._refresh).pack(pady=8)

        # Quick-start guide
        tips = ctk.CTkFrame(self)
        tips.pack(pady=10, padx=60, fill="x")
        ctk.CTkLabel(tips, text="Quick Start", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        for step in [
            "1. Go to Settings → set Bus interface and load a DBC file.",
            "2. Open CAN Monitor to watch live traffic.",
            "3. Use CAN Sender to transmit frames.",
            "4. Use Test Builder to write Python test scripts.",
            "5. Run tests from Test Runner.",
        ]:
            ctk.CTkLabel(tips, text=step, anchor="w").pack(anchor="w", padx=24, pady=2)
        ctk.CTkLabel(tips, text="").pack(pady=4)

    def _refresh(self):
        connected = bus_manager.connected
        self._status_label.configure(
            text=f"● Bus: {'Connected' if connected else 'Disconnected'}",
            text_color="green" if connected else "red",
        )
        self._project_label.configure(text=f"Project: {project.name}")
        self._dbc_label.configure(text=f"DBC: {project.dbc_path or 'None loaded'}")
