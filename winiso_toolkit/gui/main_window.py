"""WinISO Toolkit — Premium Desktop Application GUI.

Fully-new architecture inspired by Linear, Vercel Dashboard, and Raycast.
Features: Horizontal Step Progress Bar, Layered Card System,
Collapsible Terminal Drawer, Animated Page Transitions.
"""

from __future__ import annotations

import logging
import re
import sys
import time
from pathlib import Path

from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    Qt,
    QThread,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from winiso_toolkit.deps.installer import DependencyInstaller
from winiso_toolkit.gui.theme import DARK_THEME_QSS, LIGHT_THEME_QSS
from winiso_toolkit.iso.analyzer import ISOAnalyzer, ISOInfo, WIMImageInfo
from winiso_toolkit.pipeline import WinISOPipeline
from winiso_toolkit.usb.creator import BootMode, USBCreator
from winiso_toolkit.usb.detector import USBDevice, USBDetector


# ═══════════════════════════════════════════════════════════
# DESIGN SYSTEM — Reusable UI Primitives
# ═══════════════════════════════════════════════════════════

def _fmt_gb(n: int) -> str:
    return f"{n / (1024 ** 3):.2f} GB"


def _sep() -> QFrame:
    """Thin 1px separator line."""
    f = QFrame()
    f.setObjectName("separator")
    f.setFixedHeight(1)
    return f


def _text(
    content: str = "",
    *,
    size: int = 13,
    weight: int = 400,
    color: str = "",
    mono: bool = False,
) -> QLabel:
    """Typography primitive with explicit font control."""
    lbl = QLabel(content)
    parts = ["background:transparent;"]
    parts.append(f"font-size:{size}px;")
    parts.append(f"font-weight:{weight};")
    if color:
        parts.append(f"color:{color};")
    if mono:
        parts.append("font-family:'Cascadia Code','JetBrains Mono','Consolas',monospace;")
    lbl.setStyleSheet(" ".join(parts))
    return lbl


def _card(object_name: str = "card") -> QFrame:
    """Surface card with configurable depth."""
    f = QFrame()
    f.setObjectName(object_name)
    return f


def _badge(text: str, kind: str = "neutral") -> QLabel:
    """Pill-shaped status badge."""
    lbl = QLabel(text)
    lbl.setObjectName(f"badge_{kind}")
    return lbl


def _btn(text: str, variant: str = "primary") -> QPushButton:
    """Button with variant styling."""
    btn = QPushButton(text)
    btn.setObjectName(f"btn_{variant}")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
    return btn


def _fade_in(widget: QWidget, ms: int = 250) -> None:
    """Smooth opacity fade-in animation."""
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)


class _MetricCard(QFrame):
    """Individual KPI metric card used in dashboards and stat grids."""

    def __init__(self, label: str, value: str = "—", detail: str = "") -> None:
        super().__init__()
        self.setObjectName("metric_card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self._label = QLabel(label)
        self._label.setObjectName("metric_label")

        self._value = QLabel(value)
        self._value.setObjectName("metric_value")
        self._value.setWordWrap(True)

        self._detail = QLabel(detail)
        self._detail.setObjectName("metric_detail")
        self._detail.setWordWrap(True)
        self._detail.setVisible(bool(detail))

        layout.addWidget(self._label)
        layout.addWidget(self._value)
        layout.addWidget(self._detail)

    def set_value(self, value: str, detail: str = "") -> None:
        self._value.setText(value)
        if detail:
            self._detail.setText(detail)
            self._detail.setVisible(True)
        else:
            self._detail.setVisible(False)


# ═══════════════════════════════════════════════════════════
# BACKGROUND WORKERS (unchanged business logic)
# ═══════════════════════════════════════════════════════════

class _LogBridge(QThread):
    new_log = pyqtSignal(str)
    def run(self) -> None:
        pass


class QObjectLogHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self._bridge = _LogBridge()

    @property
    def new_log(self) -> pyqtSignal:
        return self._bridge.new_log  # type: ignore[return-value]

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            ts = time.strftime("%H:%M:%S", time.localtime(record.created))
            colors = {
                "INFO": "#3b82f6", "WARNING": "#f59e0b",
                "ERROR": "#ef4444", "DEBUG": "#71717a",
            }
            c = colors.get(record.levelname, "#a1a1aa")
            html = (
                f"<span style='color:#52525b'>{ts}</span>&nbsp;&nbsp;"
                f"<span style='color:{c};font-weight:600'>{record.levelname}</span>&nbsp;&nbsp;"
                f"<span>{msg}</span>"
            )
            self._bridge.new_log.emit(html)
        except (OSError, RuntimeError):
            pass


class WorkerThread(QThread):
    progress = pyqtSignal(float, str)
    finished_ok = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, fn: object, *args: object, **kwargs: object) -> None:
        super().__init__()
        self._fn, self._args, self._kwargs = fn, args, kwargs

    def run(self) -> None:
        try:
            result = self._fn(  # type: ignore[operator]
                *self._args,
                progress=lambda p, m: self.progress.emit(p, m),
                **self._kwargs,
            )
            self.finished_ok.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class ISOAnalyzeWorker(QThread):
    finished_ok = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path

    def run(self) -> None:
        try:
            self.finished_ok.emit(ISOAnalyzer(DependencyInstaller()).analyze(self.path))
        except Exception as exc:
            self.failed.emit(str(exc))


class WimlibInstallWorker(QThread):
    log_line = pyqtSignal(str)
    finished_ok = pyqtSignal(bool)
    failed = pyqtSignal(str)

    def run(self) -> None:
        try:
            ok = DependencyInstaller().install_missing(
                confirm=True,
                progress_callback=lambda m: self.log_line.emit(m),
            )
            self.finished_ok.emit(ok)
        except Exception as exc:
            self.failed.emit(str(exc))


class SHA256VerifyWorker(QThread):
    progress = pyqtSignal(float, str)
    finished_ok = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path

    def run(self) -> None:
        try:
            from winiso_toolkit.iso.verifier import ISOVerifier
            result = ISOVerifier().verify_iso(
                self.path,
                progress_callback=lambda p, m: self.progress.emit(p, m),
            )
            self.finished_ok.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


# ═══════════════════════════════════════════════════════════
# HORIZONTAL STEP PROGRESS BAR
# ═══════════════════════════════════════════════════════════

class StepProgressBar(QFrame):
    """Connected dot-and-line wizard progress indicator."""

    LABELS = ["Source", "Editions", "Tweaks", "Compress", "USB", "Review", "Build", "Done"]

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("step_progress_bar")
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        self._dots: list[QLabel] = []
        self._lines: list[QFrame] = []

        for i, label in enumerate(self.LABELS):
            dot = QLabel(f"  {i + 1}. {label}")
            dot.setObjectName("step_dot_pending")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._dots.append(dot)
            layout.addWidget(dot)

            if i < len(self.LABELS) - 1:
                line = QFrame()
                line.setObjectName("step_line_pending")
                line.setFixedHeight(2)
                line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                self._lines.append(line)
                layout.addWidget(line)

    def set_step(self, active: int) -> None:
        for i, dot in enumerate(self._dots):
            if i < active:
                dot.setObjectName("step_dot_done")
                txt = self.LABELS[i]
                dot.setText(f"  ✓ {txt}")
            elif i == active:
                dot.setObjectName("step_dot_active")
                dot.setText(f"  {i + 1}. {self.LABELS[i]}")
            else:
                dot.setObjectName("step_dot_pending")
                dot.setText(f"  {i + 1}. {self.LABELS[i]}")
            dot.style().unpolish(dot)
            dot.style().polish(dot)

        for i, line in enumerate(self._lines):
            line.setObjectName("step_line_done" if i < active else "step_line_pending")
            line.style().unpolish(line)
            line.style().polish(line)


# ═══════════════════════════════════════════════════════════
# LEFT SIDEBAR
# ═══════════════════════════════════════════════════════════

class SidebarWidget(QFrame):
    step_clicked = pyqtSignal(int)

    STEPS = [
        ("ISO Source", "📄"),
        ("Select Editions", "📋"),
        ("Custom Tweaks", "⚙"),
        ("Compress ISO", "📦"),
        ("Target USB", "💾"),
        ("Confirm & Review", "🔍"),
        ("Build Media", "🔨"),
        ("Completed", "✓"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("sidebar_root")
        self.setFixedWidth(210)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Brand header
        brand = QFrame()
        brand.setObjectName("sidebar_brand")
        bl = QVBoxLayout(brand)
        bl.setContentsMargins(16, 16, 16, 14)
        bl.setSpacing(3)
        name = QLabel("WinISO Toolkit")
        name.setObjectName("brand_app_name")
        ver = QLabel("V2.0 SUPERCHARGED")
        ver.setObjectName("brand_version")
        bl.addWidget(name)
        bl.addWidget(ver)
        layout.addWidget(brand)

        # Section label
        nav_wrap = QVBoxLayout()
        nav_wrap.setContentsMargins(10, 14, 10, 0)
        nav_wrap.setSpacing(2)

        section = QLabel("WORKFLOW")
        section.setObjectName("sidebar_section_label")
        nav_wrap.addWidget(section)
        nav_wrap.addSpacing(6)

        self._nav_buttons: list[QPushButton] = []
        for idx, (text, icon) in enumerate(self.STEPS):
            btn = QPushButton(f"  {icon}   {text}")
            btn.setObjectName("nav_item")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda checked, i=idx: self.step_clicked.emit(i))
            self._nav_buttons.append(btn)
            nav_wrap.addWidget(btn)

        layout.addLayout(nav_wrap)
        layout.addStretch()

    def set_step(self, active: int) -> None:
        for i, btn in enumerate(self._nav_buttons):
            btn.setProperty("active", i == active)
            btn.setProperty("done", i < active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            icon = self.STEPS[i][1]
            text = self.STEPS[i][0]
            if i < active:
                btn.setText(f"  ✓   {text}")
            else:
                btn.setText(f"  {icon}   {text}")


# ═══════════════════════════════════════════════════════════
# DROPZONE
# ═══════════════════════════════════════════════════════════

class IsoDropArea(QFrame):
    file_dropped = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("dropzone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(170)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(6)

        icon = QLabel("⬆")
        icon.setObjectName("dropzone_icon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Drop your Windows ISO file here")
        title.setObjectName("dropzone_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hint = QLabel("or click below to browse  ·  Supports .iso files from Microsoft")
        hint.setObjectName("dropzone_hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.browse_btn = _btn("Browse files…", "secondary")
        self.browse_btn.setMinimumWidth(160)
        self.browse_btn.setFixedHeight(34)

        layout.addWidget(icon)
        layout.addSpacing(4)
        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addSpacing(8)
        layout.addWidget(self.browse_btn, 0, Qt.AlignmentFlag.AlignCenter)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            if any(u.toLocalFile().lower().endswith(".iso") for u in event.mimeData().urls()):
                event.acceptProposedAction()
                self.setProperty("drag_over", True)
                self.style().unpolish(self)
                self.style().polish(self)

    def dragLeaveEvent(self, event: object) -> None:
        self.setProperty("drag_over", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent) -> None:
        self.setProperty("drag_over", False)
        self.style().unpolish(self)
        self.style().polish(self)
        for url in event.mimeData().urls():
            fp = url.toLocalFile()
            if fp.lower().endswith(".iso"):
                self.file_dropped.emit(fp)
                break


# ═══════════════════════════════════════════════════════════
# STEP 1 — ISO SOURCE
# ═══════════════════════════════════════════════════════════

class StepIsoSelect(QWidget):
    next_enabled = pyqtSignal(bool)
    _SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, state: dict, log_cb) -> None:
        super().__init__()
        self.state, self.log_cb = state, log_cb
        self.worker: ISOAnalyzeWorker | None = None
        self._spin_idx = 0

        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(0, 0, 0, 0)

        # Dropzone
        self.drop_area = IsoDropArea()
        self.drop_area.file_dropped.connect(self._set_path)
        self.drop_area.browse_btn.clicked.connect(self._browse)
        root.addWidget(self.drop_area)

        # Path input row
        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Paste ISO file path or drag above…")
        self.path_edit.setFixedHeight(38)
        self.verify_btn = _btn("Verify SHA-256", "secondary")
        self.verify_btn.setFixedHeight(38)
        self.verify_btn.setMinimumWidth(130)
        self.verify_btn.clicked.connect(self._verify)
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(self.verify_btn)
        root.addLayout(path_row)

        self.verify_bar = QProgressBar()
        self.verify_bar.setVisible(False)
        root.addWidget(self.verify_bar)

        # Status badge row
        status_row = QHBoxLayout()
        self.status_badge = _badge("NO FILE SELECTED", "neutral")
        self.spinner_lbl = _text("", size=12, weight=500)
        status_row.addWidget(self.status_badge)
        status_row.addSpacing(8)
        status_row.addWidget(self.spinner_lbl)
        status_row.addStretch()
        root.addLayout(status_row)

        # Metrics grid: 3 columns × 2 rows
        grid = QGridLayout()
        grid.setSpacing(8)
        self.m_volume   = _MetricCard("VOLUME LABEL")
        self.m_install  = _MetricCard("INSTALLER STATUS")
        self.m_image    = _MetricCard("INSTALL IMAGE")
        self.m_editions = _MetricCard("EDITIONS FOUND")
        self.m_compress = _MetricCard("EST. COMPRESSED")
        self.m_total    = _MetricCard("TOTAL ISO SIZE")
        grid.addWidget(self.m_volume, 0, 0)
        grid.addWidget(self.m_install, 0, 1)
        grid.addWidget(self.m_image, 0, 2)
        grid.addWidget(self.m_editions, 1, 0)
        grid.addWidget(self.m_compress, 1, 1)
        grid.addWidget(self.m_total, 1, 2)
        root.addLayout(grid)

        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._tick)
        self.path_edit.textChanged.connect(self._on_path_changed)

    def _tick(self) -> None:
        self._spin_idx = (self._spin_idx + 1) % len(self._SPIN)
        self.spinner_lbl.setText(f"{self._SPIN[self._spin_idx]}  Analyzing ISO structure…")

    def _browse(self) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Select ISO", "", "ISO Files (*.iso *.ISO)")
        if p:
            self._set_path(p)

    def _set_path(self, path: str) -> None:
        self.path_edit.setText(path)

    def _on_path_changed(self) -> None:
        p = Path(self.path_edit.text().strip())
        if not p.is_file():
            self._reset()
            return
        if self.worker and self.worker.isRunning():
            self.worker.finished_ok.disconnect()
            self.worker.failed.disconnect()
            self.worker.quit()
            self.worker.wait(300)
        self._set_badge("ANALYZING…", "neutral")
        self._spin_timer.start(80)
        self.log_cb(f"Probing: {p}")
        self.worker = ISOAnalyzeWorker(p)
        self.worker.finished_ok.connect(self._done)
        self.worker.failed.connect(self._fail)
        self.worker.start()

    def _done(self, info: ISOInfo) -> None:
        self._spin_timer.stop()
        self.spinner_lbl.setText("")
        self.state["iso_path"] = info.path
        self.state["iso_info"] = info

        if info.is_windows_installer:
            self._set_badge("VALID WINDOWS INSTALLER", "success")
            self.m_install.set_value("✓ Verified", "install.wim present")
        else:
            self._set_badge("INVALID ISO", "error")
            self.m_install.set_value("✗ Missing", "install.wim not found")

        self.m_volume.set_value(info.volume_label or "—")
        if info.install_image_path:
            self.m_image.set_value(
                str(info.install_image_path),
                _fmt_gb(info.install_image_size),
            )
        else:
            self.m_image.set_value("None")

        if info.wimlib_missing:
            self.m_editions.set_value("Requires wimlib", "Install to inspect editions")
        else:
            n = len(info.wim_images)
            names = ", ".join(i.display_name for i in info.wim_images[:3])
            self.m_editions.set_value(
                f"{n} edition{'s' if n != 1 else ''}",
                names,
            )

        self.m_compress.set_value(
            _fmt_gb(info.estimated_compressed_size),
            "LZMS ~45% savings",
        )
        self.m_total.set_value(_fmt_gb(info.total_iso_size))

        self.log_cb(
            f"OK — {info.volume_label} | Installer: {info.is_windows_installer} | "
            f"Editions: {len(info.wim_images)}"
        )
        _fade_in(self.m_volume, 200)
        self.next_enabled.emit(info.is_windows_installer)

    def _fail(self, err: str) -> None:
        self._spin_timer.stop()
        self.spinner_lbl.setText("")
        self._set_badge("READ ERROR", "error")
        self.m_install.set_value("Error", err[:100])
        self.log_cb(f"ERROR: {err}")
        self.next_enabled.emit(False)

    def _set_badge(self, text: str, kind: str) -> None:
        self.status_badge.setText(text)
        self.status_badge.setObjectName(f"badge_{kind}")
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    def _reset(self) -> None:
        self._set_badge("NO FILE SELECTED", "neutral")
        for m in (self.m_volume, self.m_install, self.m_image,
                  self.m_editions, self.m_compress, self.m_total):
            m.set_value("—")
        self.next_enabled.emit(False)

    # SHA-256 verification
    def _verify(self) -> None:
        iso = self.state.get("iso_path")
        if not iso:
            QMessageBox.warning(self, "No ISO", "Select an ISO file first.")
            return
        self.verify_btn.setEnabled(False)
        self.verify_btn.setText("Verifying…")
        self.verify_bar.setVisible(True)
        self._sha_w = SHA256VerifyWorker(iso)
        self._sha_w.progress.connect(lambda p, _: self.verify_bar.setValue(int(p)))
        self._sha_w.finished_ok.connect(self._sha_ok)
        self._sha_w.failed.connect(self._sha_err)
        self._sha_w.start()

    def _sha_ok(self, res: object) -> None:
        self.verify_btn.setEnabled(True)
        self.verify_btn.setText("Verify SHA-256")
        self.verify_bar.setVisible(False)
        QMessageBox.information(
            self, "SHA-256 Result",
            f"Hash: {res.calculated_hash}\nStatus: {res.official_name}",  # type: ignore[attr-defined]
        )

    def _sha_err(self, msg: str) -> None:
        self.verify_btn.setEnabled(True)
        self.verify_btn.setText("Verify SHA-256")
        self.verify_bar.setVisible(False)
        QMessageBox.critical(self, "Verify Error", msg)


# ═══════════════════════════════════════════════════════════
# STEP 2 — EDITION SELECT
# ═══════════════════════════════════════════════════════════

class StepEditionSelect(QWidget):
    next_enabled = pyqtSignal(bool)

    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        self._notice: QFrame | None = None
        self._install_btn: QPushButton | None = None

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        tb = QHBoxLayout()
        tb.setSpacing(8)
        sa = _btn("Select all", "ghost")
        sn = _btn("Deselect all", "ghost")
        sa.clicked.connect(lambda: self._check_all(True))
        sn.clicked.connect(lambda: self._check_all(False))
        self._count_lbl = _text("0 editions", size=12, weight=600)
        tb.addWidget(sa)
        tb.addWidget(sn)
        tb.addStretch()
        tb.addWidget(self._count_lbl)
        root.addLayout(tb)

        self.single_info = _text("", size=12, weight=400, color="#71717a")
        self.single_info.setVisible(False)
        self.single_info.setWordWrap(True)
        root.addWidget(self.single_info)

        self.list = QListWidget()
        root.addWidget(self.list, 1)

        # Footer summary
        footer = _card("card_elevated")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(16, 10, 16, 10)
        self.sum_sel = _text("Selected: 0 / 0", size=12, weight=600)
        self.sum_size = _text("~0.00 GB estimated", size=12, weight=500, color="#71717a")
        fl.addWidget(self.sum_sel)
        fl.addStretch()
        fl.addWidget(self.sum_size)
        root.addWidget(footer)

        self.list.itemChanged.connect(self._update)

    def _check_all(self, checked: bool) -> None:
        s = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item:
                item.setCheckState(s)

    def refresh(self) -> None:
        self.list.clear()
        info: ISOInfo | None = self.state.get("iso_info")
        if not info:
            self.next_enabled.emit(False)
            return

        if info.wimlib_missing:
            self._show_notice()
            item = QListWidgetItem("  ⚠  All Editions — wimlib required for individual selection")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            ph = WIMImageInfo(
                index=0, name="All Editions",
                description="Keep all editions (wimlib not installed)",
                size_bytes=info.install_image_size or info.total_iso_size,
            )
            item.setData(Qt.ItemDataRole.UserRole, ph)
            self.list.addItem(item)
            self.single_info.setVisible(False)
        else:
            if self._notice:
                self._notice.setVisible(False)
            for img in info.wim_images:
                sz = img.size_bytes / (1024 ** 3)
                item = QListWidgetItem(
                    f"  [{img.index}]   {img.display_name}   ·   {sz:.2f} GB"
                )
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                item.setData(Qt.ItemDataRole.UserRole, img)
                self.list.addItem(item)

            if len(info.wim_images) == 1:
                self.single_info.setText(
                    "ℹ  This ISO contains a single edition image. "
                    "This is normal for standard Windows 11 Pro ISOs."
                )
                self.single_info.setVisible(True)
            else:
                self.single_info.setVisible(False)

        n = self.list.count()
        self._count_lbl.setText(f"{n} edition{'s' if n != 1 else ''}")
        self._update()
        _fade_in(self.list)

    def _show_notice(self) -> None:
        if self._notice:
            self._notice.setVisible(True)
            return
        notice = _card("card_elevated")
        nl = QHBoxLayout(notice)
        nl.setContentsMargins(14, 10, 14, 10)
        nl.addWidget(_text("⚠", size=18))
        nl.addSpacing(8)
        t = _text(
            "<b>wimlib not installed.</b> "
            "Install it to inspect and remove individual Windows editions.",
            size=12,
        )
        t.setWordWrap(True)
        nl.addWidget(t, 1)
        self._install_btn = _btn("Install wimlib", "secondary")
        self._install_btn.setFixedHeight(32)
        self._install_btn.clicked.connect(self._install_wimlib)
        nl.addWidget(self._install_btn)
        self.layout().insertWidget(2, notice)
        self._notice = notice

    def _install_wimlib(self) -> None:
        if self._install_btn:
            self._install_btn.setEnabled(False)
            self._install_btn.setText("Installing…")
        self._wim_w = WimlibInstallWorker()
        self._wim_w.finished_ok.connect(self._wim_done)
        self._wim_w.failed.connect(self._wim_err)
        self._wim_w.start()

    def _wim_done(self, ok: bool) -> None:
        if self._install_btn:
            self._install_btn.setEnabled(True)
            self._install_btn.setText("Install wimlib")
        if not ok:
            QMessageBox.warning(self, "Failed", "wimlib could not be installed.")
            return
        info: ISOInfo | None = self.state.get("iso_info")
        if info:
            self._re = ISOAnalyzeWorker(info.path)
            self._re.finished_ok.connect(self._re_done)
            self._re.failed.connect(lambda e: QMessageBox.warning(self, "Error", e))
            self._re.start()

    def _wim_err(self, err: str) -> None:
        if self._install_btn:
            self._install_btn.setEnabled(True)
            self._install_btn.setText("Retry")
        QMessageBox.critical(self, "Error", err)

    def _re_done(self, info: ISOInfo) -> None:
        self.state["iso_info"] = info
        self.refresh()

    def _update(self) -> None:
        sel = total_bytes = 0
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                sel += 1
                img: WIMImageInfo = item.data(Qt.ItemDataRole.UserRole)
                if img:
                    total_bytes += img.size_bytes
        n = self.list.count()
        est_gb = total_bytes * 0.45 / (1024 ** 3)
        self.sum_sel.setText(f"Selected: {sel} / {n}")
        self.sum_size.setText(f"~{est_gb:.2f} GB estimated output")
        self.next_enabled.emit(sel > 0)

    def save_selection(self) -> None:
        indices = []
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item and item.checkState() == Qt.CheckState.Checked:
                img: WIMImageInfo = item.data(Qt.ItemDataRole.UserRole)
                if img:
                    indices.append(img.index)
        self.state["indices"] = indices


# ═══════════════════════════════════════════════════════════
# STEP 3 — CUSTOMIZATION
# ═══════════════════════════════════════════════════════════

class StepCustomization(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        # Bypass section
        bypass = QGroupBox("Windows 11 Hardware Bypasses")
        bb = QVBoxLayout(bypass)
        bb.setSpacing(8)
        self.chk_tpm = QCheckBox("Bypass TPM 2.0, Secure Boot, RAM & CPU requirements")
        self.chk_tpm.setChecked(True)
        self.chk_msa = QCheckBox("Bypass Microsoft Account requirement (BypassNRO)")
        self.chk_msa.setChecked(True)
        self.chk_tel = QCheckBox("Disable telemetry & diagnostic data collection")
        self.chk_tel.setChecked(True)
        bb.addWidget(self.chk_tpm)
        bb.addWidget(self.chk_msa)
        bb.addWidget(self.chk_tel)
        root.addWidget(bypass)

        # User identity
        user_box = QGroupBox("User Identity & Hostname")
        uf = QVBoxLayout(user_box)
        uf.setSpacing(8)
        urow = QHBoxLayout()
        urow.setSpacing(12)
        self.username = QLineEdit("User")
        self.username.setFixedHeight(36)
        self.compname = QLineEdit("WinISO-PC")
        self.compname.setFixedHeight(36)
        urow.addWidget(_text("Username", size=12, weight=500))
        urow.addWidget(self.username)
        urow.addSpacing(8)
        urow.addWidget(_text("Hostname", size=12, weight=500))
        urow.addWidget(self.compname)
        uf.addLayout(urow)
        root.addWidget(user_box)

        # Driver slipstreaming
        drv_box = QGroupBox("Driver Slipstreaming (Optional)")
        dv = QVBoxLayout(drv_box)
        drow = QHBoxLayout()
        drow.setSpacing(8)
        self.driver_edit = QLineEdit()
        self.driver_edit.setPlaceholderText("Select folder with .inf driver files…")
        self.driver_edit.setFixedHeight(36)
        drv_btn = _btn("Browse…", "secondary")
        drv_btn.setFixedHeight(36)
        drv_btn.clicked.connect(self._browse_drivers)
        drow.addWidget(self.driver_edit, 1)
        drow.addWidget(drv_btn)
        dv.addLayout(drow)
        root.addWidget(drv_box)

        root.addStretch()

    def _browse_drivers(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Select Driver Folder")
        if d:
            self.driver_edit.setText(d)

    def save_settings(self) -> None:
        from winiso_toolkit.iso.unattended import BypassOptions
        self.state["bypass_options"] = BypassOptions(
            bypass_tpm=self.chk_tpm.isChecked(),
            bypass_secure_boot=self.chk_tpm.isChecked(),
            bypass_ram=self.chk_tpm.isChecked(),
            bypass_cpu=self.chk_tpm.isChecked(),
            bypass_msa=self.chk_msa.isChecked(),
            disable_telemetry=self.chk_tel.isChecked(),
            username=self.username.text().strip() or "User",
            computer_name=self.compname.text().strip() or "WinISO-PC",
        )
        drv = self.driver_edit.text().strip()
        self.state["driver_dir"] = Path(drv) if drv else None


# ═══════════════════════════════════════════════════════════
# STEP 4 — COMPRESS
# ═══════════════════════════════════════════════════════════

class StepCompress(QWidget):
    def __init__(self, state: dict, parent_win: "MainWindow") -> None:
        super().__init__()
        self.state, self.parent_win = state, parent_win

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        # Progress card
        pcard = _card()
        pc = QVBoxLayout(pcard)
        pc.setContentsMargins(20, 18, 20, 18)
        pc.setSpacing(12)
        self.status_lbl = _text("Waiting to start…", size=13, weight=600)
        self.bar = QProgressBar()
        pc.addWidget(self.status_lbl)
        pc.addWidget(self.bar)
        root.addWidget(pcard)

        # Metrics row
        grid = QHBoxLayout()
        grid.setSpacing(8)
        self.m_speed = _MetricCard("SPEED")
        self.m_eta   = _MetricCard("ETA")
        self.m_src   = _MetricCard("SOURCE")
        self.m_out   = _MetricCard("OUTPUT")
        self.m_saved = _MetricCard("SAVED")
        for m in (self.m_speed, self.m_eta, self.m_src, self.m_out, self.m_saved):
            grid.addWidget(m)
        root.addLayout(grid)

        root.addStretch()

    def start(self) -> None:
        iso_path: Path = self.state["iso_path"]
        indices: list[int] = self.state.get("indices", [1])
        output = iso_path.with_name(f"{iso_path.stem}_compressed.iso")
        self.state["output_iso"] = output
        self._t0 = time.time()

        info: ISOInfo | None = self.state.get("iso_info")
        if info and info.install_image_size:
            self.m_src.set_value(_fmt_gb(info.install_image_size))

        self.worker = WorkerThread(
            WinISOPipeline().compress_iso,
            iso_path, output, indices,
            bypass_options=self.state.get("bypass_options"),
            driver_dir=self.state.get("driver_dir"),
        )
        self.worker.progress.connect(self._prog)
        self.worker.finished_ok.connect(self._ok)
        self.worker.failed.connect(self._err)
        self.worker.start()

    def _prog(self, pct: float, msg: str) -> None:
        self.bar.setValue(int(pct))
        self.status_lbl.setText(msg)
        elapsed = max(time.time() - self._t0, 0.1)
        if pct > 5:
            eta = elapsed / (pct / 100) - elapsed
            self.m_eta.set_value(f"{int(eta // 60)}m {int(eta % 60)}s")
            self.m_speed.set_value(f"{(pct / 100) / elapsed * 100:.1f}%/s")

    def _ok(self, result: object) -> None:
        self.state["output_iso"] = Path(str(result))
        out = self.state["output_iso"]
        if out.exists():
            self.m_out.set_value(_fmt_gb(out.stat().st_size))
            info: ISOInfo | None = self.state.get("iso_info")
            src = info.install_image_size if info else 0
            if src:
                saved = (1 - out.stat().st_size / src) * 100
                self.m_saved.set_value(f"−{saved:.1f}%")
        self.parent_win.advance()

    def _err(self, msg: str) -> None:
        QMessageBox.critical(self, "Compression Failed", msg)
        self.parent_win.set_back_enabled(True)


# ═══════════════════════════════════════════════════════════
# STEP 5 — USB SELECT
# ═══════════════════════════════════════════════════════════

class StepUsbSelect(QWidget):
    next_enabled = pyqtSignal(bool)

    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        tb = QHBoxLayout()
        tb.setSpacing(8)
        refresh = _btn("Refresh", "secondary")
        refresh.setFixedHeight(34)
        refresh.clicked.connect(self.refresh)
        health = _btn("Health check", "ghost")
        health.setFixedHeight(34)
        health.clicked.connect(self._health)
        tb.addWidget(refresh)
        tb.addWidget(health)
        tb.addStretch()
        root.addLayout(tb)

        self.combo = QComboBox()
        self.combo.setFixedHeight(40)
        self.combo.currentIndexChanged.connect(self._validate)
        root.addWidget(self.combo)

        # Capacity card
        self.cap_card = _card()
        cl = QHBoxLayout(self.cap_card)
        cl.setContentsMargins(16, 10, 16, 10)
        self.cap_badge = _badge("—", "neutral")
        self.cap_text = _text("Select a USB drive", size=12, weight=400, color="#71717a")
        cl.addWidget(self.cap_badge)
        cl.addSpacing(8)
        cl.addWidget(self.cap_text, 1)
        root.addWidget(self.cap_card)

        # Boot options
        opts = QGroupBox("Boot Mode & Partitioning")
        ol = QVBoxLayout(opts)
        ol.setSpacing(8)
        self.boot_combo = QComboBox()
        self.boot_combo.addItems([
            "UEFI + Legacy MBR (Maximum Compatibility)",
            "UEFI Only (GPT — Modern PCs)",
            "Legacy MBR Only (Older BIOS)",
        ])
        self.boot_combo.setFixedHeight(36)
        self.dual_chk = QCheckBox("Dual-partition layout (FAT32 boot + NTFS data for install.wim > 4 GB)")
        self.dual_chk.setChecked(True)
        ol.addWidget(self.boot_combo)
        ol.addWidget(self.dual_chk)
        root.addWidget(opts)

        root.addStretch()

    def refresh(self) -> None:
        self.combo.clear()
        devices = USBDetector().list_devices()
        self.state["usb_devices"] = devices
        if not devices:
            self.combo.addItem("No USB drives detected")
        for d in devices:
            self.combo.addItem(
                f"{d.name}  ·  {d.size_gb:.1f} GB  ·  {d.filesystem or '?'}  [{d.path}]",
                d,
            )
        self._validate()
        _fade_in(self.combo)

    def _health(self) -> None:
        dev: USBDevice | None = self.combo.currentData()
        if not dev:
            QMessageBox.warning(self, "No USB", "Select a USB drive first.")
            return
        try:
            from winiso_toolkit.usb.health import USBHealthChecker
            r = USBHealthChecker().run_quick_health_check(dev.path, mount_point=dev.mount_point)
            QMessageBox.information(
                self, "Health Report",
                f"Drive: {dev.name} [{dev.path}]\n"
                f"Write: {r.write_speed_mbps:.1f} MB/s\n"
                f"Capacity: {'✓ OK' if r.capacity_verified else '✗ FAIL'}\n"
                f"Status: {r.status_message}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _validate(self) -> None:
        dev: USBDevice | None = self.combo.currentData()
        out: Path | None = self.state.get("output_iso")
        if not dev or not out or not out.exists():
            self.cap_badge.setText("—")
            self.cap_badge.setObjectName("badge_neutral")
            self.cap_badge.style().unpolish(self.cap_badge)
            self.cap_badge.style().polish(self.cap_badge)
            self.cap_text.setText("Select a USB drive to verify capacity")
            self.next_enabled.emit(False)
            return
        ok, msg = USBCreator().validate_capacity(dev.size_bytes, out.stat().st_size)
        if ok:
            self.cap_badge.setText("OK")
            self.cap_badge.setObjectName("badge_success")
            self.cap_text.setText(
                f"{dev.size_gb:.1f} GB available  ≥  {out.stat().st_size / (1024**3):.1f} GB required"
            )
            self.state["usb_device"] = dev
            self.next_enabled.emit(True)
        else:
            self.cap_badge.setText("FAIL")
            self.cap_badge.setObjectName("badge_error")
            self.cap_text.setText(msg)
            self.next_enabled.emit(False)
        self.cap_badge.style().unpolish(self.cap_badge)
        self.cap_badge.style().polish(self.cap_badge)

    def save_selection(self) -> None:
        self.state["boot_mode"] = [BootMode.BOTH, BootMode.UEFI, BootMode.LEGACY][
            self.boot_combo.currentIndex()
        ]
        self.state["use_dual_partition"] = self.dual_chk.isChecked()


# ═══════════════════════════════════════════════════════════
# STEP 6 — CONFIRM
# ═══════════════════════════════════════════════════════════

class StepConfirm(QWidget):
    next_enabled = pyqtSignal(bool)

    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        # Summary card
        self.sum_card = _card()
        sl = QVBoxLayout(self.sum_card)
        sl.setContentsMargins(20, 18, 20, 18)
        sl.setSpacing(6)
        self.sum_lbl = QLabel()
        self.sum_lbl.setWordWrap(True)
        self.sum_lbl.setStyleSheet("font-size:12.5px; line-height:1.7;")
        sl.addWidget(self.sum_lbl)
        root.addWidget(self.sum_card)

        # Warning
        warn = _card("card_elevated")
        wl = QHBoxLayout(warn)
        wl.setContentsMargins(16, 12, 16, 12)
        wl.addWidget(_text("⚠", size=20))
        wl.addSpacing(10)
        wt = _text(
            "<b>All data on the selected USB drive will be permanently erased.</b><br>"
            "Ensure you have backed up any important files before proceeding.",
            size=12,
        )
        wt.setWordWrap(True)
        wl.addWidget(wt, 1)
        root.addWidget(warn)

        self.confirm_chk = QCheckBox("I understand — format the drive and create bootable media")
        self.confirm_chk.setStyleSheet("font-size:12.5px; font-weight:600;")
        self.confirm_chk.stateChanged.connect(
            lambda: self.next_enabled.emit(self.confirm_chk.isChecked())
        )
        root.addWidget(self.confirm_chk)

        root.addStretch()

    def refresh(self) -> None:
        iso: Path | None = self.state.get("output_iso")
        usb: USBDevice | None = self.state.get("usb_device")
        indices = self.state.get("indices", [])
        boot: BootMode = self.state.get("boot_mode", BootMode.BOTH)
        dual: bool = self.state.get("use_dual_partition", False)

        ed = "All" if indices == [0] else str(indices)
        sz = f"{iso.stat().st_size / (1024**3):.2f} GB" if iso and iso.exists() else "?"

        self.sum_lbl.setText(
            f"<table style='border-spacing:0 5px;'>"
            f"<tr><td style='width:160px; color:#71717a;'>Output ISO</td>"
            f"<td><b>{iso}</b></td></tr>"
            f"<tr><td style='color:#71717a;'>ISO Size</td>"
            f"<td>{sz}</td></tr>"
            f"<tr><td style='color:#71717a;'>Editions</td>"
            f"<td>{ed}</td></tr>"
            f"<tr><td style='color:#71717a;'>Target USB</td>"
            f"<td><b>{usb.path if usb else '—'}</b> ({usb.name if usb else ''})</td></tr>"
            f"<tr><td style='color:#71717a;'>Boot Mode</td>"
            f"<td>{boot.value}</td></tr>"
            f"<tr><td style='color:#71717a;'>Partitioning</td>"
            f"<td>{'Dual (FAT32 + NTFS)' if dual else 'Single'}</td></tr>"
            f"</table>"
        )
        self.confirm_chk.setChecked(False)
        self.next_enabled.emit(False)


# ═══════════════════════════════════════════════════════════
# STEP 7 — BURN
# ═══════════════════════════════════════════════════════════

class StepBurn(QWidget):
    def __init__(self, state: dict, parent_win: "MainWindow") -> None:
        super().__init__()
        self.state, self.parent_win = state, parent_win
        self._t0 = 0.0

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        pcard = _card()
        pc = QVBoxLayout(pcard)
        pc.setContentsMargins(20, 18, 20, 18)
        pc.setSpacing(12)
        self.status_lbl = _text("Preparing…", size=13, weight=600)
        self.bar = QProgressBar()
        pc.addWidget(self.status_lbl)
        pc.addWidget(self.bar)
        root.addWidget(pcard)

        grid = QHBoxLayout()
        grid.setSpacing(8)
        self.m_speed = _MetricCard("WRITE SPEED")
        self.m_eta   = _MetricCard("ETA")
        self.m_done  = _MetricCard("WRITTEN")
        for m in (self.m_speed, self.m_eta, self.m_done):
            grid.addWidget(m)
        root.addLayout(grid)

        root.addStretch()

    def start(self) -> None:
        iso: Path | None = self.state.get("output_iso")
        usb: USBDevice | None = self.state.get("usb_device")
        if not iso or not usb:
            QMessageBox.critical(self, "Error", "Missing ISO or USB device.")
            return
        self._t0 = time.time()
        mode: BootMode = self.state.get("boot_mode", BootMode.BOTH)
        self.worker = WorkerThread(
            USBCreator().create,
            iso, usb.path,
            boot_mode=mode,
            bypass_options=self.state.get("bypass_options"),
            driver_dir=self.state.get("driver_dir"),
            use_dual_partition=self.state.get("use_dual_partition", False),
            verify=True,
        )
        self.worker.progress.connect(self._prog)
        self.worker.finished_ok.connect(lambda _: self.parent_win.advance())
        self.worker.failed.connect(lambda m: QMessageBox.critical(self, "Failed", m))
        self.worker.start()

    def _prog(self, pct: float, msg: str) -> None:
        self.bar.setValue(int(pct))
        self.status_lbl.setText(msg)
        elapsed = max(time.time() - self._t0, 0.1)
        if pct > 5:
            eta = elapsed / (pct / 100) - elapsed
            self.m_eta.set_value(f"{int(eta // 60)}m {int(eta % 60)}s")
            m = re.search(r"([\d.]+)\s*MB/s", msg)
            if m:
                self.m_speed.set_value(f"{m.group(1)} MB/s")
            out = self.state.get("output_iso")
            total = out.stat().st_size if out and out.exists() else 0
            self.m_done.set_value(_fmt_gb(int((pct / 100) * total)))


# ═══════════════════════════════════════════════════════════
# STEP 8 — DONE
# ═══════════════════════════════════════════════════════════

class StepResult(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        # Result card
        self.result_card = _card()
        rl = QVBoxLayout(self.result_card)
        rl.setContentsMargins(20, 18, 20, 18)
        rl.setSpacing(6)
        self.result_lbl = QLabel()
        self.result_lbl.setWordWrap(True)
        self.result_lbl.setStyleSheet("font-size:12.5px; line-height:1.7;")
        rl.addWidget(self.result_lbl)
        root.addWidget(self.result_card)

        # Verification checklist
        chk = _card("card_elevated")
        cl = QVBoxLayout(chk)
        cl.setContentsMargins(20, 16, 20, 16)
        cl.setSpacing(8)
        cl.addWidget(_text("Integrity Verification", size=13, weight=700))
        cl.addWidget(_sep())
        for item_text in [
            "El Torito bootloader structure",
            "BCD boot configuration database",
            "Post-write SHA-256 file checksums",
            "EFI/UEFI firmware bootloader files",
        ]:
            row = QHBoxLayout()
            row.addWidget(_text("✓", size=13, weight=700, color="#4ade80"))
            row.addSpacing(8)
            row.addWidget(_text(item_text, size=12, weight=400), 1)
            row.addWidget(_badge("VERIFIED", "success"))
            cl.addLayout(row)
        root.addWidget(chk)

        # Actions
        act = QHBoxLayout()
        act.setSpacing(8)
        vm = _btn("Test in QEMU VM", "secondary")
        vm.setFixedHeight(36)
        vm.clicked.connect(self._test_vm)
        eject = _btn("Safely eject USB", "secondary")
        eject.setFixedHeight(36)
        eject.clicked.connect(self._eject)
        act.addWidget(vm)
        act.addWidget(eject)
        act.addStretch()
        root.addLayout(act)

        root.addStretch()

    def refresh(self) -> None:
        usb: USBDevice | None = self.state.get("usb_device")
        iso: Path | None = self.state.get("output_iso")
        sz = f"{iso.stat().st_size / (1024**3):.2f} GB" if iso and iso.exists() else "—"
        self.result_lbl.setText(
            f"<table style='border-spacing:0 5px;'>"
            f"<tr><td style='width:140px; color:#71717a;'>USB Drive</td>"
            f"<td><b>{usb.path if usb else '—'}</b> ({usb.name if usb else ''})</td></tr>"
            f"<tr><td style='color:#71717a;'>ISO Source</td><td>{iso}</td></tr>"
            f"<tr><td style='color:#71717a;'>Size Written</td><td>{sz}</td></tr>"
            f"</table>"
        )
        _fade_in(self.result_card)

    def _test_vm(self) -> None:
        iso: Path | None = self.state.get("output_iso")
        if not iso or not iso.exists():
            QMessageBox.warning(self, "No ISO", "Output ISO not found.")
            return
        from winiso_toolkit.utils.vm import QEMUTester
        t = QEMUTester()
        if not t.is_qemu_available():
            QMessageBox.information(self, "QEMU Not Found", "Install QEMU to test ISOs in a VM.")
            return
        try:
            t.launch_test_vm(iso)
        except Exception as e:
            QMessageBox.critical(self, "VM Error", str(e))

    def _eject(self) -> None:
        usb: USBDevice | None = self.state.get("usb_device")
        if not usb:
            return
        from winiso_toolkit.usb.ejector import USBEjector
        ok, msg = USBEjector().safe_eject(usb.path)
        (QMessageBox.information if ok else QMessageBox.warning)(self, "Eject", msg)


# ═══════════════════════════════════════════════════════════
# MAIN WINDOW — Premium Shell
# ═══════════════════════════════════════════════════════════

# Page header definitions: (title, subtitle)
_PAGE_HEADERS = [
    ("ISO Source", "Select or drag your official Windows 10/11 ISO file to begin."),
    ("Select Editions", "Choose which Windows editions to keep in the final image."),
    ("Customization", "Configure hardware bypasses, user defaults, and driver injection."),
    ("Compressing ISO", "Building and compressing your customized Windows image."),
    ("Target USB", "Select and configure the destination USB flash drive."),
    ("Confirm & Review", "Review your configuration before writing to USB."),
    ("Building Media", "Writing the bootable installer to your USB drive."),
    ("Complete", "Your bootable Windows USB drive has been created successfully."),
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WinISO Toolkit  ·  v2.0")
        self.setMinimumSize(980, 660)
        self.resize(1040, 720)
        self.state: dict = {}
        self.is_dark = True

        # Central widget
        central = QWidget()
        central.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(central)
        shell = QHBoxLayout(central)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        # ── LEFT SIDEBAR ──────────────────────────────────
        sidebar_container = QVBoxLayout()
        sidebar_container.setContentsMargins(0, 0, 0, 0)
        sidebar_container.setSpacing(0)

        self.sidebar = SidebarWidget()

        # Theme toggle at bottom
        theme_footer = QFrame()
        theme_footer.setObjectName("sidebar_root")
        tfl = QVBoxLayout(theme_footer)
        tfl.setContentsMargins(10, 8, 10, 10)
        self.theme_btn = QPushButton("  ◐   Dark mode")
        self.theme_btn.setObjectName("theme_toggle_btn")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.setFixedHeight(32)
        self.theme_btn.clicked.connect(self._toggle_theme)
        tfl.addWidget(self.theme_btn)

        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar_root")
        sf_layout = QVBoxLayout(sidebar_frame)
        sf_layout.setContentsMargins(0, 0, 0, 0)
        sf_layout.setSpacing(0)
        sf_layout.addWidget(self.sidebar, 1)
        sf_layout.addWidget(theme_footer)

        shell.addWidget(sidebar_frame)

        # ── RIGHT CONTENT AREA ────────────────────────────
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        # Content canvas
        canvas = QWidget()
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(24, 20, 24, 12)
        canvas_layout.setSpacing(14)

        # Page header (title + subtitle)
        self.page_title = QLabel()
        self.page_title.setObjectName("page_title")
        self.page_subtitle = QLabel()
        self.page_subtitle.setObjectName("page_subtitle")
        self.page_subtitle.setWordWrap(True)
        canvas_layout.addWidget(self.page_title)
        canvas_layout.addWidget(self.page_subtitle)

        # Step progress bar
        self.step_bar = StepProgressBar()
        canvas_layout.addWidget(self.step_bar)

        canvas_layout.addSpacing(4)

        # Stacked pages
        self.stack = QStackedWidget()
        self.step_iso      = StepIsoSelect(self.state, self.log_message)
        self.step_editions = StepEditionSelect(self.state)
        self.step_custom   = StepCustomization(self.state)
        self.step_compress = StepCompress(self.state, self)
        self.step_usb      = StepUsbSelect(self.state)
        self.step_confirm  = StepConfirm(self.state)
        self.step_burn     = StepBurn(self.state, self)
        self.step_result   = StepResult(self.state)

        for w in (
            self.step_iso, self.step_editions, self.step_custom,
            self.step_compress, self.step_usb, self.step_confirm,
            self.step_burn, self.step_result,
        ):
            self.stack.addWidget(self._wrap_scroll(w))

        canvas_layout.addWidget(self.stack, 1)

        # Navigation buttons
        nav = QHBoxLayout()
        nav.setSpacing(10)
        self.back_btn = _btn("← Back", "ghost")
        self.back_btn.setFixedHeight(38)
        self.back_btn.setMinimumWidth(100)
        self.next_btn = _btn("Continue →", "primary")
        self.next_btn.setFixedHeight(38)
        self.next_btn.setMinimumWidth(140)
        self.back_btn.clicked.connect(self.go_back)
        self.next_btn.clicked.connect(self.go_next)
        nav.addWidget(self.back_btn)
        nav.addStretch()
        nav.addWidget(self.next_btn)
        canvas_layout.addLayout(nav)

        right.addWidget(canvas, 1)

        # ── BOTTOM CONSOLE DRAWER ─────────────────────────
        console_frame = QFrame()
        console_frame.setObjectName("console_container")
        cfl = QVBoxLayout(console_frame)
        cfl.setContentsMargins(24, 6, 24, 6)
        cfl.setSpacing(4)

        # Console toolbar
        ctb = QHBoxLayout()
        ctb.setSpacing(8)
        dot = _text("●", size=8, color="#4ade80")
        ctb.addWidget(dot)
        ctb.addWidget(_text("Console", size=11, weight=600))
        ctb.addStretch()
        self.toggle_console_btn = QPushButton("Show")
        self.toggle_console_btn.setObjectName("console_btn")
        self.toggle_console_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_console_btn.clicked.connect(self._toggle_console)
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("console_btn")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(lambda: self.console.clear())
        ctb.addWidget(self.toggle_console_btn)
        ctb.addWidget(clear_btn)
        cfl.addLayout(ctb)

        self.console = QTextEdit()
        self.console.setObjectName("console_output")
        self.console.setReadOnly(True)
        self.console.setFixedHeight(120)
        self.console.setVisible(False)
        cfl.addWidget(self.console)

        right.addWidget(console_frame)
        shell.addLayout(right, 1)

        # ── LOGGING ───────────────────────────────────────
        self.log_handler = QObjectLogHandler()
        self.log_handler.new_log.connect(self.console.append)
        logging.getLogger("winiso_toolkit").addHandler(self.log_handler)

        # ── SIGNAL WIRING ─────────────────────────────────
        self.step_iso.next_enabled.connect(self._set_next)
        self.step_editions.next_enabled.connect(self._set_next)
        self.step_usb.next_enabled.connect(self._set_next)
        self.step_confirm.next_enabled.connect(self._set_next)
        self.sidebar.step_clicked.connect(self._sidebar_nav)

        self._step = 0
        self._update_nav()

    # ── Theme ─────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        self.is_dark = not self.is_dark
        app = QApplication.instance()
        if app:
            app.setStyleSheet(DARK_THEME_QSS if self.is_dark else LIGHT_THEME_QSS)
        self.theme_btn.setText("  ◐   Dark mode" if self.is_dark else "  ◑   Light mode")

    # ── Layout helpers ────────────────────────────────────

    @staticmethod
    def _wrap_scroll(widget: QWidget) -> QScrollArea:
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setWidget(widget)
        return sa

    # ── Navigation ────────────────────────────────────────

    def log_message(self, msg: str) -> None:
        logging.getLogger("winiso_toolkit").info(msg)

    def _toggle_console(self) -> None:
        vis = self.console.isVisible()
        self.console.setVisible(not vis)
        self.toggle_console_btn.setText("Hide" if not vis else "Show")

    def _set_next(self, enabled: bool) -> None:
        if self._step not in (3, 6, 7):
            self.next_btn.setEnabled(enabled)

    def _update_nav(self) -> None:
        self.sidebar.set_step(self._step)
        self.step_bar.set_step(self._step)

        # Page header
        title, subtitle = _PAGE_HEADERS[self._step]
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)

        auto = self._step in (3, 6, 7)
        self.back_btn.setEnabled(self._step > 0 and not auto)
        self.next_btn.setEnabled(not auto)

        if self._step == 7:
            self.next_btn.setText("Done ✓")
        elif self._step == 5:
            self.next_btn.setText("Start build →")
        else:
            self.next_btn.setText("Continue →")

    def set_back_enabled(self, v: bool) -> None:
        self.back_btn.setEnabled(v)

    def _sidebar_nav(self, idx: int) -> None:
        """Allow clicking completed steps to go back."""
        if idx < self._step:
            self._step = idx
            self.stack.setCurrentIndex(self._step)
            self._update_nav()

    def go_back(self) -> None:
        if self._step > 0:
            self._step -= 1
            self.stack.setCurrentIndex(self._step)
            self._update_nav()

    def advance(self) -> None:
        self._step += 1
        self.stack.setCurrentIndex(self._step)
        self._update_nav()
        self._on_step_entered()

    def go_next(self) -> None:
        if self._step == 1:
            self.step_editions.save_selection()
            if not self.state.get("indices"):
                QMessageBox.warning(self, "No Editions", "Select at least one edition.")
                return
        elif self._step == 2:
            self.step_custom.save_settings()
        elif self._step == 4:
            self.step_usb.save_selection()
        elif self._step == 7:
            self.close()
            return

        self._step += 1
        self.stack.setCurrentIndex(self._step)
        self._update_nav()
        self._on_step_entered()

    def _on_step_entered(self) -> None:
        if self._step == 1:
            self.step_editions.refresh()
            _fade_in(self.step_editions)
        elif self._step == 3:
            self.step_compress.start()
        elif self._step == 4:
            self.step_usb.refresh()
            _fade_in(self.step_usb)
        elif self._step == 5:
            self.step_confirm.refresh()
            _fade_in(self.step_confirm)
        elif self._step == 6:
            self.step_burn.start()
        elif self._step == 7:
            self.step_result.refresh()
            _fade_in(self.step_result)


def run_gui() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("WinISO Toolkit")
    app.setApplicationVersion("2.0.0")
    app.setStyleSheet(DARK_THEME_QSS)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run_gui())
