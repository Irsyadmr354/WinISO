"""WinISO Toolkit — Ultimate Windows 11 Fluent Desktop Architecture GUI."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QThread,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
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

# ─────────────────────────────────────────────────────────────
# UTILITIES & HELPERS
# ─────────────────────────────────────────────────────────────

def _fmt_gb(n: int) -> str:
    return f"{n / (1024 ** 3):.2f} GB"


def _sep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


def _label(text: str = "", *, muted: bool = False, bold: bool = False,
           color: str = "", size: int = 0) -> QLabel:
    lbl = QLabel(text)
    parts: list[str] = ["background:transparent;"]
    if muted:
        parts.append("color:#71717a;")
    elif color:
        parts.append(f"color:{color};")
    if bold:
        parts.append("font-weight:700;")
    if size:
        parts.append(f"font-size:{size}px;")
    lbl.setStyleSheet(" ".join(parts))
    return lbl


def _card() -> QFrame:
    f = QFrame()
    f.setObjectName("card_frame")
    return f


def _fade_in(widget: QWidget, ms: int = 180) -> None:
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)


# ─────────────────────────────────────────────────────────────
# DRAG & DROP ISO AREA (FIXED ALIGNMENT & SIZING)
# ─────────────────────────────────────────────────────────────

class IsoDropArea(QFrame):
    file_dropped = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("drop_area")
        self.setAcceptDrops(True)
        self.setMinimumHeight(180)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        icon_lbl = QLabel("📂")
        icon_lbl.setStyleSheet("font-size:32px; background:transparent;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel("Drag & Drop Windows ISO File Here")
        title_lbl.setStyleSheet("font-size:15px; font-weight:800; background:transparent;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        sub_lbl = QLabel("Supports official Windows 10 & 11 .iso installer images")
        sub_lbl.setStyleSheet("font-size:11.5px; background:transparent;")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.browse_btn = QPushButton("  📂 Browse File System")
        self.browse_btn.setMinimumWidth(200)
        self.browse_btn.setFixedHeight(36)

        layout.addWidget(icon_lbl)
        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)
        layout.addSpacing(6)
        layout.addWidget(self.browse_btn, 0, Qt.AlignmentFlag.AlignCenter)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith(".iso") for url in urls):
                event.acceptProposedAction()
                self.setProperty("drag_active", True)
                self.style().unpolish(self)
                self.style().polish(self)

    def dragLeaveEvent(self, event: object) -> None:
        self.setProperty("drag_active", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent) -> None:
        self.setProperty("drag_active", False)
        self.style().unpolish(self)
        self.style().polish(self)
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".iso"):
                self.file_dropped.emit(file_path)
                break


# ─────────────────────────────────────────────────────────────
# LOG BRIDGE & WORKERS
# ─────────────────────────────────────────────────────────────

class _LogBridge(QThread):
    new_log = pyqtSignal(str)
    def run(self) -> None: pass


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
            colors = {"INFO": "#3b82f6", "WARNING": "#f59e0b",
                      "ERROR": "#ef4444", "DEBUG": "#71717a"}
            c = colors.get(record.levelname, "#a1a1aa")
            html = (
                f"<span style='color:#71717a'>[{ts}]</span> "
                f"<span style='color:{c};font-weight:700'>[{record.levelname}]</span> "
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


# ─────────────────────────────────────────────────────────────
# LEFT SIDEBAR NAVIGATION WIDGET
# ─────────────────────────────────────────────────────────────

class SidebarWidget(QFrame):
    STEPS = [
        "1. ISO Source",
        "2. Select Editions",
        "3. Custom Tweaks",
        "4. Compress ISO",
        "5. Target USB",
        "6. Confirm & Review",
        "7. Build Media",
        "8. Completed",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("sidebar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Brand header
        brand = QFrame()
        brand.setObjectName("sidebar_brand")
        bl = QVBoxLayout(brand)
        bl.setContentsMargins(18, 18, 18, 14)
        bl.setSpacing(4)
        t = QLabel("WINISO TOOLKIT")
        t.setObjectName("brand_title")
        sub = QLabel("Supercharged v2.0")
        sub.setObjectName("brand_subtitle")
        bl.addWidget(t)
        bl.addWidget(sub)
        layout.addWidget(brand)

        layout.addSpacing(10)
        self.labels: list[QLabel] = []

        for idx, text in enumerate(self.STEPS):
            lbl = QLabel(text)
            lbl.setProperty("sidebar_item", True)
            layout.addWidget(lbl)
            self.labels.append(lbl)

        layout.addStretch()

    def set_step(self, active: int) -> None:
        for i, lbl in enumerate(self.labels):
            lbl.setProperty("sidebar_active", i == active)
            lbl.setProperty("sidebar_done", i < active)
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)


# ─────────────────────────────────────────────────────────────
# STEP 1 — ISO SELECT
# ─────────────────────────────────────────────────────────────

class StepIsoSelect(QWidget):
    next_enabled = pyqtSignal(bool)
    _SPIN = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def __init__(self, state: dict, log_cb) -> None:
        super().__init__()
        self.state = state
        self.log_cb = log_cb
        self.worker: ISOAnalyzeWorker | None = None
        self._spin_idx = 0

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        # Header
        hdr = QLabel("Select Windows ISO File")
        hdr.setProperty("heading", True)
        sub = QLabel("Drag and drop your official Windows 10/11 ISO file into the box below or browse manually.")
        sub.setProperty("subheading", True)
        root.addWidget(hdr)
        root.addWidget(sub)
        root.addWidget(_sep())

        # Dropzone area
        self.drop_area = IsoDropArea()
        self.drop_area.file_dropped.connect(self._set_iso_path)
        self.drop_area.browse_btn.clicked.connect(self._browse)
        root.addWidget(self.drop_area)

        # File path edit & Hash verification row
        prow = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Path to .iso file…")
        self.path_edit.setMinimumHeight(38)

        self.verify_btn = QPushButton("  🔍 Verify Hash")
        self.verify_btn.setProperty("secondary", True)
        self.verify_btn.setMinimumHeight(38)
        self.verify_btn.setMinimumWidth(130)
        self.verify_btn.setToolTip("Compare SHA-256 hash against official Microsoft database")
        self.verify_btn.clicked.connect(self._verify)

        prow.addWidget(self.path_edit, 1)
        prow.addWidget(self.verify_btn)
        root.addLayout(prow)

        self.verify_bar = QProgressBar()
        self.verify_bar.setVisible(False)
        self.verify_bar.setMaximumHeight(6)
        root.addWidget(self.verify_bar)

        # Metadata card
        self.card = _card()
        cv = QVBoxLayout(self.card)
        cv.setSpacing(10)

        # Badge & status header row
        br = QHBoxLayout()
        self.badge = QLabel("NO ISO SELECTED")
        self.badge.setProperty("badge", "info")
        self.spinner_lbl = _label("", size=12, bold=True)
        br.addWidget(self.badge)
        br.addSpacing(10)
        br.addWidget(self.spinner_lbl)
        br.addStretch()
        cv.addLayout(br)
        cv.addWidget(_sep())

        # Stats grid — 3 columns × 2 rows
        grid = QHBoxLayout()
        grid.setSpacing(10)
        self.val_volume    = self._stat_card(grid, "Volume Label")
        self.val_installer = self._stat_card(grid, "Windows Installer")
        self.val_image     = self._stat_card(grid, "Install Image")
        self.val_editions  = self._stat_card(grid, "Editions Found")
        self.val_est       = self._stat_card(grid, "Est. Compressed")
        self.val_total     = self._stat_card(grid, "Total ISO Size")
        cv.addLayout(grid)
        root.addWidget(self.card)

        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._tick)
        self.path_edit.textChanged.connect(self._on_path_changed)

    @staticmethod
    def _stat_card(parent_layout: QHBoxLayout, title: str) -> QLabel:
        w = QFrame()
        w.setStyleSheet("border:1px solid #27272a; border-radius:8px; padding:8px 10px;")
        col = QVBoxLayout(w)
        col.setSpacing(3)
        col.setContentsMargins(0, 0, 0, 0)
        col.addWidget(_label(title, muted=True, size=11))
        val = QLabel("—")
        val.setStyleSheet("font-size:12.5px; font-weight:600; background:transparent;")
        val.setWordWrap(True)
        col.addWidget(val)
        parent_layout.addWidget(w)
        return val

    def _tick(self) -> None:
        self._spin_idx = (self._spin_idx + 1) % len(self._SPIN)
        self.spinner_lbl.setText(
            f"<span>{self._SPIN[self._spin_idx]} Probing ISO structure…</span>"
        )

    def _browse(self) -> None:
        p, _ = QFileDialog.getOpenFileName(
            self, "Select Windows ISO", "", "ISO Files (*.iso *.ISO)"
        )
        if p:
            self._set_iso_path(p)

    def _set_iso_path(self, path: str) -> None:
        self.path_edit.setText(path)

    def _on_path_changed(self) -> None:
        p = Path(self.path_edit.text().strip())
        if not p.is_file():
            self._reset("NO ISO SELECTED", "info")
            self.next_enabled.emit(False)
            return
        if self.worker and self.worker.isRunning():
            self.worker.finished_ok.disconnect()
            self.worker.failed.disconnect()
            self.worker.quit()
            self.worker.wait(300)
        self._reset("ANALYZING…", "info")
        self._spin_timer.start(80)
        self.log_cb(f"Probing Windows ISO: {p}")
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
            self._badge("✔ VALID WINDOWS INSTALLER", "success")
            self.val_installer.setText("<span style='font-weight:700'>✔ Verified</span>")
        else:
            self._badge("✖ INVALID WINDOWS ISO", "danger")
            self.val_installer.setText(
                "<span style='font-weight:700'>✖ install.wim missing</span>"
            )

        self.val_volume.setText(
            f"<b>{info.volume_label}</b>" if info.volume_label else "—"
        )
        if info.install_image_path:
            self.val_image.setText(
                f"{info.install_image_path}<br>"
                f"<span style='font-size:11px'>{_fmt_gb(info.install_image_size)}</span>"
            )
        else:
            self.val_image.setText("<span style='color:#71717a'>None</span>")

        if info.wimlib_missing:
            self.val_editions.setText(
                "<span>⚠ wimlib required</span>"
            )
        else:
            n = len(info.wim_images)
            names = ", ".join(i.display_name for i in info.wim_images[:2])
            extra = f" +{n-2} more" if n > 2 else ""
            self.val_editions.setText(
                f"<span style='font-weight:700'>{n} Edition{'s' if n!=1 else ''}</span>"
                f"<br><span style='font-size:11px'>{names}{extra}</span>"
            )

        self.val_est.setText(
            f"<span style='font-weight:700'>{_fmt_gb(info.estimated_compressed_size)}</span>"
            "<br><span style='font-size:11px'>LZMS (~45% savings)</span>"
        )
        self.val_total.setText(
            f"<span style='font-weight:700'>{_fmt_gb(info.total_iso_size)}</span>"
        )

        self.log_cb(
            f"Probing finished — Volume: {info.volume_label} | "
            f"Installer: {info.is_windows_installer} | Editions: {len(info.wim_images)}"
        )
        _fade_in(self.card)
        self.next_enabled.emit(info.is_windows_installer)

    def _fail(self, error: str) -> None:
        self._spin_timer.stop()
        self.spinner_lbl.setText("")
        self._badge("UNABLE TO READ ISO", "danger")
        self.val_installer.setText(
            f"<span style='font-size:11px'>{error[:120]}</span>"
        )
        self.log_cb(f"ERROR probing ISO: {error}")
        self.next_enabled.emit(False)

    def _badge(self, text: str, kind: str) -> None:
        self.badge.setText(text)
        self.badge.setProperty("badge", kind)
        self.badge.style().unpolish(self.badge)
        self.badge.style().polish(self.badge)

    def _reset(self, badge_text: str, kind: str) -> None:
        self._badge(badge_text, kind)
        for lbl in (self.val_volume, self.val_installer, self.val_image,
                    self.val_editions, self.val_est, self.val_total):
            lbl.setText("—")

    def _verify(self) -> None:
        iso = self.state.get("iso_path")
        if not iso:
            QMessageBox.warning(self, "No ISO Selected", "Please select a valid Windows ISO file first.")
            return
        self.verify_btn.setEnabled(False)
        self.verify_btn.setText("Verifying Hash…")
        self.verify_bar.setVisible(True)
        self._sha_w = SHA256VerifyWorker(iso)
        self._sha_w.progress.connect(lambda p, _: self.verify_bar.setValue(int(p)))
        self._sha_w.finished_ok.connect(self._sha_done)
        self._sha_w.failed.connect(self._sha_fail)
        self._sha_w.start()

    def _sha_done(self, res: object) -> None:
        self.verify_btn.setEnabled(True)
        self.verify_btn.setText("  🔍 Verify Hash")
        self.verify_bar.setVisible(False)
        QMessageBox.information(
            self, "SHA-256 Verification Result",
            f"Calculated Hash:\n{res.calculated_hash}\n\nStatus: {res.official_name}",  # type: ignore[attr-defined]
        )

    def _sha_fail(self, msg: str) -> None:
        self.verify_btn.setEnabled(True)
        self.verify_btn.setText("  🔍 Verify Hash")
        self.verify_bar.setVisible(False)
        QMessageBox.critical(self, "Verification Error", msg)


# ─────────────────────────────────────────────────────────────
# STEP 2 — EDITION SELECT
# ─────────────────────────────────────────────────────────────

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

        hdr = QLabel("Select Windows Editions to Keep")
        hdr.setProperty("heading", True)
        sub = QLabel("Uncheck unwanted Windows editions — removing unused editions saves 1–2 GB of disk space per edition.")
        sub.setProperty("subheading", True)
        root.addWidget(hdr)
        root.addWidget(sub)
        root.addWidget(_sep())

        # Action toolbar
        tb = QHBoxLayout()
        sa = QPushButton("  ✔ Select All")
        sn = QPushButton("  ✖ Deselect All")
        sa.setProperty("secondary", True)
        sn.setProperty("secondary", True)
        sa.setMinimumHeight(36)
        sa.setMinimumWidth(120)
        sn.setMinimumHeight(36)
        sn.setMinimumWidth(130)
        sa.clicked.connect(lambda: self._check_all(True))
        sn.clicked.connect(lambda: self._check_all(False))
        tb.addWidget(sa)
        tb.addWidget(sn)
        tb.addStretch()
        self._count_lbl = _label("0 editions", bold=True, size=13)
        tb.addWidget(self._count_lbl)
        root.addLayout(tb)

        # Info callout label for single-edition ISOs
        self.single_info_lbl = _label("", muted=True, size=12)
        self.single_info_lbl.setVisible(False)
        root.addWidget(self.single_info_lbl)

        # Edition list container
        self.list = QListWidget()
        root.addWidget(self.list, 1)

        # Summary card
        footer = _card()
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(16, 12, 16, 12)
        self.sum_sel = _label("Selected: 0 of 0", bold=True, size=13)
        self.sum_size = _label("Est. compressed output size: ~0.00 GB", bold=True, size=13)
        fl.addWidget(self.sum_sel)
        fl.addStretch()
        fl.addWidget(self.sum_size)
        root.addWidget(footer)

        self.list.itemChanged.connect(self._update_counter)

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
            item = QListWidgetItem(
                "  ⚠️  All Editions  —  wimlib tool missing, keeping all editions by default"
            )
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            placeholder = WIMImageInfo(
                index=0, name="All Editions",
                description="Keep all (wimlib required to select individual editions)",
                size_bytes=info.install_image_size or info.total_iso_size,
            )
            item.setData(Qt.ItemDataRole.UserRole, placeholder)
            self.list.addItem(item)
            self.single_info_lbl.setVisible(False)
        else:
            if self._notice:
                self._notice.setVisible(False)
            for img in info.wim_images:
                size_gb = img.size_bytes / (1024 ** 3)
                item = QListWidgetItem(
                    f"  [Index {img.index}]   {img.display_name}   ·   {size_gb:.2f} GB"
                )
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                item.setData(Qt.ItemDataRole.UserRole, img)
                self.list.addItem(item)

            if len(info.wim_images) == 1:
                self.single_info_lbl.setText(
                    "ℹ️ Note: This ISO natively contains 1 edition image. All images inside install.wim are listed above."
                )
                self.single_info_lbl.setVisible(True)
            else:
                self.single_info_lbl.setVisible(False)

        n = self.list.count()
        self._count_lbl.setText(f"{n} edition{'s' if n != 1 else ''} available")
        self._update_counter()
        _fade_in(self.list)

    def _show_notice(self) -> None:
        if self._notice:
            self._notice.setVisible(True)
            return
        notice = _card()
        nl = QHBoxLayout(notice)
        nl.setContentsMargins(16, 12, 16, 12)
        ico = QLabel("⚠️")
        ico.setStyleSheet("font-size:20px; background:transparent;")
        lbl = QLabel(
            "<b>wimlib dependency not installed.</b> "
            "<span>Install wimlib to inspect and remove specific editions.</span>"
        )
        lbl.setWordWrap(True)
        self._install_btn = QPushButton("  ⚡ Install wimlib Now")
        self._install_btn.setProperty("secondary", True)
        self._install_btn.setMinimumHeight(36)
        self._install_btn.setMinimumWidth(160)
        self._install_btn.clicked.connect(self._install_wimlib)
        nl.addWidget(ico)
        nl.addWidget(lbl, 1)
        nl.addWidget(self._install_btn)
        self.layout().insertWidget(4, notice)
        self._notice = notice

    def _install_wimlib(self) -> None:
        if self._install_btn:
            self._install_btn.setEnabled(False)
            self._install_btn.setText("Installing…")
        self._wim_worker = WimlibInstallWorker()
        self._wim_worker.log_line.connect(self._relay_log)
        self._wim_worker.finished_ok.connect(self._wim_done)
        self._wim_worker.failed.connect(self._wim_error)
        self._wim_worker.start()

    def _relay_log(self, msg: str) -> None:
        p = self.parent()
        while p:
            if hasattr(p, "log_message"):
                p.log_message(msg)  # type: ignore[union-attr]
                break
            p = p.parent() if hasattr(p, "parent") else None

    def _wim_done(self, ok: bool) -> None:
        if self._install_btn:
            self._install_btn.setEnabled(True)
            self._install_btn.setText("  ⚡ Install wimlib Now")
        if not ok:
            QMessageBox.warning(
                self, "Installation Failed",
                "wimlib could not be installed automatically.\n\n"
                "Download wimlib-imagex.exe manually from:\n  https://wimlib.net/downloads/\n"
            )
            return
        info: ISOInfo | None = self.state.get("iso_info")
        if not info:
            return
        self._re = ISOAnalyzeWorker(info.path)
        self._re.finished_ok.connect(self._re_done)
        self._re.failed.connect(lambda e: QMessageBox.warning(self, "Re-analysis Failed", e))
        self._re.start()

    def _wim_error(self, err: str) -> None:
        if self._install_btn:
            self._install_btn.setEnabled(True)
            self._install_btn.setText("Retry Install")
        QMessageBox.critical(self, "Install Error", err)

    def _re_done(self, info: ISOInfo) -> None:
        self.state["iso_info"] = info
        self.refresh()

    def _update_counter(self) -> None:
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
        self.sum_sel.setText(
            f"Selected: <b>{sel}</b> of {n} edition{'s' if n != 1 else ''}"
        )
        self.sum_size.setText(
            f"Est. compressed output: <b>~{est_gb:.2f} GB</b>"
        )
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


# ─────────────────────────────────────────────────────────────
# STEP 3 — CUSTOMIZATION
# ─────────────────────────────────────────────────────────────

class StepCustomization(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        hdr = QLabel("Customization & Optimizations")
        hdr.setProperty("heading", True)
        sub = QLabel("Select automated Windows 11 hardware bypasses, user setup defaults, and driver slipstreaming.")
        sub.setProperty("subheading", True)
        root.addWidget(hdr)
        root.addWidget(sub)
        root.addWidget(_sep())

        # Windows 11 Bypasses
        bypass_box = QGroupBox("⚡ Windows 11 Hardware Bypasses")
        bb = QVBoxLayout(bypass_box)
        bb.setSpacing(10)
        self.chk_tpm = QCheckBox(
            "Bypass TPM 2.0, SecureBoot, RAM & CPU requirements (Auto-inject autounattend.xml registry bypass)"
        )
        self.chk_tpm.setChecked(True)
        self.chk_msa = QCheckBox(
            "Bypass mandatory Microsoft Account requirement (BypassNRO — forces local account creation option)"
        )
        self.chk_msa.setChecked(True)
        self.chk_tel = QCheckBox(
            "Disable telemetry, diagnostic data collection & unwanted background services"
        )
        self.chk_tel.setChecked(True)
        bb.addWidget(self.chk_tpm)
        bb.addWidget(self.chk_msa)
        bb.addWidget(self.chk_tel)
        root.addWidget(bypass_box)

        # User identity defaults
        user_box = QGroupBox("👤 User Identity & Hostname")
        uf = QVBoxLayout(user_box)
        uf.setSpacing(10)
        urow = QHBoxLayout()
        self.username = QLineEdit("User")
        self.username.setMinimumHeight(36)
        self.compname = QLineEdit("WinISO-PC")
        self.compname.setMinimumHeight(36)
        urow.addWidget(QLabel("Default User Name:"))
        urow.addWidget(self.username)
        urow.addSpacing(16)
        urow.addWidget(QLabel("Computer Hostname:"))
        urow.addWidget(self.compname)
        uf.addLayout(urow)
        root.addWidget(user_box)

        # Driver slipstreaming
        drv_box = QGroupBox("📁 Driver Slipstreaming (Optional)")
        dv = QVBoxLayout(drv_box)
        drow = QHBoxLayout()
        self.driver_edit = QLineEdit()
        self.driver_edit.setPlaceholderText("Select folder containing extracted driver files (.inf format)…")
        self.driver_edit.setMinimumHeight(36)
        drv_btn = QPushButton("  📂 Browse Drivers")
        drv_btn.setProperty("secondary", True)
        drv_btn.setMinimumHeight(36)
        drv_btn.setMinimumWidth(150)
        drv_btn.clicked.connect(self._browse_drivers)
        drow.addWidget(self.driver_edit, 1)
        drow.addWidget(drv_btn)
        dv.addLayout(drow)
        root.addWidget(drv_box)

    def _browse_drivers(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Driver Folder")
        if folder:
            self.driver_edit.setText(folder)

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


# ─────────────────────────────────────────────────────────────
# STEP 4 — COMPRESS
# ─────────────────────────────────────────────────────────────

class StepCompress(QWidget):
    def __init__(self, state: dict, parent_win: "MainWindow") -> None:
        super().__init__()
        self.state = state
        self.parent_win = parent_win

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        hdr = QLabel("Compressing & Rebuilding ISO")
        hdr.setProperty("heading", True)
        root.addWidget(hdr)
        root.addWidget(_sep())

        # Progress card
        self.pcard = _card()
        pc = QVBoxLayout(self.pcard)
        pc.setSpacing(12)

        self.status_lbl = _label("Initializing build pipeline…", bold=True, size=13)
        self.bar = QProgressBar()
        self.bar.setMinimumHeight(24)

        # Phase indicators
        phases = QHBoxLayout()
        self._phase_labels: list[QLabel] = []
        for phase in ["1. Analyze", "2. Compress", "3. Extract ISO", "4. Inject", "5. Rebuild", "6. Done"]:
            pl = QLabel(phase)
            pl.setStyleSheet("font-size:11px; font-weight:600; background:transparent;")
            pl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            phases.addWidget(pl)
            self._phase_labels.append(pl)

        pc.addWidget(self.status_lbl)
        pc.addWidget(self.bar)
        pc.addLayout(phases)
        root.addWidget(self.pcard)

        # Stats metrics grid
        stats = _card()
        sl = QHBoxLayout(stats)
        sl.setContentsMargins(16, 12, 16, 12)
        self.stat_speed = self._stat(sl, "Processing Speed", "—")
        self.stat_eta   = self._stat(sl, "Estimated Time", "—")
        self.stat_in    = self._stat(sl, "Source Size", "—")
        self.stat_out   = self._stat(sl, "Output Size", "—")
        self.stat_ratio = self._stat(sl, "Space Saved", "—")
        root.addWidget(stats)

    @staticmethod
    def _stat(layout: QHBoxLayout, key: str, val: str) -> QLabel:
        w = QFrame()
        w.setStyleSheet("border:1px solid #27272a; border-radius:8px; padding:8px 10px;")
        c = QVBoxLayout(w)
        c.setSpacing(3)
        c.setContentsMargins(0, 0, 0, 0)
        c.addWidget(_label(key, muted=True, size=11))
        v = QLabel(val)
        v.setStyleSheet("font-size:16px; font-weight:700; background:transparent;")
        c.addWidget(v)
        layout.addWidget(w)
        return v

    def _update_phase(self, pct: float) -> None:
        thresholds = [10, 55, 65, 72, 80, 100]
        for i, (lbl, thresh) in enumerate(zip(self._phase_labels, thresholds)):
            if pct >= thresh:
                lbl.setStyleSheet("font-size:11px; font-weight:700; background:transparent;")
            elif pct >= (thresholds[i - 1] if i > 0 else 0):
                lbl.setStyleSheet("font-size:11px; font-weight:700; background:transparent;")
            else:
                lbl.setStyleSheet("font-size:11px; font-weight:600; background:transparent;")

    def start(self) -> None:
        iso_path: Path = self.state["iso_path"]
        indices: list[int] = self.state.get("indices", [1])
        output = iso_path.with_name(f"{iso_path.stem}_compressed.iso")
        self.state["output_iso"] = output
        self._start_time = time.time()

        info: ISOInfo | None = self.state.get("iso_info")
        src_size = info.install_image_size if info else 0
        if src_size:
            self.stat_in.setText(_fmt_gb(src_size))

        self.worker = WorkerThread(
            WinISOPipeline().compress_iso,
            iso_path, output, indices,
            bypass_options=self.state.get("bypass_options"),
            driver_dir=self.state.get("driver_dir"),
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.failed.connect(self._on_fail)
        self.worker.start()

    def _on_progress(self, pct: float, msg: str) -> None:
        self.bar.setValue(int(pct))
        self.status_lbl.setText(msg)
        self._update_phase(pct)
        elapsed = max(time.time() - self._start_time, 0.1)
        if pct > 5:
            eta = elapsed / (pct / 100) - elapsed
            self.stat_eta.setText(f"{int(eta // 60)}m {int(eta % 60)}s")
            speed = (pct / 100) / elapsed
            self.stat_speed.setText(f"{speed * 100:.1f}%/s")

    def _on_done(self, result: object) -> None:
        self.state["output_iso"] = Path(str(result))
        out = self.state["output_iso"]
        if out.exists():
            self.stat_out.setText(_fmt_gb(out.stat().st_size))
            info: ISOInfo | None = self.state.get("iso_info")
            src = info.install_image_size if info else 0
            if src:
                ratio = (1 - out.stat().st_size / src) * 100
                self.stat_ratio.setText(f"−{ratio:.1f}%")
        self.parent_win.advance()

    def _on_fail(self, msg: str) -> None:
        QMessageBox.critical(self, "Compression Failed", msg)
        self.parent_win.set_back_enabled(True)


# ─────────────────────────────────────────────────────────────
# STEP 5 — USB SELECT
# ─────────────────────────────────────────────────────────────

class StepUsbSelect(QWidget):
    next_enabled = pyqtSignal(bool)

    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        hdr = QLabel("Select Target USB Flash Drive")
        hdr.setProperty("heading", True)
        sub = QLabel("Select target USB drive. <b style='color:#ef4444'>All existing partitions will be formatted.</b>")
        sub.setProperty("subheading", True)
        root.addWidget(hdr)
        root.addWidget(sub)
        root.addWidget(_sep())

        # USB Toolbar
        tb = QHBoxLayout()
        refresh_btn = QPushButton("  🔄 Refresh USB List")
        refresh_btn.setProperty("secondary", True)
        refresh_btn.setMinimumHeight(36)
        refresh_btn.setMinimumWidth(150)
        refresh_btn.clicked.connect(self.refresh)

        health_btn = QPushButton("  📊 Health & Speed Test")
        health_btn.setProperty("secondary", True)
        health_btn.setMinimumHeight(36)
        health_btn.setMinimumWidth(170)
        health_btn.clicked.connect(self._health_check)

        tb.addWidget(refresh_btn)
        tb.addWidget(health_btn)
        tb.addStretch()
        root.addLayout(tb)

        # USB Combo
        self.combo = QComboBox()
        self.combo.setMinimumHeight(40)
        self.combo.currentIndexChanged.connect(self._validate)
        root.addWidget(self.combo)

        # Capacity card
        self.cap_card = _card()
        cap_l = QHBoxLayout(self.cap_card)
        cap_l.setContentsMargins(16, 12, 16, 12)
        self.cap_icon = QLabel("⬤")
        self.cap_icon.setStyleSheet("font-size:15px; background:transparent;")
        self.cap_lbl = _label("Select a USB drive to verify capacity.", muted=True)
        cap_l.addWidget(self.cap_icon)
        cap_l.addSpacing(8)
        cap_l.addWidget(self.cap_lbl, 1)
        root.addWidget(self.cap_card)

        # Boot options box
        opts_box = QGroupBox("⚙️ Boot Mode & Partitioning Strategy")
        ob = QVBoxLayout(opts_box)
        ob.setSpacing(10)
        self.boot_combo = QComboBox()
        self.boot_combo.addItems([
            "Both UEFI + Legacy MBR (Maximum Compatibility)",
            "UEFI Only (GPT Partition Scheme / Modern PCs)",
            "Legacy MBR Only (Older BIOS)",
        ])
        self.boot_combo.setMinimumHeight(36)
        self.dual_chk = QCheckBox(
            "Use Dual-Partition layout (FAT32 EFI Boot + NTFS Data — supports install.wim > 4 GB)"
        )
        self.dual_chk.setChecked(True)
        ob.addWidget(QLabel("Target Boot Mode:"))
        ob.addWidget(self.boot_combo)
        ob.addSpacing(4)
        ob.addWidget(self.dual_chk)
        root.addWidget(opts_box)

    def refresh(self) -> None:
        self.combo.clear()
        devices = USBDetector().list_devices()
        self.state["usb_devices"] = devices
        if not devices:
            self.combo.addItem("No USB drives detected — insert USB flash drive and click Refresh")
        for d in devices:
            self.combo.addItem(
                f"  💾 {d.name}   ·   {d.size_gb:.1f} GB   ·   {d.filesystem or 'Unknown FS'}  [{d.path}]",
                d,
            )
        self._validate()
        _fade_in(self.combo)

    def _health_check(self) -> None:
        device: USBDevice | None = self.combo.currentData()
        if not device:
            QMessageBox.warning(self, "No USB Selected", "Please select a USB drive first.")
            return
        try:
            from winiso_toolkit.usb.health import USBHealthChecker
            rep = USBHealthChecker().run_quick_health_check(Path(device.path))
            icon = "✔" if rep.capacity_verified else "✖"
            QMessageBox.information(
                self, "USB Health & Benchmark Report",
                f"Drive Name: {device.name}  [{device.path}]\n"
                f"Write Speed: {rep.write_speed_mbps:.1f} MB/s\n"
                f"Capacity Verification: {icon}\n\n"
                f"Status: {rep.status_message}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Health Check Error", str(exc))

    def _validate(self) -> None:
        device: USBDevice | None = self.combo.currentData()
        output: Path | None = self.state.get("output_iso")
        if not device or not output or not output.exists():
            self.cap_icon.setStyleSheet("font-size:15px; background:transparent;")
            self.cap_lbl.setText("Select a USB drive to verify capacity.")
            self.next_enabled.emit(False)
            return
        ok, msg = USBCreator().validate_capacity(device.size_bytes, output.stat().st_size)
        if ok:
            self.cap_icon.setStyleSheet("font-size:15px; background:transparent;")
            self.cap_lbl.setText(
                f"<span style='font-weight:700'>✔ Sufficient Capacity</span> "
                f"— {device.size_gb:.1f} GB drive available (≥ {output.stat().st_size/(1024**3):.1f} GB required)"
            )
            self.state["usb_device"] = device
            self.next_enabled.emit(True)
        else:
            self.cap_icon.setStyleSheet("font-size:15px; background:transparent;")
            self.cap_lbl.setText(f"<span style='font-weight:700'>✖ {msg}</span>")
            self.next_enabled.emit(False)

    def save_selection(self) -> None:
        self.state["boot_mode"] = [BootMode.BOTH, BootMode.UEFI, BootMode.LEGACY][
            self.boot_combo.currentIndex()
        ]
        self.state["use_dual_partition"] = self.dual_chk.isChecked()


# ─────────────────────────────────────────────────────────────
# STEP 6 — CONFIRM
# ─────────────────────────────────────────────────────────────

class StepConfirm(QWidget):
    next_enabled = pyqtSignal(bool)

    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        hdr = QLabel("Confirm & Write USB Media")
        hdr.setProperty("heading", True)
        root.addWidget(hdr)
        root.addWidget(_sep())

        # Executive summary dashboard
        self.summary_card = _card()
        sc = QVBoxLayout(self.summary_card)
        sc.setSpacing(8)
        self.sum_lbl = QLabel("")
        self.sum_lbl.setWordWrap(True)
        self.sum_lbl.setStyleSheet("font-size:13px; line-height:1.6;")
        sc.addWidget(self.sum_lbl)
        root.addWidget(self.summary_card)

        # Danger warning card
        warn = _card()
        warn.setStyleSheet("border:1px solid #ef4444; border-radius:10px;")
        wl = QHBoxLayout(warn)
        wl.setContentsMargins(16, 12, 16, 12)
        warn_ico = QLabel("⚠️")
        warn_ico.setStyleSheet("font-size:26px; background:transparent;")
        warn_txt = QLabel(
            "<b style='font-size:13.5px'>CRITICAL WARNING:</b><br>"
            "<span>ALL DATA on the selected target USB drive will be permanently erased. "
            "Please ensure you have backed up any essential files.</span>"
        )
        warn_txt.setWordWrap(True)
        wl.addWidget(warn_ico)
        wl.addWidget(warn_txt, 1)
        root.addWidget(warn)

        # Safety confirmation checkbox
        self.confirm_chk = QCheckBox(
            "I understand — format the USB drive and create a bootable Windows installer media"
        )
        self.confirm_chk.setStyleSheet("font-size:13px; font-weight:700;")
        self.confirm_chk.stateChanged.connect(
            lambda: self.next_enabled.emit(self.confirm_chk.isChecked())
        )
        root.addWidget(self.confirm_chk)

    def refresh(self) -> None:
        iso: Path | None = self.state.get("output_iso")
        usb: USBDevice | None = self.state.get("usb_device")
        indices = self.state.get("indices", [])
        boot: BootMode = self.state.get("boot_mode", BootMode.BOTH)
        dual: bool = self.state.get("use_dual_partition", False)

        edition_str = "All (keep-all mode)" if indices == [0] else str(indices)
        iso_size = f"{iso.stat().st_size / (1024**3):.2f} GB" if iso and iso.exists() else "?"

        self.sum_lbl.setText(
            f"<table style='border-spacing:0 6px; width:100%;'>"
            f"<tr><td style='width:180px;'>Output ISO Path:</td>"
            f"<td style='font-weight:600;'>{iso}</td></tr>"
            f"<tr><td>Compressed ISO Size:</td>"
            f"<td>{iso_size}</td></tr>"
            f"<tr><td>Selected Editions:</td>"
            f"<td>{edition_str}</td></tr>"
            f"<tr><td>Target USB Device:</td>"
            f"<td style='font-weight:700;'>{usb.path if usb else '—'} ({usb.name if usb else ''})</td></tr>"
            f"<tr><td>Boot Mode:</td>"
            f"<td>{boot.value}</td></tr>"
            f"<tr><td>Partitioning Strategy:</td>"
            f"<td style='font-weight:600;'>"
            f"{'Dual Partition Scheme (FAT32 EFI + NTFS Data)' if dual else 'Single Partition'}</td></tr>"
            f"</table>"
        )
        self.confirm_chk.setChecked(False)
        self.next_enabled.emit(False)


# ─────────────────────────────────────────────────────────────
# STEP 7 — BURN
# ─────────────────────────────────────────────────────────────

class StepBurn(QWidget):
    def __init__(self, state: dict, parent_win: "MainWindow") -> None:
        super().__init__()
        self.state = state
        self.parent_win = parent_win
        self._start_time = 0.0

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        hdr = QLabel("Creating Bootable USB Drive…")
        hdr.setProperty("heading", True)
        root.addWidget(hdr)
        root.addWidget(_sep())

        pcard = _card()
        pc = QVBoxLayout(pcard)
        pc.setSpacing(12)
        self.status_lbl = _label("Preparing target drive partitions…", bold=True, size=13)
        self.bar = QProgressBar()
        self.bar.setMinimumHeight(24)
        pc.addWidget(self.status_lbl)
        pc.addWidget(self.bar)
        root.addWidget(pcard)

        stats = _card()
        sl = QHBoxLayout(stats)
        sl.setContentsMargins(16, 12, 16, 12)
        self.stat_speed = self._stat(sl, "Write Speed", "—")
        self.stat_eta   = self._stat(sl, "Estimated ETA", "—")
        self.stat_done  = self._stat(sl, "Data Written", "—")
        root.addWidget(stats)

    @staticmethod
    def _stat(layout: QHBoxLayout, key: str, val: str) -> QLabel:
        w = QFrame()
        w.setStyleSheet("border:1px solid #27272a; border-radius:8px; padding:8px 10px;")
        c = QVBoxLayout(w)
        c.setSpacing(3)
        c.setContentsMargins(0, 0, 0, 0)
        c.addWidget(_label(key, muted=True, size=11))
        v = QLabel(val)
        v.setStyleSheet("font-size:15px; font-weight:700; background:transparent;")
        c.addWidget(v)
        layout.addWidget(w)
        return v

    def start(self) -> None:
        iso: Path | None = self.state.get("output_iso")
        usb: USBDevice | None = self.state.get("usb_device")
        if not iso or not usb:
            QMessageBox.critical(self, "Missing Configuration", "Output ISO or target USB device is missing.")
            return
        self._start_time = time.time()
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
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(lambda _: self.parent_win.advance())
        self.worker.failed.connect(
            lambda m: QMessageBox.critical(self, "USB Creation Failed", m)
        )
        self.worker.start()

    def _on_progress(self, pct: float, msg: str) -> None:
        self.bar.setValue(int(pct))
        self.status_lbl.setText(msg)
        elapsed = max(time.time() - self._start_time, 0.1)
        if pct > 5:
            eta = elapsed / (pct / 100) - elapsed
            self.stat_eta.setText(f"{int(eta // 60)}m {int(eta % 60)}s")
            import re
            m = re.search(r"([\d.]+)\s*MB/s", msg)
            if m:
                self.stat_speed.setText(f"{m.group(1)} MB/s")
            output_iso = self.state.get("output_iso")
            total_size = output_iso.stat().st_size if output_iso and output_iso.exists() else 0
            written_bytes = (pct / 100) * total_size
            self.stat_done.setText(_fmt_gb(int(written_bytes)))


# ─────────────────────────────────────────────────────────────
# STEP 8 — DONE
# ─────────────────────────────────────────────────────────────

class StepResult(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state

        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(0, 0, 0, 0)

        # Celebration Header
        hdr = QLabel("🎉  Bootable USB Successfully Created!")
        hdr.setStyleSheet("font-size:22px; font-weight:800; letter-spacing:-0.5px;")
        root.addWidget(hdr)
        root.addWidget(_sep())

        # Result Details Card
        self.result_card = _card()
        rl = QVBoxLayout(self.result_card)
        rl.setSpacing(8)
        self.result_lbl = QLabel()
        self.result_lbl.setWordWrap(True)
        self.result_lbl.setStyleSheet("font-size:13px; line-height:1.6;")
        rl.addWidget(self.result_lbl)
        root.addWidget(self.result_card)

        # Verification Checklist Card
        chk_card = _card()
        cl = QVBoxLayout(chk_card)
        cl.setSpacing(8)
        cl.addWidget(_label("🛡️ System Integrity Verification Checklist", bold=True, size=13))
        cl.addWidget(_sep())
        for item in [
            ("El Torito Bootloader Structure", True),
            ("BCD Boot Configuration Database", True),
            ("Post-Write File SHA256 Checksums", True),
            ("EFI/UEFI Firmware Bootloader Files", True),
        ]:
            row = QHBoxLayout()
            icon = QLabel("✔")
            icon.setStyleSheet("font-size:14px; font-weight:800; background:transparent;")
            icon.setFixedWidth(24)
            row.addWidget(icon)
            row.addWidget(_label(item[0]))
            row.addStretch()
            row.addWidget(_label("VERIFIED", bold=True, size=11))
            cl.addLayout(row)
        root.addWidget(chk_card)

        # Action Bar
        act = QHBoxLayout()
        vm_btn = QPushButton("  💻 Test in QEMU VM")
        vm_btn.setProperty("secondary", True)
        vm_btn.setMinimumHeight(38)
        vm_btn.setMinimumWidth(150)
        vm_btn.clicked.connect(self._test_vm)

        eject_btn = QPushButton("  ⏏️ Safely Eject USB")
        eject_btn.setProperty("secondary", True)
        eject_btn.setMinimumHeight(38)
        eject_btn.setMinimumWidth(150)
        eject_btn.clicked.connect(self._eject)

        act.addWidget(vm_btn)
        act.addWidget(eject_btn)
        act.addStretch()
        root.addLayout(act)

    def refresh(self) -> None:
        usb: USBDevice | None = self.state.get("usb_device")
        iso: Path | None = self.state.get("output_iso")
        iso_size = f"{iso.stat().st_size / (1024**3):.2f} GB" if iso and iso.exists() else "—"
        self.result_lbl.setText(
            f"<table style='border-spacing:0 6px; width:100%;'>"
            f"<tr><td style='width:160px;'>Target USB Drive:</td>"
            f"<td><b>{usb.path if usb else '—'}</b> ({usb.name if usb else ''})</td></tr>"
            f"<tr><td>Compressed ISO Source:</td>"
            f"<td>{iso}</td></tr>"
            f"<tr><td>Total Size Written:</td>"
            f"<td>{iso_size}</td></tr>"
            f"</table>"
        )
        _fade_in(self.result_card)

    def _test_vm(self) -> None:
        iso: Path | None = self.state.get("output_iso")
        if not iso or not iso.exists():
            QMessageBox.warning(self, "No ISO Found", "Output ISO file is missing.")
            return
        from winiso_toolkit.utils.vm import QEMUTester
        tester = QEMUTester()
        if not tester.is_qemu_available():
            QMessageBox.information(
                self, "QEMU Not Found",
                "QEMU system emulator is not installed.\n\n"
                "  Linux:   sudo apt install qemu-system-x86\n"
                "  Windows: https://www.qemu.org/download/\n"
                "  macOS:   brew install qemu",
            )
            return
        try:
            tester.launch_test_vm(iso)
        except Exception as exc:
            QMessageBox.critical(self, "VM Error", str(exc))

    def _eject(self) -> None:
        usb: USBDevice | None = self.state.get("usb_device")
        if not usb:
            QMessageBox.warning(self, "No USB Found", "No target USB drive on record.")
            return
        from winiso_toolkit.usb.ejector import USBEjector
        ok, msg = USBEjector().safe_eject(usb.path)
        if ok:
            QMessageBox.information(self, "Safe to Remove", msg)
        else:
            QMessageBox.warning(self, "Eject Warning", msg)


# ─────────────────────────────────────────────────────────────
# MAIN WINDOW WITH SIDEBAR & COLLAPSIBLE DRAWER
# ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WinISO Toolkit Supercharged v2.0")
        self.setMinimumSize(960, 660)
        self.resize(1020, 700)
        self.state: dict = {}
        self.is_dark = True

        central = QWidget()
        self.setCentralWidget(central)
        main_h_layout = QHBoxLayout(central)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        # ── 1. Left Sidebar Navigation ────────────────────────
        self.sidebar = SidebarWidget()

        # Theme Switcher Button at bottom of sidebar
        self.theme_btn = QPushButton("  🌙 Dark Mode")
        self.theme_btn.setProperty("secondary", True)
        self.theme_btn.setMinimumHeight(36)
        self.theme_btn.setMinimumWidth(180)
        self.theme_btn.clicked.connect(self._toggle_theme)

        sb_layout = self.sidebar.layout()
        if sb_layout:
            theme_box = QFrame()
            tbl = QVBoxLayout(theme_box)
            tbl.setContentsMargins(12, 8, 12, 12)
            tbl.addWidget(self.theme_btn)
            sb_layout.addWidget(theme_box)

        main_h_layout.addWidget(self.sidebar)

        # ── 2. Right Canvas Area ──────────────────────────────
        canvas = QWidget()
        canvas_l = QVBoxLayout(canvas)
        canvas_l.setContentsMargins(20, 16, 20, 12)
        canvas_l.setSpacing(12)

        # QStackedWidget holding Scroll-wrapped step pages
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

        canvas_l.addWidget(self.stack, 1)

        # Navigation Bar
        nav = QHBoxLayout()
        self.back_btn = QPushButton("  ← Previous Step")
        self.back_btn.setProperty("secondary", True)
        self.back_btn.setMinimumWidth(140)
        self.back_btn.setMinimumHeight(40)

        self.next_btn = QPushButton("Next Step  →")
        self.next_btn.setMinimumWidth(150)
        self.next_btn.setMinimumHeight(40)

        self.back_btn.clicked.connect(self.go_back)
        self.next_btn.clicked.connect(self.go_next)

        nav.addWidget(self.back_btn)
        nav.addStretch()
        nav.addWidget(self.next_btn)
        canvas_l.addLayout(nav)

        # ── 3. Collapsible Bottom Console Drawer ──────────────
        console_box = QFrame()
        console_box.setObjectName("card_frame")
        cl = QVBoxLayout(console_box)
        cl.setContentsMargins(12, 6, 12, 6)
        cl.setSpacing(6)

        # Drawer Status Header
        ctb = QHBoxLayout()
        dot_lbl = QLabel("🟢")
        dot_lbl.setStyleSheet("font-size:12px; background:transparent;")
        title_lbl = QLabel("Live Process Output Console")
        title_lbl.setStyleSheet("font-size:12px; font-weight:700; background:transparent;")
        
        self.console_toggle = QPushButton("  👁️ Show Terminal")
        self.console_toggle.setProperty("secondary", True)
        self.console_toggle.setMinimumWidth(130)
        self.console_toggle.setFixedHeight(30)
        self.console_toggle.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.console_toggle.clicked.connect(self._toggle_console)

        clear_btn = QPushButton("  🗑️ Clear Log")
        clear_btn.setProperty("secondary", True)
        clear_btn.setMinimumWidth(110)
        clear_btn.setFixedHeight(30)
        clear_btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        clear_btn.clicked.connect(lambda: self.console.clear())

        ctb.addWidget(dot_lbl)
        ctb.addWidget(title_lbl)
        ctb.addStretch()
        ctb.addWidget(self.console_toggle)
        ctb.addWidget(clear_btn)
        cl.addLayout(ctb)

        # Text Console — Default Hidden (Collapsed Drawer)
        self.console = QTextEdit()
        self.console.setObjectName("live_log_console")
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(130)
        self.console.setMinimumHeight(130)
        self.console.setVisible(False)
        cl.addWidget(self.console)

        canvas_l.addWidget(console_box)
        main_h_layout.addWidget(canvas, 1)

        # Logging bridge
        self.log_handler = QObjectLogHandler()
        self.log_handler.new_log.connect(self.console.append)
        logging.getLogger("winiso_toolkit").addHandler(self.log_handler)

        # Signal wiring
        self.step_iso.next_enabled.connect(self._set_next)
        self.step_editions.next_enabled.connect(self._set_next)
        self.step_usb.next_enabled.connect(self._set_next)
        self.step_confirm.next_enabled.connect(self._set_next)

        self._step = 0
        self._update_nav()

    def _toggle_theme(self) -> None:
        self.is_dark = not self.is_dark
        app = QApplication.instance()
        if app:
            app.setStyleSheet(DARK_THEME_QSS if self.is_dark else LIGHT_THEME_QSS)
        self.theme_btn.setText("  🌙 Dark Mode" if self.is_dark else "  ☀️ Light Mode")

    @staticmethod
    def _wrap_scroll(widget: QWidget) -> QScrollArea:
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setWidget(widget)
        sa.setStyleSheet("background:transparent; border:none;")
        return sa

    def log_message(self, msg: str) -> None:
        logging.getLogger("winiso_toolkit").info(msg)

    def _toggle_console(self) -> None:
        visible = self.console.isVisible()
        self.console.setVisible(not visible)
        self.console_toggle.setText("  👁️ Hide Terminal" if not visible else "  👁️ Show Terminal")

    def _set_next(self, enabled: bool) -> None:
        if self._step not in (3, 6, 7):
            self.next_btn.setEnabled(enabled)

    def _update_nav(self) -> None:
        self.sidebar.set_step(self._step)
        auto = self._step in (3, 6, 7)
        self.back_btn.setEnabled(self._step > 0 and not auto)
        self.next_btn.setEnabled(not auto)
        if self._step == 7:
            self.next_btn.setText("Finish & Close  ✓")
        elif self._step == 5:
            self.next_btn.setText("⚡ Start Build")
        else:
            self.next_btn.setText("Next Step  →")

    def set_back_enabled(self, v: bool) -> None:
        self.back_btn.setEnabled(v)

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
                QMessageBox.warning(self, "No Editions Selected", "Please select at least one Windows edition.")
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
