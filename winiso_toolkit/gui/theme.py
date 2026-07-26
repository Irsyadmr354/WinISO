"""WinISO Toolkit — Deep Space Dark Theme with Neon Accents."""

# Accent palette
# --primary:  #3b82f6  (electric blue)
# --success:  #22c55e  (neon green)
# --danger:   #ef4444  (red)
# --warning:  #f59e0b  (amber)
# --info:     #06b6d4  (cyan)
# --surface0: #0a0f1e  (deepest bg)
# --surface1: #0f172a  (card bg)
# --surface2: #1e293b  (elevated card)
# --surface3: #334155  (border / input bg)
# --text:     #f1f5f9
# --muted:    #64748b

DARK_THEME_QSS = """
/* ═══════════════════════════════════════════════
   BASE
═══════════════════════════════════════════════ */
QMainWindow, QDialog {
    background-color: #0a0f1e;
    color: #f1f5f9;
}

QWidget {
    background-color: #0a0f1e;
    color: #f1f5f9;
    font-family: 'Segoe UI', 'Inter', system-ui, -apple-system, sans-serif;
    font-size: 13px;
}

/* ═══════════════════════════════════════════════
   TOP STEP BREADCRUMB BAR
═══════════════════════════════════════════════ */
QFrame#step_bar {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #111827, stop:1 #0a0f1e
    );
    border-bottom: 1px solid #1e293b;
    min-height: 46px;
    max-height: 46px;
}

QLabel[step_item="true"] {
    color: #475569;
    font-weight: 600;
    font-size: 11px;
    padding: 5px 9px;
    border-radius: 14px;
    letter-spacing: 0.3px;
}

QLabel[step_active="true"] {
    color: #f1f5f9;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #1d4ed8, stop:1 #2563eb
    );
    border-radius: 14px;
    font-weight: 700;
    padding: 5px 11px;
}

QLabel[step_done="true"] {
    color: #22c55e;
    font-weight: 600;
}

/* ═══════════════════════════════════════════════
   GLASSMORPHISM CARDS
═══════════════════════════════════════════════ */
QFrame#card_frame {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #111827, stop:1 #0f172a
    );
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 16px;
}

QFrame#card_frame:hover {
    border: 1px solid #334155;
}

QFrame#info_row {
    background-color: #0f172a;
    border-bottom: 1px solid #1e293b;
    padding: 6px 10px;
    border-radius: 0px;
}

/* ═══════════════════════════════════════════════
   STATUS BADGES
═══════════════════════════════════════════════ */
QLabel[badge="success"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #064e3b, stop:1 #065f46);
    color: #4ade80;
    border: 1px solid #22c55e;
    border-radius: 20px;
    padding: 5px 14px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
}

QLabel[badge="danger"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #7f1d1d, stop:1 #991b1b);
    color: #fca5a5;
    border: 1px solid #ef4444;
    border-radius: 20px;
    padding: 5px 14px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
}

QLabel[badge="info"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #0c4a6e, stop:1 #075985);
    color: #7dd3fc;
    border: 1px solid #0284c7;
    border-radius: 20px;
    padding: 5px 14px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
}

QLabel[badge="warning"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #78350f, stop:1 #92400e);
    color: #fde68a;
    border: 1px solid #f59e0b;
    border-radius: 20px;
    padding: 5px 14px;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 0.5px;
}

/* ═══════════════════════════════════════════════
   GROUP BOXES
═══════════════════════════════════════════════ */
QGroupBox {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 16px;
    font-weight: 700;
    font-size: 12px;
    color: #38bdf8;
    letter-spacing: 0.4px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: #38bdf8;
    font-size: 12px;
}

/* ═══════════════════════════════════════════════
   LABELS
═══════════════════════════════════════════════ */
QLabel {
    color: #cbd5e1;
    font-size: 13px;
    background: transparent;
}

QLabel[heading="true"] {
    color: #f1f5f9;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.3px;
}

QLabel[subheading="true"] {
    color: #94a3b8;
    font-size: 13px;
}

QLabel[key="true"] {
    color: #64748b;
    font-size: 12px;
    font-weight: 600;
}

QLabel[value="true"] {
    color: #e2e8f0;
    font-size: 12px;
}

QLabel[stat_value="true"] {
    color: #38bdf8;
    font-size: 16px;
    font-weight: 700;
}

/* ═══════════════════════════════════════════════
   INPUTS
═══════════════════════════════════════════════ */
QLineEdit, QComboBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    color: #f1f5f9;
    selection-background-color: #2563eb;
    min-height: 20px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #3b82f6;
    background-color: #1e3a5f;
}

QLineEdit:hover, QComboBox:hover {
    border: 1px solid #475569;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    selection-background-color: #2563eb;
    color: #f1f5f9;
    padding: 4px;
}

/* ═══════════════════════════════════════════════
   LIST WIDGET (edition selector)
═══════════════════════════════════════════════ */
QListWidget {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 6px;
    color: #f1f5f9;
    outline: none;
}

QListWidget::item {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 3px 2px;
    color: #e2e8f0;
}

QListWidget::item:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #1d4ed8, stop:1 #2563eb);
    border: 1px solid #3b82f6;
    color: #f1f5f9;
}

QListWidget::item:hover {
    background-color: #273549;
    border: 1px solid #475569;
}

/* ═══════════════════════════════════════════════
   BUTTONS
═══════════════════════════════════════════════ */
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #3b82f6, stop:1 #2563eb);
    color: #ffffff;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-size: 13px;
    letter-spacing: 0.2px;
    min-height: 20px;
}

QPushButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #60a5fa, stop:1 #3b82f6);
}

QPushButton:pressed {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #1d4ed8, stop:1 #1e40af);
    padding-top: 10px;
    padding-bottom: 8px;
}

QPushButton:disabled {
    background-color: #1e293b;
    color: #475569;
    border: 1px solid #334155;
}

QPushButton[secondary="true"] {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #334155, stop:1 #1e293b);
    color: #cbd5e1;
    border: 1px solid #475569;
}

QPushButton[secondary="true"]:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #475569, stop:1 #334155);
    color: #f1f5f9;
}

QPushButton[danger="true"] {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #ef4444, stop:1 #dc2626);
    color: #ffffff;
}

QPushButton[danger="true"]:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #f87171, stop:1 #ef4444);
}

QPushButton[success="true"] {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #22c55e, stop:1 #16a34a);
    color: #ffffff;
}

/* ═══════════════════════════════════════════════
   PROGRESS BAR
═══════════════════════════════════════════════ */
QProgressBar {
    border: 1px solid #1e293b;
    border-radius: 8px;
    text-align: center;
    background-color: #0f172a;
    color: #f1f5f9;
    font-weight: 700;
    font-size: 12px;
    min-height: 24px;
    max-height: 24px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #1d4ed8,
        stop:0.4 #2563eb,
        stop:0.7 #06b6d4,
        stop:1 #22d3ee);
    border-radius: 7px;
}

/* ═══════════════════════════════════════════════
   LIVE TERMINAL CONSOLE
═══════════════════════════════════════════════ */
QTextEdit#live_log_console {
    background-color: #020817;
    color: #22d3ee;
    font-family: 'Cascadia Code', 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
    font-size: 11.5px;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 10px;
    selection-background-color: #1d4ed8;
}

/* ═══════════════════════════════════════════════
   CHECKBOXES
═══════════════════════════════════════════════ */
QCheckBox {
    color: #cbd5e1;
    font-size: 13px;
    spacing: 10px;
    background: transparent;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1.5px solid #475569;
    background-color: #1e293b;
}

QCheckBox::indicator:hover {
    border-color: #3b82f6;
    background-color: #1e3a5f;
}

QCheckBox::indicator:checked {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #2563eb, stop:1 #1d4ed8);
    border-color: #3b82f6;
}

/* ═══════════════════════════════════════════════
   SCROLL BARS
═══════════════════════════════════════════════ */
QScrollBar:vertical {
    background: #0f172a;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #334155;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #0f172a;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #334155;
    border-radius: 4px;
    min-width: 30px;
}

/* ═══════════════════════════════════════════════
   SEPARATOR
═══════════════════════════════════════════════ */
QFrame[frameShape="4"], QFrame[frameShape="HLine"] {
    color: #1e293b;
    background-color: #1e293b;
    max-height: 1px;
}

/* ═══════════════════════════════════════════════
   TOOLTIPS
═══════════════════════════════════════════════ */
QToolTip {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 12px;
}

/* ═══════════════════════════════════════════════
   MESSAGE BOX
═══════════════════════════════════════════════ */
QMessageBox {
    background-color: #0f172a;
    color: #f1f5f9;
}

QMessageBox QLabel {
    color: #f1f5f9;
    font-size: 13px;
}
"""
