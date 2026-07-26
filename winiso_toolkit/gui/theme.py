"""WinISO Toolkit — Premium Desktop Theme System.

Monochrome Dark & Light themes inspired by Linear, Vercel, and Raycast.
"""

DARK_THEME_QSS = """
/* ═══════════════════════════════════════════════════════════
   WINISO TOOLKIT — PREMIUM DARK THEME
═══════════════════════════════════════════════════════════ */

* { outline: none; }

QMainWindow, QWidget {
    background-color: #111318;
    color: #e4e4e7;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', system-ui, sans-serif;
    font-size: 13px;
    selection-background-color: #2a2d35;
    selection-color: #ffffff;
}

/* ── SIDEBAR ──────────────────────────────────────────── */

QFrame#sidebar_root {
    background-color: #0d0f13;
    border-right: 1px solid #1e2028;
}

QFrame#sidebar_brand {
    background-color: #0d0f13;
    border-bottom: 1px solid #1e2028;
}

QLabel#brand_app_name {
    color: #f4f4f5;
    font-size: 13.5px;
    font-weight: 700;
    letter-spacing: -0.2px;
    background-color: #0d0f13;
}

QLabel#brand_version {
    color: #52525b;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    background-color: #0d0f13;
}

QLabel#sidebar_section_label {
    color: #3f3f46;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
    background-color: #0d0f13;
    padding: 0 0 0 4px;
}

QPushButton#nav_item {
    background-color: transparent;
    color: #71717a;
    font-size: 12.5px;
    font-weight: 500;
    text-align: left;
    padding: 7px 12px;
    border: 1px solid transparent;
    border-radius: 7px;
}

QPushButton#nav_item:hover {
    color: #d4d4d8;
    background-color: #1a1d25;
}

QPushButton#nav_item[active="true"] {
    color: #ffffff;
    background-color: #1e2130;
    border: 1px solid #2a2d3a;
    font-weight: 600;
}

QPushButton#nav_item[done="true"] {
    color: #4ade80;
}

QPushButton#nav_item[done="true"]:hover {
    color: #86efac;
    background-color: #1a1d25;
}

QPushButton#theme_toggle_btn {
    background-color: transparent;
    color: #52525b;
    font-size: 11.5px;
    font-weight: 500;
    text-align: left;
    padding: 7px 12px;
    border: 1px solid transparent;
    border-radius: 7px;
}

QPushButton#theme_toggle_btn:hover {
    color: #a1a1aa;
    background-color: #1a1d25;
}

/* ── PAGE HEADER ──────────────────────────────────────── */

QLabel#page_title {
    color: #f4f4f5;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.5px;
    background-color: #111318;
}

QLabel#page_subtitle {
    color: #71717a;
    font-size: 12.5px;
    font-weight: 400;
    background-color: #111318;
}

/* ── STEP PROGRESS BAR ────────────────────────────────── */

QFrame#step_progress_bar {
    background-color: #161921;
    border: 1px solid #1e2028;
    border-radius: 10px;
}

QLabel#step_dot_active {
    background-color: #161921;
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
}

QLabel#step_dot_done {
    background-color: #161921;
    color: #4ade80;
    font-size: 11px;
    font-weight: 600;
}

QLabel#step_dot_pending {
    background-color: #161921;
    color: #3f3f46;
    font-size: 11px;
    font-weight: 500;
}

QFrame#step_line_done {
    background-color: #4ade80;
    max-height: 2px;
    min-height: 2px;
    border: none;
    border-radius: 1px;
}

QFrame#step_line_pending {
    background-color: #2a2d35;
    max-height: 2px;
    min-height: 2px;
    border: none;
    border-radius: 1px;
}

/* ── CARDS ─────────────────────────────────────────────── */

QFrame#card {
    background-color: #161921;
    border: 1px solid #1e2028;
    border-radius: 10px;
}

QFrame#card:hover {
    border-color: #2a2d3a;
}

QFrame#card_elevated {
    background-color: #1a1d25;
    border: 1px solid #1e2028;
    border-radius: 10px;
}

QFrame#card_elevated:hover {
    border-color: #2a2d3a;
}

QFrame#metric_card {
    background-color: #161921;
    border: 1px solid #1e2028;
    border-radius: 8px;
}

QLabel#metric_label {
    color: #71717a;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.3px;
    background-color: transparent;
}

QLabel#metric_value {
    color: #f4f4f5;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: -0.3px;
    background-color: transparent;
}

QLabel#metric_detail {
    color: #71717a;
    font-size: 10.5px;
    font-weight: 500;
    background-color: transparent;
}

/* ── DROPZONE ──────────────────────────────────────────── */

QFrame#dropzone {
    background-color: #131620;
    border: 1.5px dashed #2a2d3a;
    border-radius: 12px;
}

QFrame#dropzone:hover {
    border-color: #3f3f46;
    background-color: #161921;
}

QFrame#dropzone[drag_over="true"] {
    border-color: #ffffff;
    border-width: 2px;
    background-color: #1a1d25;
}

QLabel#dropzone_icon {
    color: #52525b;
    font-size: 36px;
    background-color: transparent;
}

QLabel#dropzone_title {
    color: #d4d4d8;
    font-size: 14px;
    font-weight: 600;
    background-color: transparent;
}

QLabel#dropzone_hint {
    color: #52525b;
    font-size: 11.5px;
    font-weight: 400;
    background-color: transparent;
}

/* ── BADGES / PILLS ────────────────────────────────────── */

QLabel#badge_success {
    background-color: #052e16;
    color: #4ade80;
    border: 1px solid #166534;
    border-radius: 100px;
    padding: 3px 10px;
    font-weight: 600;
    font-size: 11px;
}

QLabel#badge_error {
    background-color: #2a0a0a;
    color: #fca5a5;
    border: 1px solid #7f1d1d;
    border-radius: 100px;
    padding: 3px 10px;
    font-weight: 600;
    font-size: 11px;
}

QLabel#badge_neutral {
    background-color: #1e2028;
    color: #a1a1aa;
    border: 1px solid #2a2d3a;
    border-radius: 100px;
    padding: 3px 10px;
    font-weight: 600;
    font-size: 11px;
}

QLabel#badge_warning {
    background-color: #2a1a03;
    color: #fde68a;
    border: 1px solid #854d0e;
    border-radius: 100px;
    padding: 3px 10px;
    font-weight: 600;
    font-size: 11px;
}

/* ── BUTTONS ───────────────────────────────────────────── */

QPushButton#btn_primary {
    background-color: #e4e4e7;
    color: #111318;
    font-weight: 600;
    font-size: 12.5px;
    border: 1px solid #d4d4d8;
    border-radius: 7px;
    padding: 8px 20px;
    min-height: 20px;
}

QPushButton#btn_primary:hover {
    background-color: #ffffff;
    border-color: #ffffff;
}

QPushButton#btn_primary:pressed {
    background-color: #d4d4d8;
    border-color: #d4d4d8;
}

QPushButton#btn_primary:disabled {
    background-color: #1e2028;
    color: #3f3f46;
    border-color: #1e2028;
}

QPushButton#btn_secondary {
    background-color: #1a1d25;
    color: #d4d4d8;
    font-weight: 500;
    font-size: 12.5px;
    border: 1px solid #2a2d3a;
    border-radius: 7px;
    padding: 8px 18px;
    min-height: 20px;
}

QPushButton#btn_secondary:hover {
    color: #ffffff;
    background-color: #1e2130;
    border-color: #3f3f46;
}

QPushButton#btn_secondary:pressed {
    background-color: #2a2d35;
}

QPushButton#btn_secondary:disabled {
    color: #3f3f46;
    border-color: #1e2028;
    background-color: #161921;
}

QPushButton#btn_ghost {
    background-color: transparent;
    color: #a1a1aa;
    font-weight: 500;
    font-size: 12px;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
}

QPushButton#btn_ghost:hover {
    color: #ffffff;
    background-color: #1a1d25;
}

QPushButton#btn_danger {
    background-color: #2a0a0a;
    color: #fca5a5;
    font-weight: 600;
    font-size: 12.5px;
    border: 1px solid #7f1d1d;
    border-radius: 7px;
    padding: 8px 18px;
    min-height: 20px;
}

QPushButton#btn_danger:hover {
    background-color: #3a1010;
    border-color: #991b1b;
}

/* ── FORM INPUTS ───────────────────────────────────────── */

QLineEdit {
    background-color: #161921;
    border: 1px solid #1e2028;
    border-radius: 7px;
    padding: 8px 12px;
    color: #f4f4f5;
    font-size: 13px;
    min-height: 22px;
}

QLineEdit:hover {
    border-color: #2a2d3a;
}

QLineEdit:focus {
    border-color: #52525b;
    background-color: #131620;
}

QLineEdit::placeholder {
    color: #3f3f46;
}

QComboBox {
    background-color: #161921;
    border: 1px solid #1e2028;
    border-radius: 7px;
    padding: 8px 12px;
    color: #f4f4f5;
    font-size: 13px;
    min-height: 22px;
}

QComboBox:hover {
    border-color: #2a2d3a;
}

QComboBox:focus {
    border-color: #52525b;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #161921;
    border: 1px solid #2a2d3a;
    border-radius: 8px;
    padding: 4px;
    color: #f4f4f5;
    outline: none;
    selection-background-color: #1e2130;
}

/* ── LIST WIDGET ───────────────────────────────────────── */

QListWidget {
    background-color: #131620;
    border: 1px solid #1e2028;
    border-radius: 10px;
    padding: 6px;
    color: #e4e4e7;
    outline: none;
}

QListWidget::item {
    background-color: #161921;
    border: 1px solid #1e2028;
    border-radius: 7px;
    padding: 10px 14px;
    margin: 2px 1px;
    color: #d4d4d8;
    font-size: 12.5px;
}

QListWidget::item:hover {
    border-color: #2a2d3a;
    background-color: #1a1d25;
}

QListWidget::item:selected {
    background-color: #1e2130;
    border: 1px solid #3f3f46;
    color: #ffffff;
    font-weight: 600;
}

/* ── GROUP BOX ─────────────────────────────────────────── */

QGroupBox {
    background-color: #161921;
    border: 1px solid #1e2028;
    border-radius: 10px;
    margin-top: 8px;
    padding: 20px 16px 14px 16px;
    font-weight: 600;
    font-size: 12.5px;
    color: #e4e4e7;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    background-color: #161921;
    color: #a1a1aa;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* ── CHECKBOXES ────────────────────────────────────────── */

QCheckBox {
    color: #d4d4d8;
    font-size: 12.5px;
    font-weight: 400;
    spacing: 8px;
    background-color: transparent;
}

QCheckBox:hover {
    color: #ffffff;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1.5px solid #3f3f46;
    background-color: transparent;
}

QCheckBox::indicator:hover {
    border-color: #71717a;
}

QCheckBox::indicator:checked {
    background-color: #e4e4e7;
    border-color: #e4e4e7;
}

/* ── PROGRESS BAR ──────────────────────────────────────── */

QProgressBar {
    border: 1px solid #1e2028;
    border-radius: 5px;
    text-align: center;
    background-color: #161921;
    color: #71717a;
    font-weight: 600;
    font-size: 11px;
    min-height: 10px;
    max-height: 10px;
}

QProgressBar::chunk {
    background-color: #e4e4e7;
    border-radius: 4px;
}

/* ── CONSOLE ───────────────────────────────────────────── */

QFrame#console_container {
    background-color: #0d0f13;
    border-top: 1px solid #1e2028;
}

QTextEdit#console_output {
    background-color: #0a0c10;
    color: #a1a1aa;
    font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
    font-size: 11px;
    border: 1px solid #1e2028;
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: #2a2d35;
}

QPushButton#console_btn {
    background-color: transparent;
    color: #52525b;
    font-size: 11px;
    font-weight: 500;
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
}

QPushButton#console_btn:hover {
    color: #a1a1aa;
    background-color: #1a1d25;
}

/* ── SCROLLBARS ────────────────────────────────────────── */

QScrollArea {
    background-color: #111318;
    border: none;
}

QScrollBar:vertical {
    background: transparent;
    width: 5px;
    border-radius: 2px;
    margin: 2px 0;
}

QScrollBar::handle:vertical {
    background: #2a2d35;
    border-radius: 2px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #3f3f46;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 5px;
    border-radius: 2px;
}

QScrollBar::handle:horizontal {
    background: #2a2d35;
    border-radius: 2px;
    min-width: 40px;
}

/* ── SEPARATORS & TOOLTIPS ─────────────────────────────── */

QFrame#separator {
    background-color: #1e2028;
    max-height: 1px;
    min-height: 1px;
    border: none;
}

QToolTip {
    background-color: #1a1d25;
    color: #f4f4f5;
    border: 1px solid #2a2d3a;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 11.5px;
}

QMessageBox {
    background-color: #161921;
}

QMessageBox QLabel {
    color: #f4f4f5;
    font-size: 13px;
}
"""


LIGHT_THEME_QSS = """
/* ═══════════════════════════════════════════════════════════
   WINISO TOOLKIT — PREMIUM LIGHT THEME
═══════════════════════════════════════════════════════════ */

* { outline: none; }

QMainWindow, QWidget {
    background-color: #f8f9fa;
    color: #18181b;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', system-ui, sans-serif;
    font-size: 13px;
    selection-background-color: #e4e4e7;
    selection-color: #09090b;
}

/* ── SIDEBAR ──────────────────────────────────────────── */

QFrame#sidebar_root {
    background-color: #f0f1f3;
    border-right: 1px solid #e0e1e5;
}

QFrame#sidebar_brand {
    background-color: #f0f1f3;
    border-bottom: 1px solid #e0e1e5;
}

QLabel#brand_app_name {
    color: #18181b;
    font-size: 13.5px;
    font-weight: 700;
    letter-spacing: -0.2px;
    background-color: #f0f1f3;
}

QLabel#brand_version {
    color: #a1a1aa;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    background-color: #f0f1f3;
}

QLabel#sidebar_section_label {
    color: #a1a1aa;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
    background-color: #f0f1f3;
    padding: 0 0 0 4px;
}

QPushButton#nav_item {
    background-color: transparent;
    color: #71717a;
    font-size: 12.5px;
    font-weight: 500;
    text-align: left;
    padding: 7px 12px;
    border: 1px solid transparent;
    border-radius: 7px;
}

QPushButton#nav_item:hover {
    color: #18181b;
    background-color: #e4e5e9;
}

QPushButton#nav_item[active="true"] {
    color: #18181b;
    background-color: #ffffff;
    border: 1px solid #d8d9dd;
    font-weight: 600;
}

QPushButton#nav_item[done="true"] {
    color: #16a34a;
}

QPushButton#nav_item[done="true"]:hover {
    color: #15803d;
    background-color: #e4e5e9;
}

QPushButton#theme_toggle_btn {
    background-color: transparent;
    color: #a1a1aa;
    font-size: 11.5px;
    font-weight: 500;
    text-align: left;
    padding: 7px 12px;
    border: 1px solid transparent;
    border-radius: 7px;
}

QPushButton#theme_toggle_btn:hover {
    color: #18181b;
    background-color: #e4e5e9;
}

/* ── PAGE HEADER ──────────────────────────────────────── */

QLabel#page_title {
    color: #18181b;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.5px;
    background-color: #f8f9fa;
}

QLabel#page_subtitle {
    color: #71717a;
    font-size: 12.5px;
    font-weight: 400;
    background-color: #f8f9fa;
}

/* ── STEP PROGRESS BAR ────────────────────────────────── */

QFrame#step_progress_bar {
    background-color: #ffffff;
    border: 1px solid #e0e1e5;
    border-radius: 10px;
}

QLabel#step_dot_active {
    background-color: #ffffff;
    color: #18181b;
    font-size: 11px;
    font-weight: 700;
}

QLabel#step_dot_done {
    background-color: #ffffff;
    color: #16a34a;
    font-size: 11px;
    font-weight: 600;
}

QLabel#step_dot_pending {
    background-color: #ffffff;
    color: #d4d4d8;
    font-size: 11px;
    font-weight: 500;
}

QFrame#step_line_done {
    background-color: #16a34a;
    max-height: 2px;
    min-height: 2px;
    border: none;
    border-radius: 1px;
}

QFrame#step_line_pending {
    background-color: #e4e4e7;
    max-height: 2px;
    min-height: 2px;
    border: none;
    border-radius: 1px;
}

/* ── CARDS ─────────────────────────────────────────────── */

QFrame#card {
    background-color: #ffffff;
    border: 1px solid #e0e1e5;
    border-radius: 10px;
}

QFrame#card:hover {
    border-color: #d4d4d8;
}

QFrame#card_elevated {
    background-color: #ffffff;
    border: 1px solid #e0e1e5;
    border-radius: 10px;
}

QFrame#card_elevated:hover {
    border-color: #d4d4d8;
}

QFrame#metric_card {
    background-color: #ffffff;
    border: 1px solid #e0e1e5;
    border-radius: 8px;
}

QLabel#metric_label {
    color: #a1a1aa;
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.3px;
    background-color: transparent;
}

QLabel#metric_value {
    color: #18181b;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: -0.3px;
    background-color: transparent;
}

QLabel#metric_detail {
    color: #a1a1aa;
    font-size: 10.5px;
    font-weight: 500;
    background-color: transparent;
}

/* ── DROPZONE ──────────────────────────────────────────── */

QFrame#dropzone {
    background-color: #ffffff;
    border: 1.5px dashed #d4d4d8;
    border-radius: 12px;
}

QFrame#dropzone:hover {
    border-color: #a1a1aa;
    background-color: #f4f4f5;
}

QFrame#dropzone[drag_over="true"] {
    border-color: #18181b;
    border-width: 2px;
    background-color: #f4f4f5;
}

QLabel#dropzone_icon {
    color: #d4d4d8;
    font-size: 36px;
    background-color: transparent;
}

QLabel#dropzone_title {
    color: #3f3f46;
    font-size: 14px;
    font-weight: 600;
    background-color: transparent;
}

QLabel#dropzone_hint {
    color: #a1a1aa;
    font-size: 11.5px;
    font-weight: 400;
    background-color: transparent;
}

/* ── BADGES / PILLS ────────────────────────────────────── */

QLabel#badge_success {
    background-color: #dcfce7;
    color: #15803d;
    border: 1px solid #86efac;
    border-radius: 100px;
    padding: 3px 10px;
    font-weight: 600;
    font-size: 11px;
}

QLabel#badge_error {
    background-color: #fee2e2;
    color: #b91c1c;
    border: 1px solid #fca5a5;
    border-radius: 100px;
    padding: 3px 10px;
    font-weight: 600;
    font-size: 11px;
}

QLabel#badge_neutral {
    background-color: #f4f4f5;
    color: #71717a;
    border: 1px solid #e4e4e7;
    border-radius: 100px;
    padding: 3px 10px;
    font-weight: 600;
    font-size: 11px;
}

QLabel#badge_warning {
    background-color: #fef3c7;
    color: #b45309;
    border: 1px solid #fde68a;
    border-radius: 100px;
    padding: 3px 10px;
    font-weight: 600;
    font-size: 11px;
}

/* ── BUTTONS ───────────────────────────────────────────── */

QPushButton#btn_primary {
    background-color: #18181b;
    color: #ffffff;
    font-weight: 600;
    font-size: 12.5px;
    border: 1px solid #27272a;
    border-radius: 7px;
    padding: 8px 20px;
    min-height: 20px;
}

QPushButton#btn_primary:hover {
    background-color: #27272a;
    border-color: #3f3f46;
}

QPushButton#btn_primary:pressed {
    background-color: #3f3f46;
}

QPushButton#btn_primary:disabled {
    background-color: #e4e4e7;
    color: #a1a1aa;
    border-color: #e4e4e7;
}

QPushButton#btn_secondary {
    background-color: #ffffff;
    color: #3f3f46;
    font-weight: 500;
    font-size: 12.5px;
    border: 1px solid #e0e1e5;
    border-radius: 7px;
    padding: 8px 18px;
    min-height: 20px;
}

QPushButton#btn_secondary:hover {
    color: #18181b;
    background-color: #f4f4f5;
    border-color: #d4d4d8;
}

QPushButton#btn_secondary:pressed {
    background-color: #e4e4e7;
}

QPushButton#btn_secondary:disabled {
    color: #d4d4d8;
    border-color: #e4e4e7;
    background-color: #f8f9fa;
}

QPushButton#btn_ghost {
    background-color: transparent;
    color: #71717a;
    font-weight: 500;
    font-size: 12px;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
}

QPushButton#btn_ghost:hover {
    color: #18181b;
    background-color: #f4f4f5;
}

QPushButton#btn_danger {
    background-color: #fee2e2;
    color: #b91c1c;
    font-weight: 600;
    font-size: 12.5px;
    border: 1px solid #fca5a5;
    border-radius: 7px;
    padding: 8px 18px;
    min-height: 20px;
}

QPushButton#btn_danger:hover {
    background-color: #fecaca;
    border-color: #f87171;
}

/* ── FORM INPUTS ───────────────────────────────────────── */

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #e0e1e5;
    border-radius: 7px;
    padding: 8px 12px;
    color: #18181b;
    font-size: 13px;
    min-height: 22px;
}

QLineEdit:hover {
    border-color: #d4d4d8;
}

QLineEdit:focus {
    border-color: #a1a1aa;
    background-color: #ffffff;
}

QLineEdit::placeholder {
    color: #d4d4d8;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #e0e1e5;
    border-radius: 7px;
    padding: 8px 12px;
    color: #18181b;
    font-size: 13px;
    min-height: 22px;
}

QComboBox:hover {
    border-color: #d4d4d8;
}

QComboBox:focus {
    border-color: #a1a1aa;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e0e1e5;
    border-radius: 8px;
    padding: 4px;
    color: #18181b;
    outline: none;
    selection-background-color: #f4f4f5;
}

/* ── LIST WIDGET ───────────────────────────────────────── */

QListWidget {
    background-color: #f8f9fa;
    border: 1px solid #e0e1e5;
    border-radius: 10px;
    padding: 6px;
    color: #18181b;
    outline: none;
}

QListWidget::item {
    background-color: #ffffff;
    border: 1px solid #e0e1e5;
    border-radius: 7px;
    padding: 10px 14px;
    margin: 2px 1px;
    color: #3f3f46;
    font-size: 12.5px;
}

QListWidget::item:hover {
    border-color: #d4d4d8;
    background-color: #f4f4f5;
}

QListWidget::item:selected {
    background-color: #f4f4f5;
    border: 1px solid #d4d4d8;
    color: #18181b;
    font-weight: 600;
}

/* ── GROUP BOX ─────────────────────────────────────────── */

QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e0e1e5;
    border-radius: 10px;
    margin-top: 8px;
    padding: 20px 16px 14px 16px;
    font-weight: 600;
    font-size: 12.5px;
    color: #18181b;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    background-color: #ffffff;
    color: #71717a;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* ── CHECKBOXES ────────────────────────────────────────── */

QCheckBox {
    color: #3f3f46;
    font-size: 12.5px;
    font-weight: 400;
    spacing: 8px;
    background-color: transparent;
}

QCheckBox:hover {
    color: #18181b;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1.5px solid #d4d4d8;
    background-color: #ffffff;
}

QCheckBox::indicator:hover {
    border-color: #a1a1aa;
}

QCheckBox::indicator:checked {
    background-color: #18181b;
    border-color: #18181b;
}

/* ── PROGRESS BAR ──────────────────────────────────────── */

QProgressBar {
    border: 1px solid #e0e1e5;
    border-radius: 5px;
    text-align: center;
    background-color: #f4f4f5;
    color: #71717a;
    font-weight: 600;
    font-size: 11px;
    min-height: 10px;
    max-height: 10px;
}

QProgressBar::chunk {
    background-color: #18181b;
    border-radius: 4px;
}

/* ── CONSOLE ───────────────────────────────────────────── */

QFrame#console_container {
    background-color: #f0f1f3;
    border-top: 1px solid #e0e1e5;
}

QTextEdit#console_output {
    background-color: #f8f9fa;
    color: #3f3f46;
    font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
    font-size: 11px;
    border: 1px solid #e0e1e5;
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: #e4e4e7;
}

QPushButton#console_btn {
    background-color: transparent;
    color: #a1a1aa;
    font-size: 11px;
    font-weight: 500;
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
}

QPushButton#console_btn:hover {
    color: #18181b;
    background-color: #e4e5e9;
}

/* ── SCROLLBARS ────────────────────────────────────────── */

QScrollArea {
    background-color: #f8f9fa;
    border: none;
}

QScrollBar:vertical {
    background: transparent;
    width: 5px;
    border-radius: 2px;
    margin: 2px 0;
}

QScrollBar::handle:vertical {
    background: #e4e4e7;
    border-radius: 2px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #d4d4d8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 5px;
    border-radius: 2px;
}

QScrollBar::handle:horizontal {
    background: #e4e4e7;
    border-radius: 2px;
    min-width: 40px;
}

/* ── SEPARATORS & TOOLTIPS ─────────────────────────────── */

QFrame#separator {
    background-color: #e0e1e5;
    max-height: 1px;
    min-height: 1px;
    border: none;
}

QToolTip {
    background-color: #ffffff;
    color: #18181b;
    border: 1px solid #e0e1e5;
    border-radius: 6px;
    padding: 5px 9px;
    font-size: 11.5px;
}

QMessageBox {
    background-color: #ffffff;
}

QMessageBox QLabel {
    color: #18181b;
    font-size: 13px;
}
"""
