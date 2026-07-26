"""WinISO Toolkit — Strict Contrast Theme System with Vector Icons.

Dark Mode: ALL TEXT IS WHITE (#FFFFFF), checkmark is a sharp black check in a white box.
Light Mode: ALL TEXT IS BLACK (#09090B), checkmark is a sharp white check in a black box.
"""

from pathlib import Path

_ASSETS_DIR = Path(__file__).parent / "assets"
_CHECK_DARK = (_ASSETS_DIR / "check_dark.svg").as_posix()
_CHECK_LIGHT = (_ASSETS_DIR / "check_light.svg").as_posix()

DARK_THEME_QSS = f"""
/* ═══════════════════════════════════════════════════════════
   WINISO TOOLKIT — DARK THEME (ALL TEXT = WHITE)
═══════════════════════════════════════════════════════════ */

* {{
    outline: none;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', system-ui, sans-serif;
    font-size: 13px;
    color: #ffffff;
}}

QMainWindow, QWidget {{
    background-color: #09090b;
    color: #ffffff;
    selection-background-color: #27272a;
    selection-color: #ffffff;
}}

QLabel {{
    background-color: transparent;
    color: #ffffff;
}}

/* ── SIDEBAR ──────────────────────────────────────────── */

QFrame#sidebar_root {{
    background-color: #121215;
    border-right: 1px solid #27272a;
}}

QFrame#sidebar_brand {{
    background-color: #121215;
    border-bottom: 1px solid #27272a;
}}

QLabel#brand_app_name {{
    color: #ffffff;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: -0.2px;
}}

QLabel#brand_version {{
    color: #a1a1aa;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
}}

QLabel#sidebar_section_label {{
    color: #a1a1aa;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.2px;
    padding: 0 0 0 4px;
}}

QPushButton#nav_item {{
    background-color: transparent;
    color: #a1a1aa;
    font-size: 12.5px;
    font-weight: 600;
    text-align: left;
    padding: 8px 12px;
    border: 1px solid transparent;
    border-radius: 7px;
}}

QPushButton#nav_item:hover {{
    color: #ffffff;
    background-color: #18181b;
}}

QPushButton#nav_item[active="true"] {{
    background-color: #27272a;
    color: #ffffff;
    border: 1.5px solid #ffffff;
    font-weight: 800;
}}

QPushButton#nav_item[done="true"] {{
    color: #22c55e;
    background-color: transparent;
    font-weight: 600;
}}

QPushButton#nav_item[done="true"]:hover {{
    color: #4ade80;
    background-color: #18181b;
}}

QPushButton#theme_toggle_btn {{
    background-color: #18181b;
    color: #ffffff;
    font-size: 12px;
    font-weight: 600;
    text-align: left;
    padding: 8px 12px;
    border: 1px solid #27272a;
    border-radius: 7px;
}}

QPushButton#theme_toggle_btn:hover {{
    color: #ffffff;
    background-color: #27272a;
    border-color: #3f3f46;
}}

/* ── PAGE HEADER ──────────────────────────────────────── */

QLabel#page_title {{
    color: #ffffff;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.5px;
}}

QLabel#page_subtitle {{
    color: #a1a1aa;
    font-size: 13px;
    font-weight: 500;
}}

/* ── STEP PROGRESS BAR ────────────────────────────────── */

QFrame#step_progress_bar {{
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 10px;
}}

QLabel#step_dot_active {{
    color: #ffffff;
    font-size: 12px;
    font-weight: 800;
}}

QLabel#step_dot_done {{
    color: #22c55e;
    font-size: 12px;
    font-weight: 700;
}}

QLabel#step_dot_pending {{
    color: #a1a1aa;
    font-size: 12px;
    font-weight: 600;
}}

QFrame#step_line_done {{
    background-color: #22c55e;
    max-height: 2px;
    min-height: 2px;
    border: none;
    border-radius: 1px;
}}

QFrame#step_line_pending {{
    background-color: #3f3f46;
    max-height: 2px;
    min-height: 2px;
    border: none;
    border-radius: 1px;
}}

/* ── CARDS ─────────────────────────────────────────────── */

QFrame#card {{
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 10px;
}}

QFrame#card:hover {{
    border-color: #3f3f46;
}}

QFrame#card_elevated {{
    background-color: #27272a;
    border: 1px solid #3f3f46;
    border-radius: 10px;
}}

QFrame#metric_card {{
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
}}

QLabel#metric_label {{
    color: #a1a1aa;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}

QLabel#metric_value {{
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: -0.3px;
}}

QLabel#metric_detail {{
    color: #a1a1aa;
    font-size: 11px;
    font-weight: 500;
}}

/* ── DROPZONE ──────────────────────────────────────────── */

QFrame#dropzone {{
    background-color: #18181b;
    border: 2px dashed #3f3f46;
    border-radius: 12px;
}}

QFrame#dropzone:hover {{
    border-color: #71717a;
    background-color: #27272a;
}}

QFrame#dropzone[drag_over="true"] {{
    border-color: #ffffff;
    border-width: 2px;
    background-color: #27272a;
}}

QLabel#dropzone_icon {{
    color: #ffffff;
    font-size: 38px;
}}

QLabel#dropzone_title {{
    color: #ffffff;
    font-size: 15px;
    font-weight: 700;
}}

QLabel#dropzone_hint {{
    color: #a1a1aa;
    font-size: 12px;
    font-weight: 500;
}}

/* ── BADGES / PILLS ────────────────────────────────────── */

QLabel#badge_success {{
    background-color: #14532d;
    color: #4ade80;
    border: 1px solid #22c55e;
    border-radius: 100px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}}

QLabel#badge_error {{
    background-color: #450a0a;
    color: #fca5a5;
    border: 1px solid #ef4444;
    border-radius: 100px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}}

QLabel#badge_neutral {{
    background-color: #27272a;
    color: #ffffff;
    border: 1px solid #3f3f46;
    border-radius: 100px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}}

QLabel#badge_warning {{
    background-color: #451a03;
    color: #fde68a;
    border: 1px solid #f59e0b;
    border-radius: 100px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}}

/* ── BUTTONS ───────────────────────────────────────────── */

QPushButton#btn_primary {{
    background-color: #27272a;
    color: #ffffff;
    font-weight: 800;
    font-size: 13.5px;
    border: 2px solid #ffffff;
    border-radius: 8px;
    padding: 9px 24px;
    min-height: 24px;
}}

QPushButton#btn_primary:hover {{
    background-color: #3f3f46;
    color: #ffffff;
    border-color: #ffffff;
}}

QPushButton#btn_primary:pressed {{
    background-color: #52525b;
    color: #ffffff;
    border-color: #ffffff;
}}

QPushButton#btn_primary:disabled {{
    background-color: #18181b;
    color: #71717a;
    border: 1px solid #27272a;
}}

QPushButton#btn_secondary {{
    background-color: #18181b;
    color: #ffffff;
    font-weight: 700;
    font-size: 13px;
    border: 1px solid #3f3f46;
    border-radius: 8px;
    padding: 8px 18px;
    min-height: 22px;
}}

QPushButton#btn_secondary:hover {{
    color: #ffffff;
    background-color: #27272a;
    border-color: #71717a;
}}

QPushButton#btn_secondary:pressed {{
    background-color: #3f3f46;
}}

QPushButton#btn_secondary:disabled {{
    color: #71717a;
    border-color: #27272a;
    background-color: #18181b;
}}

QPushButton#btn_ghost {{
    background-color: transparent;
    color: #ffffff;
    font-weight: 600;
    font-size: 12.5px;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 6px 14px;
}}

QPushButton#btn_ghost:hover {{
    color: #ffffff;
    background-color: #18181b;
    border-color: #3f3f46;
}}

QPushButton#btn_danger {{
    background-color: #450a0a;
    color: #fca5a5;
    font-weight: 700;
    font-size: 13px;
    border: 1px solid #ef4444;
    border-radius: 8px;
    padding: 8px 18px;
    min-height: 22px;
}}

QPushButton#btn_danger:hover {{
    background-color: #7f1d1d;
    color: #ffffff;
}}

/* ── FORM INPUTS ───────────────────────────────────────── */

QLineEdit {{
    background-color: #18181b;
    border: 1px solid #3f3f46;
    border-radius: 8px;
    padding: 8px 12px;
    color: #ffffff;
    font-size: 13px;
    min-height: 24px;
}}

QLineEdit:hover {{
    border-color: #71717a;
}}

QLineEdit:focus {{
    border-color: #ffffff;
    background-color: #18181b;
}}

QLineEdit::placeholder {{
    color: #71717a;
}}

QComboBox {{
    background-color: #18181b;
    border: 1px solid #3f3f46;
    border-radius: 8px;
    padding: 8px 12px;
    color: #ffffff;
    font-size: 13px;
    min-height: 24px;
}}

QComboBox:hover {{
    border-color: #71717a;
}}

QComboBox:focus {{
    border-color: #ffffff;
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
    padding-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: #18181b;
    border: 1px solid #3f3f46;
    border-radius: 8px;
    padding: 4px;
    color: #ffffff;
    outline: none;
    selection-background-color: #27272a;
}}

/* ── LIST WIDGET ───────────────────────────────────────── */

QListWidget {{
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 10px;
    padding: 6px;
    color: #ffffff;
    outline: none;
}}

QListWidget::item {{
    background-color: #27272a;
    border: 1px solid #3f3f46;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 3px 2px;
    color: #ffffff;
    font-size: 13px;
}}

QListWidget::item:hover {{
    border-color: #71717a;
    background-color: #3f3f46;
}}

QListWidget::item:selected {{
    background-color: #3f3f46;
    border: 1.5px solid #ffffff;
    color: #ffffff;
    font-weight: 700;
}}

/* ── GROUP BOX ─────────────────────────────────────────── */

QGroupBox {{
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 10px;
    margin-top: 8px;
    padding: 20px 16px 14px 16px;
    font-weight: 700;
    font-size: 13px;
    color: #ffffff;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    background-color: #18181b;
    color: #ffffff;
    font-size: 12px;
    font-weight: 700;
}}

/* ── CHECKBOXES (WITH VECTOR CHECKMARK ICON) ────────────── */

QCheckBox {{
    color: #ffffff;
    font-size: 13px;
    font-weight: 500;
    spacing: 10px;
    background-color: transparent;
}}

QCheckBox:hover {{
    color: #ffffff;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid #71717a;
    background-color: #18181b;
}}

QCheckBox::indicator:hover {{
    border-color: #ffffff;
}}

QCheckBox::indicator:checked {{
    background-color: #ffffff;
    border: 1.5px solid #ffffff;
    image: url("{_CHECK_DARK}");
}}

/* ── PROGRESS BAR ──────────────────────────────────────── */

QProgressBar {{
    border: 1px solid #27272a;
    border-radius: 6px;
    text-align: center;
    background-color: #18181b;
    color: #ffffff;
    font-weight: 700;
    font-size: 11px;
    min-height: 12px;
    max-height: 12px;
}}

QProgressBar::chunk {{
    background-color: #ffffff;
    border-radius: 5px;
}}

/* ── CONSOLE ───────────────────────────────────────────── */

QFrame#console_container {{
    background-color: #121215;
    border-top: 1px solid #27272a;
}}

QTextEdit#console_output {{
    background-color: #000000;
    color: #e4e4e7;
    font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
    font-size: 11.5px;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: #27272a;
}}

QPushButton#console_btn {{
    background-color: transparent;
    color: #a1a1aa;
    font-size: 12px;
    font-weight: 600;
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
}}

QPushButton#console_btn:hover {{
    color: #ffffff;
    background-color: #18181b;
}}

/* ── SCROLLBARS ────────────────────────────────────────── */

QScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 2px 0;
}}

QScrollBar::handle:vertical {{
    background: #27272a;
    border-radius: 3px;
    min-height: 40px;
}}

QScrollBar::handle:vertical:hover {{
    background: #3f3f46;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    border-radius: 3px;
}}

QScrollBar::handle:horizontal {{
    background: #27272a;
    border-radius: 3px;
    min-width: 40px;
}}

/* ── SEPARATORS & TOOLTIPS ─────────────────────────────── */

QFrame#separator {{
    background-color: #27272a;
    max-height: 1px;
    min-height: 1px;
    border: none;
}}

QToolTip {{
    background-color: #18181b;
    color: #ffffff;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

QMessageBox {{
    background-color: #18181b;
}}

QMessageBox QLabel {{
    color: #ffffff;
    font-size: 13px;
}}
"""


LIGHT_THEME_QSS = f"""
/* ═══════════════════════════════════════════════════════════
   WINISO TOOLKIT — LIGHT THEME (ALL TEXT = BLACK)
═══════════════════════════════════════════════════════════ */

* {{
    outline: none;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', system-ui, sans-serif;
    font-size: 13px;
    color: #09090b;
}}

QMainWindow, QWidget {{
    background-color: #ffffff;
    color: #09090b;
    selection-background-color: #e4e4e7;
    selection-color: #09090b;
}}

QLabel {{
    background-color: transparent;
    color: #09090b;
}}

/* ── SIDEBAR ──────────────────────────────────────────── */

QFrame#sidebar_root {{
    background-color: #f4f4f5;
    border-right: 1px solid #e4e4e7;
}}

QFrame#sidebar_brand {{
    background-color: #f4f4f5;
    border-bottom: 1px solid #e4e4e7;
}}

QLabel#brand_app_name {{
    color: #09090b;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: -0.2px;
}}

QLabel#brand_version {{
    color: #71717a;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
}}

QLabel#sidebar_section_label {{
    color: #71717a;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.2px;
    padding: 0 0 0 4px;
}}

QPushButton#nav_item {{
    background-color: transparent;
    color: #71717a;
    font-size: 12.5px;
    font-weight: 600;
    text-align: left;
    padding: 8px 12px;
    border: 1px solid transparent;
    border-radius: 7px;
}}

QPushButton#nav_item:hover {{
    color: #09090b;
    background-color: #e4e4e7;
}}

QPushButton#nav_item[active="true"] {{
    background-color: #e4e4e7;
    color: #09090b;
    border: 1.5px solid #09090b;
    font-weight: 800;
}}

QPushButton#nav_item[done="true"] {{
    color: #16a34a;
    background-color: transparent;
    font-weight: 600;
}}

QPushButton#nav_item[done="true"]:hover {{
    color: #15803d;
    background-color: #e4e4e7;
}}

QPushButton#theme_toggle_btn {{
    background-color: #ffffff;
    color: #09090b;
    font-size: 12px;
    font-weight: 600;
    text-align: left;
    padding: 8px 12px;
    border: 1px solid #e4e4e7;
    border-radius: 7px;
}}

QPushButton#theme_toggle_btn:hover {{
    color: #09090b;
    background-color: #f4f4f5;
    border-color: #d4d4d8;
}}

/* ── PAGE HEADER ──────────────────────────────────────── */

QLabel#page_title {{
    color: #09090b;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.5px;
}}

QLabel#page_subtitle {{
    color: #71717a;
    font-size: 13px;
    font-weight: 500;
}}

/* ── STEP PROGRESS BAR ────────────────────────────────── */

QFrame#step_progress_bar {{
    background-color: #f4f4f5;
    border: 1px solid #e4e4e7;
    border-radius: 10px;
}}

QLabel#step_dot_active {{
    color: #09090b;
    font-size: 12px;
    font-weight: 800;
}}

QLabel#step_dot_done {{
    color: #16a34a;
    font-size: 12px;
    font-weight: 700;
}}

QLabel#step_dot_pending {{
    color: #71717a;
    font-size: 12px;
    font-weight: 600;
}}

QFrame#step_line_done {{
    background-color: #16a34a;
    max-height: 2px;
    min-height: 2px;
    border: none;
    border-radius: 1px;
}}

QFrame#step_line_pending {{
    background-color: #d4d4d8;
    max-height: 2px;
    min-height: 2px;
    border: none;
    border-radius: 1px;
}}

/* ── CARDS ─────────────────────────────────────────────── */

QFrame#card {{
    background-color: #f4f4f5;
    border: 1px solid #e4e4e7;
    border-radius: 10px;
}}

QFrame#card:hover {{
    border-color: #d4d4d8;
}}

QFrame#card_elevated {{
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 10px;
}}

QFrame#metric_card {{
    background-color: #f4f4f5;
    border: 1px solid #e4e4e7;
    border-radius: 8px;
}}

QLabel#metric_label {{
    color: #71717a;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}

QLabel#metric_value {{
    color: #09090b;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: -0.3px;
}}

QLabel#metric_detail {{
    color: #71717a;
    font-size: 11px;
    font-weight: 500;
}}

/* ── DROPZONE ──────────────────────────────────────────── */

QFrame#dropzone {{
    background-color: #f4f4f5;
    border: 2px dashed #d4d4d8;
    border-radius: 12px;
}}

QFrame#dropzone:hover {{
    border-color: #a1a1aa;
    background-color: #e4e4e7;
}}

QFrame#dropzone[drag_over="true"] {{
    border-color: #09090b;
    border-width: 2px;
    background-color: #e4e4e7;
}}

QLabel#dropzone_icon {{
    color: #09090b;
    font-size: 38px;
}}

QLabel#dropzone_title {{
    color: #09090b;
    font-size: 15px;
    font-weight: 700;
}}

QLabel#dropzone_hint {{
    color: #71717a;
    font-size: 12px;
    font-weight: 500;
}}

/* ── BADGES / PILLS ────────────────────────────────────── */

QLabel#badge_success {{
    background-color: #dcfce7;
    color: #15803d;
    border: 1px solid #86efac;
    border-radius: 100px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}}

QLabel#badge_error {{
    background-color: #fee2e2;
    color: #b91c1c;
    border: 1px solid #fca5a5;
    border-radius: 100px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}}

QLabel#badge_neutral {{
    background-color: #e4e4e7;
    color: #09090b;
    border: 1px solid #d4d4d8;
    border-radius: 100px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}}

QLabel#badge_warning {{
    background-color: #fef3c7;
    color: #b45309;
    border: 1px solid #fde68a;
    border-radius: 100px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}}

/* ── BUTTONS (ALL TEXT IS BLACK IN LIGHT MODE) ─────────── */

QPushButton#btn_primary {{
    background-color: #e4e4e7;
    color: #09090b;
    font-weight: 800;
    font-size: 13.5px;
    border: 2px solid #09090b;
    border-radius: 8px;
    padding: 9px 24px;
    min-height: 24px;
}}

QPushButton#btn_primary:hover {{
    background-color: #d4d4d8;
    color: #09090b;
    border-color: #09090b;
}}

QPushButton#btn_primary:pressed {{
    background-color: #a1a1aa;
    color: #09090b;
    border-color: #09090b;
}}

QPushButton#btn_primary:disabled {{
    background-color: #f4f4f5;
    color: #71717a;
    border: 1px solid #d4d4d8;
}}

QPushButton#btn_secondary {{
    background-color: #ffffff;
    color: #09090b;
    font-weight: 700;
    font-size: 13px;
    border: 1px solid #d4d4d8;
    border-radius: 8px;
    padding: 8px 18px;
    min-height: 22px;
}}

QPushButton#btn_secondary:hover {{
    color: #09090b;
    background-color: #f4f4f5;
    border-color: #a1a1aa;
}}

QPushButton#btn_secondary:pressed {{
    background-color: #e4e4e7;
}}

QPushButton#btn_secondary:disabled {{
    color: #a1a1aa;
    border-color: #e4e4e7;
    background-color: #f4f4f5;
}}

QPushButton#btn_ghost {{
    background-color: transparent;
    color: #09090b;
    font-weight: 600;
    font-size: 12.5px;
    border: 1px solid #d4d4d8;
    border-radius: 6px;
    padding: 6px 14px;
}}

QPushButton#btn_ghost:hover {{
    color: #09090b;
    background-color: #f4f4f5;
    border-color: #a1a1aa;
}}

QPushButton#btn_danger {{
    background-color: #fee2e2;
    color: #b91c1c;
    font-weight: 700;
    font-size: 13px;
    border: 1px solid #fca5a5;
    border-radius: 8px;
    padding: 8px 18px;
    min-height: 22px;
}}

QPushButton#btn_danger:hover {{
    background-color: #fecaca;
    color: #991b1b;
}}

/* ── FORM INPUTS ───────────────────────────────────────── */

QLineEdit {{
    background-color: #ffffff;
    border: 1px solid #d4d4d8;
    border-radius: 8px;
    padding: 8px 12px;
    color: #09090b;
    font-size: 13px;
    min-height: 24px;
}}

QLineEdit:hover {{
    border-color: #a1a1aa;
}}

QLineEdit:focus {{
    border-color: #09090b;
    background-color: #ffffff;
}}

QLineEdit::placeholder {{
    color: #71717a;
}}

QComboBox {{
    background-color: #ffffff;
    border: 1px solid #d4d4d8;
    border-radius: 8px;
    padding: 8px 12px;
    color: #09090b;
    font-size: 13px;
    min-height: 24px;
}}

QComboBox:hover {{
    border-color: #a1a1aa;
}}

QComboBox:focus {{
    border-color: #09090b;
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
    padding-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: #ffffff;
    border: 1px solid #d4d4d8;
    border-radius: 8px;
    padding: 4px;
    color: #09090b;
    outline: none;
    selection-background-color: #f4f4f5;
}}

/* ── LIST WIDGET ───────────────────────────────────────── */

QListWidget {{
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 10px;
    padding: 6px;
    color: #09090b;
    outline: none;
}}

QListWidget::item {{
    background-color: #f4f4f5;
    border: 1px solid #e4e4e7;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 3px 2px;
    color: #09090b;
    font-size: 13px;
}}

QListWidget::item:hover {{
    border-color: #a1a1aa;
    background-color: #e4e4e7;
}}

QListWidget::item:selected {{
    background-color: #e4e4e7;
    border: 1.5px solid #09090b;
    color: #09090b;
    font-weight: 700;
}}

/* ── GROUP BOX ─────────────────────────────────────────── */

QGroupBox {{
    background-color: #f4f4f5;
    border: 1px solid #e4e4e7;
    border-radius: 10px;
    margin-top: 8px;
    padding: 20px 16px 14px 16px;
    font-weight: 700;
    font-size: 13px;
    color: #09090b;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    background-color: #f4f4f5;
    color: #09090b;
    font-size: 12px;
    font-weight: 700;
}}

/* ── CHECKBOXES (WITH VECTOR CHECKMARK ICON) ────────────── */

QCheckBox {{
    color: #09090b;
    font-size: 13px;
    font-weight: 500;
    spacing: 10px;
    background-color: transparent;
}}

QCheckBox:hover {{
    color: #09090b;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid #a1a1aa;
    background-color: #ffffff;
}}

QCheckBox::indicator:hover {{
    border-color: #09090b;
}}

QCheckBox::indicator:checked {{
    background-color: #09090b;
    border: 1.5px solid #09090b;
    image: url("{_CHECK_LIGHT}");
}}

/* ── PROGRESS BAR ──────────────────────────────────────── */

QProgressBar {{
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    text-align: center;
    background-color: #f4f4f5;
    color: #09090b;
    font-weight: 700;
    font-size: 11px;
    min-height: 12px;
    max-height: 12px;
}}

QProgressBar::chunk {{
    background-color: #09090b;
    border-radius: 5px;
}}

/* ── CONSOLE ───────────────────────────────────────────── */

QFrame#console_container {{
    background-color: #f4f4f5;
    border-top: 1px solid #e4e4e7;
}}

QTextEdit#console_output {{
    background-color: #ffffff;
    color: #09090b;
    font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
    font-size: 11.5px;
    border: 1px solid #e4e4e7;
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: #e4e4e7;
}}

QPushButton#console_btn {{
    background-color: transparent;
    color: #71717a;
    font-size: 12px;
    font-weight: 600;
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
}}

QPushButton#console_btn:hover {{
    color: #09090b;
    background-color: #e4e4e7;
}}

/* ── SCROLLBARS ────────────────────────────────────────── */

QScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 2px 0;
}}

QScrollBar::handle:vertical {{
    background: #e4e4e7;
    border-radius: 3px;
    min-height: 40px;
}}

QScrollBar::handle:vertical:hover {{
    background: #d4d4d8;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    border-radius: 3px;
}}

QScrollBar::handle:horizontal {{
    background: #e4e4e7;
    border-radius: 3px;
    min-width: 40px;
}}

/* ── SEPARATORS & TOOLTIPS ─────────────────────────────── */

QFrame#separator {{
    background-color: #e4e4e7;
    max-height: 1px;
    min-height: 1px;
    border: none;
}}

QToolTip {{
    background-color: #ffffff;
    color: #09090b;
    border: 1px solid #d4d4d8;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

QMessageBox {{
    background-color: #ffffff;
}}

QMessageBox QLabel {{
    color: #09090b;
    font-size: 13px;
}}
"""
