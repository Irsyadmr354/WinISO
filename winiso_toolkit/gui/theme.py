"""Modern Glassmorphic Dark Theme for PyQt6."""

DARK_THEME_QSS = """
QMainWindow {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}

QWidget {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}

QGroupBox {
    background-color: #1e293b;
    border: 1px solid #334155;
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

QLabel[heading="true"] {
    font-size: 20px;
    font-weight: bold;
    color: #f8fafc;
}

QLineEdit, QComboBox, QListWidget {
    background-color: #1e293b;
    border: 1px solid #475569;
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
    background-color: #334155;
    color: #94a3b8;
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
