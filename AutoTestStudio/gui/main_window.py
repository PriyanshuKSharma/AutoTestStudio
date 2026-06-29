import customtkinter as ctk
from gui.home import HomePanel
from gui.sender import SenderPanel
from gui.monitor import MonitorPanel
from gui.dbc_explorer import DBCExplorerPanel
from gui.signal_viewer import SignalViewerPanel
from gui.test_builder import TestBuilderPanel
from gui.test_runner import TestRunnerPanel
from gui.fault_injection import FaultInjectionPanel
from gui.reports import ReportsPanel
from gui.settings import SettingsPanel

NAV_ITEMS = [
    ("🏠  Home",           HomePanel),
    ("📡  CAN Monitor",    MonitorPanel),
    ("📤  CAN Sender",     SenderPanel),
    ("📊  Signal Viewer",  SignalViewerPanel),
    ("📖  DBC Explorer",   DBCExplorerPanel),
    ("🔧  Test Builder",   TestBuilderPanel),
    ("▶️   Test Runner",    TestRunnerPanel),
    ("⚡  Fault Injection", FaultInjectionPanel),
    ("📋  Reports",        ReportsPanel),
    ("⚙️   Settings",       SettingsPanel),
]


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("AutoTest Studio")
        self.geometry("1280x800")
        self.minsize(1024, 640)

        self._panels: dict[str, ctk.CTkFrame] = {}
        self._active_btn = None
        self._build_layout()
        self._show_panel("🏠  Home")

    def _build_layout(self):
        # Sidebar
        self._sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        ctk.CTkLabel(
            self._sidebar, text="AutoTest\nStudio",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 24))

        for label, PanelClass in NAV_ITEMS:
            btn = ctk.CTkButton(
                self._sidebar, text=label, anchor="w",
                fg_color="transparent", hover_color=("gray75", "gray30"),
                command=lambda l=label: self._show_panel(l),
                corner_radius=0, height=36,
            )
            btn.pack(fill="x", padx=8, pady=2)

        # Content area
        self._content = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "gray17"))
        self._content.pack(side="left", fill="both", expand=True)

        for label, PanelClass in NAV_ITEMS:
            panel = PanelClass(self._content)
            panel.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._panels[label] = panel

    def _show_panel(self, label: str):
        for key, panel in self._panels.items():
            if key == label:
                panel.lift()
            else:
                panel.lower()
