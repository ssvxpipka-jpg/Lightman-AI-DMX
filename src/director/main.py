#!/usr/bin/env python3
"""
Lightman Director Application (PySide6)
========================================
Main control center for the Lightman stage lighting automation system.

Tabs: [Studio] [Settings] [Script] [Live Light] [Knowledge Base] [Rehearsals] [Profile]
Features:
  - Login window (pops up before main window)
  - 3D scene viewport (PyQtGraph OpenGL stub)
  - Chat agent panel
  - Language selector (English / Russian)
  - Lightman Server stubs (v2.0)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QGuiApplication, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpacerItem, QSizePolicy, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox,
    QTabWidget, QGridLayout, QTextEdit, QComboBox, QCheckBox,
)

from shared.config import get_logger, ensure_directories
from shared.i18n import _, set_language, get_available_languages
from shared.auth import register_user, authenticate, load_profile, login
from shared.server_client import ServerClient

# OpenGL imports for 3D view controls
try:
    from pyqtgraph.opengl import GLMeshItem, GLGridItem
except Exception:
    GLMeshItem = None
    GLGridItem = None

logger = get_logger("director")


# ─── Login Dialog ────────────────────────────────────────────────────

class LoginDialog(QDialog):
    """
    Login dialog that appears before the main Director window.
    Supports both login and registration.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(_("Login"))
        self.resize(350, 200)
        self._is_login_mode = True
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QFormLayout(self)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(_("Username"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText(_("Password"))

        layout.addRow(QLabel(_("Username")), self.username_input)
        layout.addRow(QLabel(_("Password")), self.password_input)

        # Toggle mode button
        self.toggle_btn = QPushButton(_("New User? Register"))
        self.toggle_btn.clicked.connect(self._toggle_mode)
        layout.addRow(self.toggle_btn)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _toggle_mode(self) -> None:
        self._is_login_mode = not self._is_login_mode
        if self._is_login_mode:
            self.setWindowTitle(_("Login"))
            self.toggle_btn.setText(_("New User? Register"))
        else:
            self.setWindowTitle(_("Register"))
            self.toggle_btn.setText(_("Already have an account? Login"))

    def _accept(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, _("Error"), "Please enter username and password.")
            return

        if self._is_login_mode:
            if authenticate(username, password):
                self.accept()
            else:
                QMessageBox.warning(self, _("Error"), "Invalid credentials.")
        else:
            if register_user(username, password):
                QMessageBox.information(self, _("Status"), "Registration successful. Please login.")
                self._is_login_mode = True
                self._toggle_mode()
            else:
                QMessageBox.warning(self, _("Error"), "Registration failed. Username may already exist.")


# ─── Director Main Window ────────────────────────────────────────────

class DirectorWindow(QMainWindow):
    """
    Main Director window with tab-based interface.

    Tabs: [Studio] [Settings] [Script] [Live Light] [Knowledge Base] [Rehearsals] [Profile]
    """

    TABS = [
        "Studio", "Settings", "Script",
        "Live Light", "Knowledge Base", "Rehearsals", "Profile",
    ]

    def __init__(self, username: str, parent=None) -> None:
        super().__init__(parent)
        self.username = username
        self.setWindowTitle(f"{_('Lightman Director')} — {username}")
        self.resize(1200, 720)
        self._center()

        # Initialize modules
        ensure_directories()
        self._profile = load_profile(username)
        self._server_client = ServerClient()
        self._engine = None  # LightEngine will be set in studio tab

        # Haze Analyzer (initialised lazily with RTSP feed)
        self._haze_analyzer = None
        self._haze_timer = None
        self._last_haze_score = 0.0
        self._haze_warned = False

        # Apply saved language
        lang = self._profile.get("settings", {}).get("language", "en") if self._profile else "en"
        set_language(lang)
        self._rebuild_ui_text()

        self._build_ui()

        # Apply saved haze settings to UI
        if self._profile:
            settings = self._profile.get("settings", {})
            if settings.get("haze_enabled", False):
                self.haze_checkbox.setChecked(True)
            self.haze_min_input.setText(str(settings.get("haze_min_score", "0.3")))
            # Start haze monitoring if enabled
            if self.haze_checkbox.isChecked():
                self._start_haze_monitoring()

    def _center(self) -> None:
        frame = self.frameGeometry()
        screen = QGuiApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(screen)
        self.move(frame.topLeft())

    def _build_ui(self) -> None:
        """Build the complete UI: tabs + chat dock."""
        # Menu bar
        self._build_menu()

        # Central widget: tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.tabBar().setMovable(True)

        self._tab_widgets = {}
        for i, tab_name in enumerate(self.TABS):
            widget = self._build_tab(tab_name)
            self._tab_widgets[tab_name] = widget
            self.tab_widget.addTab(widget, _(tab_name))

        self.setCentralWidget(self.tab_widget)

        # Chat dock (right side)
        self._build_chat_dock()

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def _build_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self._logout)
        file_menu.addAction(logout_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")
        lang_action = QAction("Language", self)
        lang_action.triggered.connect(self._open_language_selector)
        view_menu.addAction(lang_action)

    def _build_chat_dock(self) -> None:
        from PySide6.QtWidgets import QDockWidget
        dock = QDockWidget("Agent Chat", self)
        dock.setAllowedAreas(Qt.RightDockWidgetArea)

        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)

        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setMaximumWidth(350)
        chat_layout.addWidget(QLabel("Agent:"))
        chat_layout.addWidget(self.chat_history)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText(_("Type a message..."))
        self.chat_input.returnPressed.connect(self._send_chat)
        chat_layout.addWidget(self.chat_input)

        send_btn = QPushButton(_("Send"))
        send_btn.clicked.connect(self._send_chat)
        chat_layout.addWidget(send_btn)

        dock.setWidget(chat_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def _build_tab(self, name: str) -> QWidget:
        """Dispatch to the correct tab builder."""
        builders = {
            "Studio": self._build_studio_tab,
            "Settings": self._build_settings_tab,
            "Script": self._build_script_tab,
            "Live Light": self._build_live_light_tab,
            "Knowledge Base": self._build_knowledge_base_tab,
            "Rehearsals": self._build_rehearsals_tab,
            "Profile": self._build_profile_tab,
        }
        return builders[name]()

    # ─── Studio Tab ─────────────────────────────────────────────────

    def _build_studio_tab(self) -> QWidget:
        """Build the Studio tab with 3D viewport and controls."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 3D viewport — real PyQtGraph OpenGL scene with stage fixtures
        from src.director.ui_3d import Lightman3DView
        self.viewport_widget = Lightman3DView()
        self.viewport_widget.setMinimumSize(600, 400)
        layout.addWidget(self.viewport_widget, stretch=1)

        # Viewport controls
        view_controls = QHBoxLayout()
        self.reset_view_btn = QPushButton(_("Reset View"))
        self.reset_view_btn.setStyleSheet("font-size: 12px; padding: 6px 12px;")
        self.reset_view_btn.clicked.connect(self._reset_3d_view)
        view_controls.addWidget(self.reset_view_btn)

        self.toggle_wireframe_btn = QPushButton(_("Toggle Wireframe"))
        self.toggle_wireframe_btn.setStyleSheet("font-size: 12px; padding: 6px 12px;")
        self.toggle_wireframe_btn.clicked.connect(self._toggle_wireframe)
        view_controls.addWidget(self.toggle_wireframe_btn)

        self.toggle_grid_btn = QPushButton(_("Toggle Grid"))
        self.toggle_grid_btn.setStyleSheet("font-size: 12px; padding: 6px 12px;")
        self.toggle_grid_btn.clicked.connect(self._toggle_grid)
        view_controls.addWidget(self.toggle_grid_btn)
        view_controls.addStretch()
        layout.addLayout(view_controls)

        return widget

    def _reset_3d_view(self) -> None:
        """Reset the 3D viewport camera to the default position."""
        if hasattr(self, "viewport_widget") and self.viewport_widget:
            self.viewport_widget.setCameraPosition(distance=400, elevation=25, azimuth=-45)

    def _toggle_wireframe(self) -> None:
        """Toggle wireframe mode for all mesh items in the 3D view."""
        if hasattr(self, "viewport_widget") and self.viewport_widget:
            view = self.viewport_widget
            # Toggle shader between 'shaded' and 'wireframe'
            items = getattr(view, "items", [])
            if not items:
                # collect child items
                pass
            for item in view.items:
                if isinstance(item, GLMeshItem):
                    item.shader = "wireframe" if item.shader == "shaded" else "shaded"
                    item.update()

    def _toggle_grid(self) -> None:
        """Toggle the floor grid visibility."""
        if hasattr(self, "viewport_widget") and self.viewport_widget:
            view = self.viewport_widget
            self._grid_visible = not getattr(self, "_grid_visible", True)
            for item in view.items:
                if isinstance(item, GLGridItem):
                    item.setVisible(self._grid_visible)

    # ─── Haze Analyzer ──────────────────────────────────────────────

    def _init_haze_analyzer(self) -> None:
        """Initialize the HazeAnalyzer with the RTSP URL from settings."""
        rtsp_url = self.rtsp_input.text().strip()
        if not rtsp_url:
            return
        try:
            from shared.haze_analyzer import HazeAnalyzer
            import cv2
            cap = cv2.VideoCapture()
            cap.open(rtsp_url)
            if not cap.isOpened():
                logger.warning("HazeAnalyzer: could not open RTSP stream")
                return
            w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self._haze_analyzer = HazeAnalyzer(image_width=w, image_height=h)
            self._haze_cap = cap
            logger.info("HazeAnalyzer initialized with RTSP stream")
        except Exception as e:
            logger.error(f"HazeAnalyzer init failed: {e}")
            self._haze_analyzer = None

    def _check_haze(self) -> None:
        """Periodically analyse a frame for haze level and warn if low."""
        if not self.haze_checkbox.isChecked():
            return
        if self._haze_analyzer is None or not hasattr(self, "_haze_cap"):
            self._init_haze_analyzer()
            return

        # Fixture positions for beam projection (mirrors the 3D scene)
        fixture_positions = [
            (-120, 40, -100),  # MH left
            (120, 40, -100),   # MH right
            (-80, 10, -110),   # LED bar left
            (80, 10, -110),    # LED bar right
        ]

        score = self._haze_analyzer.analyze_frame_from_capture(self._haze_cap, fixture_positions)
        if score is None:
            return

        self._last_haze_score = score
        self.status_bar.showMessage(f"Haze score: {score:.2f}", 3000)

        # Check threshold
        try:
            min_score = float(self.haze_min_input.text())
        except ValueError:
            min_score = 0.3

        if self._haze_analyzer.should_warn_user(score, min_score) and not self._haze_warned:
            self._haze_warned = True
            self.chat_history.append(
                f"⚠️ AI Agent: Haze level is too low (Score: {score:.1f}). "
                f"Beams are not visible! Please increase hazer output."
            )
            self.chat_input.setReadOnly(False)
        elif score >= min_score and self._haze_warned:
            self._haze_warned = False

    def _start_haze_monitoring(self) -> None:
        """Start the periodic haze check timer."""
        self._haze_timer = QTimer()
        self._haze_timer.timeout.connect(self._check_haze)
        self._haze_timer.start(3000)  # check every 3 seconds

    def _stop_haze_monitoring(self) -> None:
        """Stop the haze check timer."""
        if self._haze_timer:
            self._haze_timer.stop()
            self._haze_timer = None


    # ─── Settings Tab ───────────────────────────────────────────────

    def _build_settings_tab(self) -> QWidget:
        """Build the Settings tab with all configuration options."""
        widget = QWidget()
        layout = QFormLayout(widget)

        # Language selector
        self.lang_combo = QComboBox()
        for code, name in get_available_languages():
            self.lang_combo.addItem(name, code)
        layout.addRow(QLabel(_("Language")), self.lang_combo)
        self.lang_combo.currentTextChanged.connect(self._on_language_changed)

        # Mode selector
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([_("full_auto"), _("assist"), _("follow_only")])
        layout.addRow(QLabel(_("Mode")), self.mode_combo)

        # Audience selector
        self.audience_combo = QComboBox()
        self.audience_combo.addItems([_("kids"), _("teens"), _("adults")])
        layout.addRow(QLabel(_("Audience")), self.audience_combo)

        # RTSP URL
        self.rtsp_input = QLineEdit()
        self.rtsp_input.setPlaceholderText("rtsp://user:pass@host:port/stream")
        layout.addRow(QLabel(_("RTSP URL")), self.rtsp_input)

        # Standby level
        self.standby_input = QLineEdit("0.05")
        layout.addRow(QLabel(_("Standby Level")), self.standby_input)

        # Intercept threshold
        self.intercept_input = QLineEdit("0.15")
        layout.addRow(QLabel(_("Intercept Threshold")), self.intercept_input)

        # Haze Analyzer settings
        self.haze_checkbox = QCheckBox(_("I have a Hazer/Smoke Machine"))
        self.haze_checkbox.setChecked(False)
        layout.addRow(self.haze_checkbox)

        self.haze_min_input = QLineEdit("0.3")
        haze_input_label = QLabel(_("Minimum acceptable Haze Score"))
        layout.addRow(haze_input_label, self.haze_min_input)

        # Save button
        save_btn = QPushButton(_("Save Profile"))
        save_btn.clicked.connect(self._save_settings)
        layout.addRow(save_btn)

        # ─── Server section (stub) ────────────────────────────────
        layout.addRow(QLabel(""))  # spacer

        server_group = self._build_server_section()
        layout.addRow(server_group)

        return widget

    def _build_server_section(self) -> QWidget:
        """Build the 'Lightman Server (Coming Soon)' section."""
        group = QWidget()
        group.setStyleSheet("background-color: #1a1a2e; border: 1px solid #333; border-radius: 6px;")
        layout = QVBoxLayout(group)

        header = QLabel(_("Lightman Server (Coming Soon)"))
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(12)
        header.setFont(header_font)
        header.setStyleSheet("color: #aaa; padding: 8px;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setContentsMargins(12, 0, 12, 12)

        self.server_login_input = QLineEdit()
        self.server_login_input.setPlaceholderText("username")
        self.server_login_input.setEnabled(False)
        form.addRow(QLabel(_("Server Login") + ":"), self.server_login_input)

        self.server_pass_input = QLineEdit()
        self.server_pass_input.setEchoMode(QLineEdit.Password)
        self.server_pass_input.setPlaceholderText("••••••")
        self.server_pass_input.setEnabled(False)
        form.addRow(QLabel(_("Server Password") + ":"), self.server_pass_input)

        self.server_connect_btn = QPushButton(_("Connect"))
        self.server_connect_btn.setEnabled(False)
        self.server_connect_btn.setToolTip(_("Server OS coming in v2.0"))
        form.addRow(self.server_connect_btn)

        layout.addLayout(form)
        return group

    # ─── Script Tab ─────────────────────────────────────────────────

    def _build_script_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.script_input = QTextEdit()
        self.script_input.setPlaceholderText("Paste or load script.txt content here...")
        self.script_input.setMinimumHeight(200)
        layout.addWidget(self.script_input)

        btn_row = QHBoxLayout()
        parse_btn = QPushButton(_("Parse Script"))
        parse_btn.clicked.connect(self._parse_script)
        btn_row.addWidget(parse_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.timeline_display = QTextEdit()
        self.timeline_display.setReadOnly(True)
        self.timeline_display.setPlaceholderText("Timeline will appear here...")
        layout.addWidget(self.timeline_display)
        return widget

    def _build_live_light_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        select_btn = QPushButton(_("Select Fixtures"))
        select_btn.clicked.connect(self._select_fixtures)
        layout.addWidget(select_btn)
        self.fixture_status = QLabel(_("No fixtures selected"))
        layout.addWidget(self.fixture_status)

        self.priority_display = QTextEdit()
        self.priority_display.setReadOnly(True)
        self.priority_display.setMaximumHeight(150)
        self.priority_display.setPlaceholderText("Fixture priority list...")
        layout.addWidget(self.priority_display)

        self.mute_btn = QPushButton(_("Mute"))
        self.mute_btn.setCheckable(True)
        self.mute_btn.toggled.connect(self._toggle_mute)
        layout.addWidget(self.mute_btn)
        return widget

    def _build_knowledge_base_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        search_row = QHBoxLayout()
        self.kb_search_input = QLineEdit()
        self.kb_search_input.setPlaceholderText(_("Search") + "...")
        search_row.addWidget(self.kb_search_input)
        search_btn = QPushButton(_("Search"))
        search_btn.clicked.connect(self._search_kb)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)

        add_btn = QPushButton(_("Add Document"))
        layout.addWidget(add_btn)

        self.kb_results = QTextEdit()
        self.kb_results.setReadOnly(True)
        self.kb_results.setPlaceholderText("Search results will appear here...")
        layout.addWidget(self.kb_results)
        return widget

    def _build_rehearsals_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        btn_row = QHBoxLayout()
        self.record_btn = QPushButton(_("Start Recording"))
        self.record_btn.setCheckable(True)
        self.record_btn.toggled.connect(self._toggle_recording)
        btn_row.addWidget(self.record_btn)

        stop_btn = QPushButton(_("Stop Recording"))
        stop_btn.clicked.connect(self._stop_recording)
        btn_row.addWidget(stop_btn)
        layout.addLayout(btn_row)

        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel(_("Playback Speed") + ":"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["1x", "2x", "3x", "5x"])
        speed_row.addWidget(self.speed_combo)
        speed_row.addStretch()
        layout.addLayout(speed_row)

        report_btn = QPushButton(_("Generate Report"))
        report_btn.clicked.connect(self._generate_report)
        layout.addWidget(report_btn)

        self.rehearsal_log = QTextEdit()
        self.rehearsal_log.setReadOnly(True)
        self.rehearsal_log.setPlaceholderText("Rehearsal log...")
        layout.addWidget(self.rehearsal_log)
        return widget

    def _build_profile_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)

        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText("Display Name")
        layout.addRow(QLabel(_("Display Name")), self.display_name_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email (optional)")
        layout.addRow(QLabel("Email"), self.email_input)

        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText("Role (e.g. Director, Teacher)")
        layout.addRow(QLabel("Role"), self.role_input)

        save_btn = QPushButton(_("Save Profile"))
        save_btn.clicked.connect(self._save_profile)
        layout.addRow(save_btn)
        return widget

    # ─── Slot Methods ───────────────────────────────────────────────

    def _on_language_changed(self) -> None:
        code = self.lang_combo.currentData()
        set_language(code)
        try:
            from shared.auth import update_profile_setting
            update_profile_setting(self.username, "settings.language", code)
        except Exception as e:
            logger.error("Failed to save language setting: %s", e)
        logger.info("Language changed to: %s", code)

    def _save_settings(self) -> None:
        """Save settings from the Settings tab."""
        try:
            from shared.auth import update_profile_setting
            update_profile_setting(self.username, "settings.mode", self.mode_combo.currentText())
            update_profile_setting(self.username, "settings.audience", self.audience_combo.currentText())
            update_profile_setting(self.username, "settings.rtsp_url", self.rtsp_input.text())
            update_profile_setting(self.username, "settings.haze_enabled", self.haze_checkbox.isChecked())
            update_profile_setting(self.username, "settings.haze_min_score", self.haze_min_input.text())
            update_profile_setting(self.username, "settings.language",
                                    self.lang_combo.currentData())
        except Exception as e:
            logger.error("Failed to save settings: %s", e)
        self.status_bar.showMessage("Settings saved", 3000)

        # Start / stop haze monitoring based on checkbox
        if self.haze_checkbox.isChecked():
            self._start_haze_monitoring()
        else:
            self._stop_haze_monitoring()

    def _save_profile(self) -> None:
        """Save profile from the Profile tab."""
        try:
            from shared.auth import update_profile_setting
            update_profile_setting(self.username, "display_name", self.display_name_input.text())
            update_profile_setting(self.username, "email", self.email_input.text())
            update_profile_setting(self.username, "role", self.role_input.text())
        except Exception as e:
            logger.error("Failed to save profile: %s", e)
        self.status_bar.showMessage("Profile saved", 3000)

    def _send_chat(self) -> None:
        """Send a chat message to the agent."""
        msg = self.chat_input.text().strip()
        if not msg:
            return
        self.chat_history.append(f"<b>You:</b> {msg}")
        self.chat_input.clear()
        # TODO: Send to LangGraph assistant agent
        response = f"[Assistant] Received: '{msg}' (stub)"
        self.chat_history.append(response)

    def _parse_script(self) -> None:
        """Parse script text and build timeline."""
        text = self.script_input.toPlainText().strip()
        if not text:
            self.timeline_display.setPlainText("No script text to parse.")
            return
        self.timeline_display.setPlainText(
            f"Script parsed (stub):\n{text[:200]}...\n\n"
            "Anchors: [Scene 1] [Scene 2] [Scene 3]\n"
            "Timeline built.")

    def _select_fixtures(self) -> None:
        QMessageBox.information(self, _("Select Fixtures"),
            "Fixture selection dialog (stub).\n"
            "Will show fixture library with GDTF search.")

    def _toggle_mute(self, muted: bool) -> None:
        if muted:
            self.mute_btn.setText(_("Unmute"))
        else:
            self.mute_btn.setText(_("Mute"))

    def _search_kb(self) -> None:
        query = self.kb_search_input.text().strip()
        if not query:
            return
        self.kb_results.setPlainText(
            f"Search results for '{query}' (stub):\n\n"
            "1. [Document] Light Safety Guidelines\n"
            "2. [Document] DMX Protocol Overview\n"
            "3. [Document] Strobe Frequency Recommendations")

    def _toggle_recording(self, recording: bool) -> None:
        if recording:
            self.record_btn.setText(_("Stop Recording"))
        else:
            self.record_btn.setText(_("Start Recording"))

    def _stop_recording(self) -> None:
        if self.record_btn.isChecked():
            self.record_btn.setChecked(False)
            self.record_btn.setText(_("Start Recording"))

    def _generate_report(self) -> None:
        self.rehearsal_log.setPlainText(
            "Rehearsal Report (stub):\n"
            "- Total movements: 1,247\n"
            "- Audio peaks: 89\n"
            "- AI corrections: 12\n"
            "- User interventions: 3\n")

    def _logout(self) -> None:
        try:
            from shared.auth import logout
            logout(self.username)
        except Exception:
            pass
        self.close()

    def _rebuild_ui_text(self) -> None:
        """Rebuild UI text with current language."""
        for i, tab_name in enumerate(self.TABS):
            self.tab_widget.setTabText(i, _(tab_name))
        self.mute_btn.setText(_("Mute"))
        self.status_bar.showMessage("Ready")


# ─── Entry Point ─────────────────────────────────────────────────────

def main() -> None:
    """Entry point for the Director application."""
    set_language("en")

    app = QApplication(sys.argv)

    # Show login dialog first
    login_dialog = LoginDialog()
    login_dialog.exec()

    # If user cancelled login, exit
    if login_dialog.result() == QDialog.Rejected:
        sys.exit(0)

    username = login_dialog.username_input.text().strip()
    if not username:
        sys.exit(0)

    # Authenticate and store session in keyring
    from shared.auth import login
    token = login(username, login_dialog.password_input.text())
    if not token:
        sys.exit(0)

    # Create and show main window
    window = DirectorWindow(username)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


