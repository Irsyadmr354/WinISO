"""Modern Glassmorphic Dark Theme with Live Console & Badge Styling."""

DARK_THEME_QSS = """
QMainWindow {
    background-color: #0b1329;
    color: #f8fafc;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}

QWidget {
    background-color: #0b1329;
    color: #f8fafc;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}

/* --- Top Step Breadcrumb Bar --- */
QFrame#step_bar {
    background-color: #111c38;
    border-bottom: 1px solid #1e293b;
    padding: 6px 12px;
}

QLabel[step_item="true"] {
    color: #64748b;
    font-weight: 600;
    font-size: 12px;
    padding: 4px 8px;
    border-radius: 4px;
}

QLabel[step_active="true"] {
    color: #38bdf8;
    background-color: #0369a1;
    font-weight: bold;
}

QLabel[step_done="true"] {
    color: #34d399;
}

/* --- Glassmorphism Card Panels --- */
QFrame#card_frame {
    background-color: #111c38;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 14px;
}

/* --- Status Badges --- */
QLabel[badge="success"] {
    background-color: #065f46;
    color: #34d399;
    border: 1px solid #10b981;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: bold;
    font-size: 11px;
}

QLabel[badge="danger"] {
    background-color: #991b1b;
    color: #fca5a5;
    border: 1px solid #ef4444;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: bold;
    font-size: 11px;
}

QLabel[badge="info"] {
    background-color: #075985;
    color: #7dd3fc;
    border: 1px solid #0284c7;
    border-radius: 12px;
    padding: 4px 12px;
    font-weight: bold;
    font-size: 11px;
}

QGroupBox {
    background-color: #111c38;
    border: 1px solid #1e293b;
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: bold;
    color: #38bdf8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #38bdf8;
}

QLabel {
    color: #e2e8f0;
    font-size: 13px;
}

QLineEdit, QComboBox, QListWidget {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
    color: #f8fafc;
    selection-background-color: #0284c7;
}

QLineEdit:focus, QComboBox:focus, QListWidget:focus {
    border: 1px solid #38bdf8;
}

QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #3b82f6;
}

QPushButton:pressed {
    background-color: #1d4ed8;
}

QPushButton:disabled {
    background-color: #1e293b;
    color: #64748b;
}

QPushButton[secondary="true"] {
    background-color: #334155;
    color: #f8fafc;
}

QPushButton[secondary="true"]:hover {
    background-color: #475569;
}

QProgressBar {
    border: 1px solid #334155;
    border-radius: 6px;
    text-align: center;
    background-color: #1e293b;
    color: #f8fafc;
    font-weight: bold;
    height: 22px;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
    border-radius: 5px;
}

/* --- Embedded Live Terminal Console --- */
QTextEdit#live_log_console {
    background-color: #040814;
    color: #38bdf8;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 8px;
}

QCheckBox {
    color: #e2e8f0;
    font-size: 13px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #475569;
    background-color: #1e293b;
}

QCheckBox::indicator:checked {
    background-color: #0284c7;
    border-color: #38bdf8;
}
"""
