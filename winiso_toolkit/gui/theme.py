"""WinISO Toolkit — Ultimate Windows 11 Fluent Theme System."""

DARK_THEME_QSS = """
/* ═══════════════════════════════════════════════
   FLUENT DARK THEME (MONOCHROME & CLEAN)
═══════════════════════════════════════════════ */
QMainWindow, QDialog {
    background-color: #09090b;
    color: #fafafa;
}

QWidget {
    background-color: #09090b;
    color: #fafafa;
    font-family: 'Segoe UI Variable', 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 13px;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* ═══════════════════════════════════════════════
   LEFT SIDEBAR NAVIGATION
═══════════════════════════════════════════════ */
QFrame#sidebar {
    background-color: #121215;
    border-right: 1px solid #27272a;
    min-width: 220px;
    max-width: 220px;
}

QFrame#sidebar_brand {
    background: transparent;
    padding: 18px 16px 14px 16px;
    border-bottom: 1px solid #27272a;
}

QLabel#brand_title {
    color: #ffffff;
    font-size: 16px;
    font-weight: 800;
    letter-spacing: -0.3px;
    background: transparent;
}

QLabel#brand_subtitle {
    color: #a1a1aa;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    background: transparent;
}

QLabel[sidebar_item="true"] {
    color: #a1a1aa;
    font-weight: 600;
    font-size: 12.5px;
    padding: 9px 14px;
    border-radius: 8px;
    margin: 2px 10px;
    background-color: transparent;
}

QLabel[sidebar_item="true"]:hover {
    color: #ffffff;
    background-color: #18181b;
}

QLabel[sidebar_active="true"] {
    color: #09090b;
    background-color: #ffffff;
    border: 1px solid #ffffff;
    border-radius: 8px;
    font-weight: 700;
    padding: 9px 14px;
    margin: 2px 10px;
}

QLabel[sidebar_done="true"] {
    color: #22c55e;
    font-weight: 600;
}

/* ═══════════════════════════════════════════════
   CARDS & DROPZONE
═══════════════════════════════════════════════ */
QFrame#card_frame {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 12px;
    padding: 16px;
}

QFrame#card_frame:hover {
    border-color: #3f3f46;
}

QFrame#drop_area {
    background-color: #18181b;
    border: 2px dashed #3f3f46;
    border-radius: 14px;
    padding: 20px;
    min-height: 190px;
}

QFrame#drop_area[drag_active="true"] {
    border: 2px dashed #ffffff;
    background-color: #27272a;
}

QFrame#drop_area:hover {
    border-color: #71717a;
}

/* ═══════════════════════════════════════════════
   BADGES & METRICS
═══════════════════════════════════════════════ */
QLabel[badge="success"] {
    background-color: #14532d;
    color: #4ade80;
    border: 1px solid #22c55e;
    border-radius: 6px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}

QLabel[badge="danger"] {
    background-color: #450a0a;
    color: #fca5a5;
    border: 1px solid #ef4444;
    border-radius: 6px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}

QLabel[badge="info"] {
    background-color: #27272a;
    color: #fafafa;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}

QLabel[badge="warning"] {
    background-color: #451a03;
    color: #fde68a;
    border: 1px solid #f59e0b;
    border-radius: 6px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}

/* ═══════════════════════════════════════════════
   GROUP BOXES & TYPOGRAPHY
═══════════════════════════════════════════════ */
QGroupBox {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 18px;
    font-weight: 700;
    font-size: 13px;
    color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 2px 8px;
    background-color: #18181b;
    color: #ffffff;
    font-size: 12px;
    font-weight: 700;
}

QLabel[heading="true"] {
    color: #ffffff;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.4px;
    background: transparent;
}

QLabel[subheading="true"] {
    color: #a1a1aa;
    font-size: 12.5px;
    background: transparent;
}

/* ═══════════════════════════════════════════════
   FORM INPUTS & COMBOS
═══════════════════════════════════════════════ */
QLineEdit, QComboBox {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 8px 12px;
    color: #ffffff;
    selection-background-color: #3f3f46;
    min-height: 24px;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1.5px solid #ffffff;
    background-color: #18181b;
}

QLineEdit:hover, QComboBox:hover {
    border: 1px solid #3f3f46;
}

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox QAbstractItemView {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    selection-background-color: #27272a;
    color: #ffffff;
    padding: 6px;
    outline: none;
}

/* ═══════════════════════════════════════════════
   LIST WIDGET
═══════════════════════════════════════════════ */
QListWidget {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 10px;
    padding: 6px;
    color: #ffffff;
    outline: none;
    min-height: 180px;
}

QListWidget::item {
    background-color: #27272a;
    border: 1px solid #3f3f46;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 3px 2px;
    color: #fafafa;
}

QListWidget::item:selected {
    background-color: #ffffff;
    border: 1px solid #ffffff;
    color: #09090b;
    font-weight: 700;
}

QListWidget::item:hover {
    border-color: #71717a;
}

/* ═══════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════ */
QPushButton {
    background-color: #ffffff;
    color: #09090b;
    font-weight: 700;
    border: 1px solid #ffffff;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 13px;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #e4e4e7;
    border-color: #e4e4e7;
}

QPushButton:pressed {
    background-color: #d4d4d8;
    border-color: #d4d4d8;
}

QPushButton:disabled {
    background-color: #27272a;
    color: #71717a;
    border: 1px solid #27272a;
}

QPushButton[secondary="true"] {
    background-color: #18181b;
    color: #ffffff;
    border: 1px solid #27272a;
}

QPushButton[secondary="true"]:hover {
    background-color: #27272a;
    border-color: #3f3f46;
}

/* ═══════════════════════════════════════════════
   PROGRESS BAR
═══════════════════════════════════════════════ */
QProgressBar {
    border: 1px solid #27272a;
    border-radius: 8px;
    text-align: center;
    background-color: #18181b;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
    min-height: 24px;
    max-height: 24px;
}

QProgressBar::chunk {
    background-color: #ffffff;
    border-radius: 7px;
}

/* ═══════════════════════════════════════════════
   LIVE TERMINAL CONSOLE
═══════════════════════════════════════════════ */
QTextEdit#live_log_console {
    background-color: #000000;
    color: #e4e4e7;
    font-family: 'Cascadia Code', 'Consolas', 'JetBrains Mono', monospace;
    font-size: 11.5px;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 10px;
    selection-background-color: #27272a;
}

/* ═══════════════════════════════════════════════
   CHECKBOXES & RADIOS
═══════════════════════════════════════════════ */
QCheckBox {
    color: #fafafa;
    font-size: 13px;
    spacing: 10px;
    background: transparent;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid #3f3f46;
    background-color: #18181b;
}

QCheckBox::indicator:hover {
    border-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #ffffff;
    border-color: #ffffff;
}

/* ═══════════════════════════════════════════════
   SLEEK SCROLL BARS
═══════════════════════════════════════════════ */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #27272a;
    border-radius: 3px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #3f3f46;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal {
    background: #27272a;
    border-radius: 3px;
    min-width: 30px;
}

QFrame[frameShape="4"], QFrame[frameShape="HLine"] {
    color: #27272a;
    background-color: #27272a;
    max-height: 1px;
}

QToolTip {
    background-color: #18181b;
    color: #ffffff;
    border: 1px solid #3f3f46;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

QMessageBox {
    background-color: #18181b;
    color: #ffffff;
}

QMessageBox QLabel {
    color: #ffffff;
    font-size: 13px;
}
"""


LIGHT_THEME_QSS = """
/* ═══════════════════════════════════════════════
   FLUENT LIGHT THEME (MONOCHROME & CLEAN)
═══════════════════════════════════════════════ */
QMainWindow, QDialog {
    background-color: #ffffff;
    color: #09090b;
}

QWidget {
    background-color: #ffffff;
    color: #09090b;
    font-family: 'Segoe UI Variable', 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 13px;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* ═══════════════════════════════════════════════
   LEFT SIDEBAR NAVIGATION
═══════════════════════════════════════════════ */
QFrame#sidebar {
    background-color: #f4f4f5;
    border-right: 1px solid #e4e4e7;
    min-width: 220px;
    max-width: 220px;
}

QFrame#sidebar_brand {
    background: transparent;
    padding: 18px 16px 14px 16px;
    border-bottom: 1px solid #e4e4e7;
}

QLabel#brand_title {
    color: #09090b;
    font-size: 16px;
    font-weight: 800;
    letter-spacing: -0.3px;
    background: transparent;
}

QLabel#brand_subtitle {
    color: #71717a;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    background: transparent;
}

QLabel[sidebar_item="true"] {
    color: #71717a;
    font-weight: 600;
    font-size: 12.5px;
    padding: 9px 14px;
    border-radius: 8px;
    margin: 2px 10px;
    background-color: transparent;
}

QLabel[sidebar_item="true"]:hover {
    color: #09090b;
    background-color: #e4e4e7;
}

QLabel[sidebar_active="true"] {
    color: #ffffff;
    background-color: #09090b;
    border: 1px solid #09090b;
    border-radius: 8px;
    font-weight: 700;
    padding: 9px 14px;
    margin: 2px 10px;
}

QLabel[sidebar_done="true"] {
    color: #16a34a;
    font-weight: 600;
}

/* ═══════════════════════════════════════════════
   CARDS & DROPZONE
═══════════════════════════════════════════════ */
QFrame#card_frame {
    background-color: #f4f4f5;
    border: 1px solid #e4e4e7;
    border-radius: 12px;
    padding: 16px;
}

QFrame#card_frame:hover {
    border-color: #d4d4d8;
}

QFrame#drop_area {
    background-color: #f4f4f5;
    border: 2px dashed #d4d4d8;
    border-radius: 14px;
    padding: 20px;
    min-height: 190px;
}

QFrame#drop_area[drag_active="true"] {
    border: 2px dashed #09090b;
    background-color: #e4e4e7;
}

QFrame#drop_area:hover {
    border-color: #a1a1aa;
}

/* ═══════════════════════════════════════════════
   BADGES & METRICS
═══════════════════════════════════════════════ */
QLabel[badge="success"] {
    background-color: #dcfce7;
    color: #15803d;
    border: 1px solid #86efac;
    border-radius: 6px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}

QLabel[badge="danger"] {
    background-color: #fee2e2;
    color: #b91c1c;
    border: 1px solid #fca5a5;
    border-radius: 6px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}

QLabel[badge="info"] {
    background-color: #e4e4e7;
    color: #09090b;
    border: 1px solid #d4d4d8;
    border-radius: 6px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}

QLabel[badge="warning"] {
    background-color: #fef3c7;
    color: #b45309;
    border: 1px solid #fde68a;
    border-radius: 6px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}

/* ═══════════════════════════════════════════════
   GROUP BOXES & TYPOGRAPHY
═══════════════════════════════════════════════ */
QGroupBox {
    background-color: #f4f4f5;
    border: 1px solid #e4e4e7;
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 18px;
    font-weight: 700;
    font-size: 13px;
    color: #09090b;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 2px 8px;
    background-color: #f4f4f5;
    color: #09090b;
    font-size: 12px;
    font-weight: 700;
}

QLabel[heading="true"] {
    color: #09090b;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.4px;
    background: transparent;
}

QLabel[subheading="true"] {
    color: #71717a;
    font-size: 12.5px;
    background: transparent;
}

/* ═══════════════════════════════════════════════
   FORM INPUTS & COMBOS
═══════════════════════════════════════════════ */
QLineEdit, QComboBox {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 8px;
    padding: 8px 12px;
    color: #09090b;
    selection-background-color: #e4e4e7;
    min-height: 24px;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1.5px solid #09090b;
    background-color: #ffffff;
}

QLineEdit:hover, QComboBox:hover {
    border: 1px solid #d4d4d8;
}

QComboBox::drop-down {
    border: none;
    width: 28px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 8px;
    selection-background-color: #f4f4f5;
    color: #09090b;
    padding: 6px;
    outline: none;
}

/* ═══════════════════════════════════════════════
   LIST WIDGET
═══════════════════════════════════════════════ */
QListWidget {
    background-color: #f4f4f5;
    border: 1px solid #e4e4e7;
    border-radius: 10px;
    padding: 6px;
    color: #09090b;
    outline: none;
    min-height: 180px;
}

QListWidget::item {
    background-color: #ffffff;
    border: 1px solid #e4e4e7;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 3px 2px;
    color: #09090b;
}

QListWidget::item:selected {
    background-color: #09090b;
    border: 1px solid #09090b;
    color: #ffffff;
    font-weight: 700;
}

QListWidget::item:hover {
    border-color: #a1a1aa;
}

/* ═══════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════ */
QPushButton {
    background-color: #09090b;
    color: #ffffff;
    font-weight: 700;
    border: 1px solid #09090b;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 13px;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #27272a;
    border-color: #27272a;
}

QPushButton:pressed {
    background-color: #3f3f46;
    border-color: #3f3f46;
}

QPushButton:disabled {
    background-color: #e4e4e7;
    color: #a1a1aa;
    border: 1px solid #e4e4e7;
}

QPushButton[secondary="true"] {
    background-color: #ffffff;
    color: #09090b;
    border: 1px solid #e4e4e7;
}

QPushButton[secondary="true"]:hover {
    background-color: #f4f4f5;
    border-color: #d4d4d8;
}

/* ═══════════════════════════════════════════════
   PROGRESS BAR
═══════════════════════════════════════════════ */
QProgressBar {
    border: 1px solid #e4e4e7;
    border-radius: 8px;
    text-align: center;
    background-color: #f4f4f5;
    color: #09090b;
    font-weight: 700;
    font-size: 12px;
    min-height: 24px;
    max-height: 24px;
}

QProgressBar::chunk {
    background-color: #09090b;
    border-radius: 7px;
}

/* ═══════════════════════════════════════════════
   LIVE TERMINAL CONSOLE
═══════════════════════════════════════════════ */
QTextEdit#live_log_console {
    background-color: #f4f4f5;
    color: #09090b;
    font-family: 'Cascadia Code', 'Consolas', 'JetBrains Mono', monospace;
    font-size: 11.5px;
    border: 1px solid #e4e4e7;
    border-radius: 8px;
    padding: 10px;
    selection-background-color: #e4e4e7;
}

/* ═══════════════════════════════════════════════
   CHECKBOXES & RADIOS
═══════════════════════════════════════════════ */
QCheckBox {
    color: #09090b;
    font-size: 13px;
    spacing: 10px;
    background: transparent;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid #d4d4d8;
    background-color: #ffffff;
}

QCheckBox::indicator:hover {
    border-color: #09090b;
}

QCheckBox::indicator:checked {
    background-color: #09090b;
    border-color: #09090b;
}

/* ═══════════════════════════════════════════════
   SLEEK SCROLL BARS
═══════════════════════════════════════════════ */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #e4e4e7;
    border-radius: 3px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #d4d4d8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal {
    background: #e4e4e7;
    border-radius: 3px;
    min-width: 30px;
}

QFrame[frameShape="4"], QFrame[frameShape="HLine"] {
    color: #e4e4e7;
    background-color: #e4e4e7;
    max-height: 1px;
}

QToolTip {
    background-color: #ffffff;
    color: #09090b;
    border: 1px solid #d4d4d8;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

QMessageBox {
    background-color: #ffffff;
    color: #09090b;
}

QMessageBox QLabel {
    color: #09090b;
    font-size: 13px;
}
"""
