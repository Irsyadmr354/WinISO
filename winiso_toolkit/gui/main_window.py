"""WinISO Toolkit — PyQt6 Deep Space Dark Wizard UI."""

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
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from winiso_toolkit.deps.installer import DependencyInstaller
from winiso_toolkit.iso.analyzer import ISOAnalyzer, ISOInfo, WIMImageInfo
from winiso_toolkit.pipeline import WinISOPipeline
from winiso_toolkit.usb.creator import BootMode, USBCreator
from winiso_toolkit.usb.detector import USBDevice, USBDetector

# ─────────────────────────────────────────────────────────────
# UTILITIES
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
        parts.append("color:#64748b;")
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


def _fade_in(widget: QWidget, ms: int = 260) -> None:
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

# ─────────────────────────────────────────────────────────────
# LOG HANDLER
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
            colors = {"INFO": "#22d3ee", "WARNING": "#fbbf24",
                      "ERROR": "#f87171", "DEBUG": "#64748b"}
            c = colors.get(record.levelname, "#94a3b8")
            html = (
                f"<span style='color:#334155'>[{ts}]</span> "
                f"<span style='color:{c};font-weight:600'>[{record.levelname}]</span> "
                f"<span style='color:#cbd5e1'>{msg}</span>"
            )
            self._bridge.new_log.emit(html)
        except (OSError, RuntimeError):
            pass


# ─────────────────────────────────────────────────────────────
# BACKGROUND WORKERS
# ─────────────────────────────────────────────────────────────

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
# STEP INDICATOR BAR
# ─────────────────────────────────────────────────────────────

class StepIndicatorWidget(QFrame):
    STEPS = ["1. ISO", "2. Editions", "3. Custom", "4. Compress",
             "5. USB", "6. Confirm", "7. Build", "8. Done"]

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("step_bar")
        self.setFixedHeight(46)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(0)
        self.labels: list[QLabel] = []

        for idx, text in enumerate(self.STEPS):
            lbl = QLabel(text)
            lbl.setProperty("step_item", True)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedHeight(30)
            layout.addWidget(lbl)
            self.labels.append(lbl)
            if idx < len(self.STEPS) - 1:
                arrow = QLabel("›")
                arrow.setStyleSheet(
                    "color:#1e293b; font-size:16px; font-weight:300;"
                    "background:transparent;"
                )
                arrow.setFixedWidth(18)
                arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(arrow)

        layout.addStretch()

    def set_step(self, active: int) -> None:
        for i, lbl in enumerate(self.labels):
            lbl.setProperty("step_active", i == active)
            lbl.setProperty("step_done", i < active)
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
        hdr = QLabel("Select Windows ISO")
        hdr.setStyleSheet("color:#f1f5f9;font-size:22px;font-weight:700;")
        sub = _label("Browse to an official Windows 10 or 11 installer .iso file.", muted=True)
        root.addWidget(hdr)
        root.addWidget(sub)
        root.addWidget(_sep())

        # File picker
        row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("  Path to .iso file…")
        self.path_edit.setMinimumHeight(40)
        browse = QPushButton("Browse…")
        browse.setFixedWidth(100)
        browse.setMinimumHeight(40)
        browse.clicked.connect(self._browse)
        row.addWidget(self.path_edit, 1)
        row.addWidget(browse)
        root.addLayout(row)

        # Metadata card
        self.card = _card()
        cv = QVBoxLayout(self.card)
        cv.setSpacing(12)

        # Badge row
        br = QHBoxLayout()
        self.badge = QLabel("NO ISO SELECTED")
        self.badge.setProperty("badge", "info")
        self.spinner_lbl = _label("", color="#38bdf8", size=12)
        br.addWidget(self.badge)
        br.addSpacing(8)
        br.addWidget(self.spinner_lbl)
        br.addStretch()
        cv.addLayout(br)
        cv.addWidget(_sep())

        # Stats grid — 3 columns × 2 rows
        grid = QHBoxLayout()
        grid.setSpacing(12)
        self.val_volume    = self._stat_col(grid, "Volume Label")
        self.val_installer = self._stat_col(grid, "Windows Installer")
        self.val_image     = self._stat_col(grid, "Install Image")
        self.val_editions  = self._stat_col(grid, "Editions Found")
        self.val_est       = self._stat_col(grid, "Est. Compressed")
        self.val_total     = self._stat_col(grid, "Total Size")
        cv.addLayout(grid)
        root.addWidget(self.card)

        # Verify SHA-256 row
        vrow = QHBoxLayout()
        self.verify_btn = QPushButton("  Verify SHA-256 Checksum")
        self.verify_btn.setProperty("secondary", True)
        self.verify_btn.setToolTip("Compare against official Microsoft hashes")
        self.verify_btn.clicked.connect(self._verify)
        self.verify_bar = QProgressBar()
        self.verify_bar.setVisible(False)
        self.verify_bar.setMaximumHeight(6)
        vrow.addWidget(self.verify_btn)
        vrow.addWidget(self.verify_bar, 1)
        root.addLayout(vrow)
        root.addStretch()

        # Spinner timer
        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._tick)

        self.path_edit.textChanged.connect(self._on_path_changed)

    @staticmethod
    def _stat_col(parent_layout: QHBoxLayout, title: str) -> QLabel:
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        col = QVBoxLayout(w)
        col.setSpacing(3)
        col.setContentsMargins(0, 0, 0, 0)
        col.addWidget(_label(title, muted=True, size=11))
        val = QLabel("—")
        val.setStyleSheet("color:#e2e8f0; font-size:13px; background:transparent;")
        val.setWordWrap(True)
        col.addWidget(val)
        parent_layout.addWidget(w)
        return val

    def _tick(self) -> None:
        self._spin_idx = (self._spin_idx + 1) % len(self._SPIN)
        self.spinner_lbl.setText(
            f"<span style='color:#38bdf8'>{self._SPIN[self._spin_idx]} Analyzing…</span>"
        )

    def _browse(self) -> None:
        p, _ = QFileDialog.getOpenFileName(
            self, "Select Windows ISO", "", "ISO Files (*.iso *.ISO)"
        )
        if p:
            self.path_edit.setText(p)

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
        self.log_cb(f"Opening and probing ISO: {p}")
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
            self._badge("✔  VALID WINDOWS INSTALLER", "success")
            self.val_installer.setText("<span style='color:#4ade80'>✔  Yes</span>")
        else:
            self._badge("✖  INVALID WINDOWS ISO", "danger")
            self.val_installer.setText(
                "<span style='color:#f87171'>✖  install.wim not found</span>"
            )

        self.val_volume.setText(
            f"<b>{info.volume_label}</b>" if info.volume_label else "—"
        )
        if info.install_image_path:
            self.val_image.setText(
                f"{info.install_image_path}<br>"
                f"<span style='color:#38bdf8'>{_fmt_gb(info.install_image_size)}</span>"
            )
        else:
            self.val_image.setText("<span style='color:#64748b'>None</span>")

        if info.wimlib_missing:
            self.val_editions.setText(
                "<span style='color:#fbbf24'>⚠ wimlib missing</span>"
            )
        else:
            n = len(info.wim_images)
            names = ", ".join(i.display_name for i in info.wim_images[:2])
            extra = f" +{n-2} more" if n > 2 else ""
            self.val_editions.setText(
                f"<span style='color:#4ade80'>{n} edition{'s' if n!=1 else ''}</span>"
                f"<br><span style='color:#64748b;font-size:11px'>{names}{extra}</span>"
            )

        self.val_est.setText(
            f"<span style='color:#38bdf8'>{_fmt_gb(info.estimated_compressed_size)}</span>"
            "<br><span style='color:#64748b;font-size:11px'>LZMS ~45%</span>"
        )
        self.val_total.setText(
            f"<span style='color:#e2e8f0'>{_fmt_gb(info.total_iso_size)}</span>"
        )

        n = len(info.wim_images)
        self.log_cb(
            f"ISO analysis complete — Volume: {info.volume_label} | "
            f"Valid: {info.is_windows_installer} | Editions: {n}"
            + (" [wimlib missing]" if info.wimlib_missing else "")
        )
        _fade_in(self.card)
        self.next_enabled.emit(info.is_windows_installer)

    def _fail(self, error: str) -> None:
        self._spin_timer.stop()
        self.spinner_lbl.setText("")
        self._badge("UNABLE TO READ ISO", "danger")
        self.val_installer.setText(
            f"<span style='color:#f87171;font-size:11px'>{error[:120]}</span>"
        )
        self.log_cb(f"ERROR reading ISO: {error}")
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
            QMessageBox.warning(self, "No ISO", "Select an ISO file first.")
            return
        self.verify_btn.setEnabled(False)
        self.verify_btn.setText("Verifying…")
        self.verify_bar.setVisible(True)
        self._sha_w = SHA256VerifyWorker(iso)
        self._sha_w.progress.connect(lambda p, _: self.verify_bar.setValue(int(p)))
        self._sha_w.finished_ok.connect(self._sha_done)
        self._sha_w.failed.connect(self._sha_fail)
        self._sha_w.start()

    def _sha_done(self, res: object) -> None:
        self.verify_btn.setEnabled(True)
        self.verify_btn.setText("  Verify SHA-256 Checksum")
        self.verify_bar.setVisible(False)
        QMessageBox.information(
            self, "SHA-256 Result",
            f"Hash:\n{res.calculated_hash}\n\nStatus: {res.official_name}",  # type: ignore[attr-defined]
        )

    def _sha_fail(self, msg: str) -> None:
        self.verify_btn.setEnabled(True)
        self.verify_btn.setText("  Verify SHA-256 Checksum")
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
        root.setSpacing(12)
        root.setContentsMargins(0, 0, 0, 0)

        hdr = QLabel("Select Editions to Keep")
        hdr.setStyleSheet("color:#f1f5f9;font-size:22px;font-weight:700;")
        sub = _label("Uncheck editions you don't need — each removed edition saves ~1–2 GB.", muted=True)
        root.addWidget(hdr)
        root.addWidget(sub)
        root.addWidget(_sep())

        # Toolbar
        tb = QHBoxLayout()
        sa = QPushButton("Select All")
        sn = QPushButton("Deselect All")
        sa.setProperty("secondary", True)
        sn.setProperty("secondary", True)
        sa.setFixedHeight(32)
        sn.setFixedHeight(32)
        sa.clicked.connect(lambda: self._check_all(True))
        sn.clicked.connect(lambda: self._check_all(False))
        tb.addWidget(sa)
        tb.addWidget(sn)
        tb.addStretch()
        self._count_lbl = _label("0 editions", muted=True, size=12)
        tb.addWidget(self._count_lbl)
        root.addLayout(tb)

        # Edition list
        self.list = QListWidget()
        root.addWidget(self.list, 1)

        # Footer summary card
        footer = _card()
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(14, 10, 14, 10)
        self.sum_sel = _label("Selected: 0 of 0", bold=True)
        self.sum_size = _label("Est. output: ~0.00 GB", color="#38bdf8")
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
                "  ⚠  All Editions  —  wimlib not installed, all editions will be kept"
            )
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            placeholder = WIMImageInfo(
                index=0, name="All Editions",
                description="Keep all (wimlib required to list individually)",
                size_bytes=info.install_image_size or info.total_iso_size,
            )
            item.setData(Qt.ItemDataRole.UserRole, placeholder)
            self.list.addItem(item)
        else:
            if self._notice:
                self._notice.setVisible(False)
            for img in info.wim_images:
                size_gb = img.size_bytes / (1024 ** 3)
                item = QListWidgetItem(
                    f"  [{img.index}]  {img.display_name}"
                    f"    ·    {size_gb:.2f} GB"
                )
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                item.setData(Qt.ItemDataRole.UserRole, img)
                self.list.addItem(item)

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
        nl.setContentsMargins(14, 10, 14, 10)
        ico = QLabel("⚠")
        ico.setStyleSheet("color:#f59e0b;font-size:18px;background:transparent;")
        lbl = QLabel(
            "<b style='color:#fde68a'>wimlib not installed.</b>"
            " <span style='color:#94a3b8'>Install wimlib to pick individual editions.</span>"
        )
        lbl.setWordWrap(True)
        self._install_btn = QPushButton("Install wimlib now")
        self._install_btn.setProperty("secondary", True)
        self._install_btn.setFixedHeight(34)
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
            self._install_btn.setText("Install wimlib now")
        if not ok:
            QMessageBox.warning(
                self, "Installation failed",
                "wimlib could not be installed automatically.\n\n"
                "Download wimlib-imagex.exe from:\n  https://wimlib.net/downloads/\n\n"
                "Then place it in:  winiso_toolkit/tools/wimlib-imagex.exe",
            )
            return
        info: ISOInfo | None = self.state.get("iso_info")
        if not info:
            return
        self._re = ISOAnalyzeWorker(info.path)
        self._re.finished_ok.connect(self._re_done)
        self._re.failed.connect(lambda e: QMessageBox.warning(self, "Re-analysis failed", e))
        self._re.start()

    def _wim_error(self, err: str) -> None:
        if self._install_btn:
            self._install_btn.setEnabled(True)
            self._install_btn.setText("Retry install")
        QMessageBox.critical(self, "Install error", err)

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
            f"<b>Selected:</b> {sel} of {n} edition{'s' if n != 1 else ''}"
        )
        self.sum_size.setText(
            f"Est. compressed output: <b style='color:#38bdf8'>~{est_gb:.2f} GB</b>"
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
        self.state["indices"] = indices  # index 0 = keep-all sentinel


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

        hdr = QLabel("Customization & Bypasses")
        hdr.setStyleSheet("color:#f1f5f9;font-size:22px;font-weight:700;")
        sub = _label("Select which tweaks to bake into the ISO.", muted=True)
        root.addWidget(hdr)
        root.addWidget(sub)
        root.addWidget(_sep())

        # Windows 11 bypasses
        bypass_box = QGroupBox("Windows 11 Hardware Bypasses")
        bb = QVBoxLayout(bypass_box)
        self.chk_tpm = QCheckBox(
            "Bypass TPM 2.0, SecureBoot, RAM & CPU checks  "
            "(adds autounattend.xml registry tweaks)"
        )
        self.chk_tpm.setChecked(True)
        self.chk_msa = QCheckBox(
            "Bypass mandatory Microsoft Account  "
            "(BypassNRO — forces local account setup)"
        )
        self.chk_msa.setChecked(True)
        self.chk_tel = QCheckBox("Disable telemetry & background data collection")
        self.chk_tel.setChecked(True)
        bb.addWidget(self.chk_tpm)
        bb.addWidget(self.chk_msa)
        bb.addWidget(self.chk_tel)
        root.addWidget(bypass_box)

        # User setup
        user_box = QGroupBox("User & System Identity")
        uf = QVBoxLayout(user_box)
        urow = QHBoxLayout()
        self.username = QLineEdit("User")
        self.compname = QLineEdit("WinISO-PC")
        urow.addWidget(QLabel("Username:"))
        urow.addWidget(self.username)
        urow.addSpacing(16)
        urow.addWidget(QLabel("Computer name:"))
        urow.addWidget(self.compname)
        uf.addLayout(urow)
        root.addWidget(user_box)

        # Driver injection
        drv_box = QGroupBox("Driver Slipstreaming (Optional)")
        dv = QVBoxLayout(drv_box)
        drow = QHBoxLayout()
        self.driver_edit = QLineEdit()
        self.driver_edit.setPlaceholderText(
            "Path to folder containing .inf driver packages…"
        )
        drv_btn = QPushButton("Browse…")
        drv_btn.setProperty("secondary", True)
        drv_btn.setFixedWidth(90)
        drv_btn.clicked.connect(self._browse_drivers)
        drow.addWidget(self.driver_edit, 1)
        drow.addWidget(drv_btn)
        dv.addLayout(drow)
        root.addWidget(drv_box)

        root.addStretch()

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

        hdr = QLabel("Compressing ISO")
        hdr.setStyleSheet("color:#f1f5f9;font-size:22px;font-weight:700;")
        root.addWidget(hdr)
        root.addWidget(_sep())

        # Progress card
        self.pcard = _card()
        pc = QVBoxLayout(self.pcard)
        pc.setSpacing(10)

        self.status_lbl = _label("Waiting to start…", muted=True)
        self.bar = QProgressBar()
        self.bar.setMinimumHeight(22)

        # Phase labels
        phases = QHBoxLayout()
        self._phase_labels: list[QLabel] = []
        for phase in ["Analyze", "Compress", "Extract ISO", "Inject", "Rebuild", "Done"]:
            pl = QLabel(phase)
            pl.setStyleSheet(
                "color:#334155; font-size:10px; font-weight:600;"
                "background:transparent;"
            )
            pl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            phases.addWidget(pl)
            self._phase_labels.append(pl)

        pc.addWidget(self.status_lbl)
        pc.addWidget(self.bar)
        pc.addLayout(phases)
        root.addWidget(self.pcard)

        # Stats row
        stats = _card()
        sl = QHBoxLayout(stats)
        sl.setContentsMargins(16, 10, 16, 10)
        self.stat_speed = self._stat(sl, "Speed", "—")
        self.stat_eta   = self._stat(sl, "ETA", "—")
        self.stat_in    = self._stat(sl, "Source Size", "—")
        self.stat_out   = self._stat(sl, "Output Size", "—")
        self.stat_ratio = self._stat(sl, "Compression Ratio", "—")
        root.addWidget(stats)
        root.addStretch()

    @staticmethod
    def _stat(layout: QHBoxLayout, key: str, val: str) -> QLabel:
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        c = QVBoxLayout(w)
        c.setSpacing(2)
        c.setContentsMargins(0, 0, 0, 0)
        c.addWidget(_label(key, muted=True, size=11))
        v = QLabel(val)
        v.setStyleSheet("color:#38bdf8;font-size:16px;font-weight:700;background:transparent;")
        c.addWidget(v)
        layout.addWidget(w)
        return v

    def _update_phase(self, pct: float) -> None:
        thresholds = [10, 55, 65, 72, 80, 100]
        for i, (lbl, thresh) in enumerate(zip(self._phase_labels, thresholds)):
            if pct >= thresh:
                lbl.setStyleSheet(
                    "color:#22c55e;font-size:10px;font-weight:700;background:transparent;"
                )
            elif pct >= (thresholds[i - 1] if i > 0 else 0):
                lbl.setStyleSheet(
                    "color:#38bdf8;font-size:10px;font-weight:700;background:transparent;"
                )
            else:
                lbl.setStyleSheet(
                    "color:#334155;font-size:10px;font-weight:600;background:transparent;"
                )

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

        hdr = QLabel("Select USB Drive")
        hdr.setStyleSheet("color:#f1f5f9;font-size:22px;font-weight:700;")
        sub = _label(
            "Choose the USB drive to burn. "
            "<b style='color:#f87171'>All data on it will be erased.</b>",
            muted=False,
        )
        sub.setWordWrap(True)
        root.addWidget(hdr)
        root.addWidget(sub)
        root.addWidget(_sep())

        # Toolbar
        tb = QHBoxLayout()
        refresh_btn = QPushButton("  Refresh USB List")
        refresh_btn.setProperty("secondary", True)
        refresh_btn.clicked.connect(self.refresh)
        health_btn = QPushButton("  Health & Speed Check")
        health_btn.setProperty("secondary", True)
        health_btn.clicked.connect(self._health_check)
        tb.addWidget(refresh_btn)
        tb.addWidget(health_btn)
        tb.addStretch()
        root.addLayout(tb)

        # USB combo
        self.combo = QComboBox()
        self.combo.setMinimumHeight(40)
        self.combo.currentIndexChanged.connect(self._validate)
        root.addWidget(self.combo)

        # Capacity indicator card
        self.cap_card = _card()
        cap_l = QHBoxLayout(self.cap_card)
        cap_l.setContentsMargins(14, 10, 14, 10)
        self.cap_icon = QLabel("⬤")
        self.cap_icon.setStyleSheet("color:#64748b;font-size:14px;background:transparent;")
        self.cap_lbl = _label("Select a USB drive to check capacity.", muted=True)
        self.cap_lbl.setWordWrap(True)
        cap_l.addWidget(self.cap_icon)
        cap_l.addSpacing(8)
        cap_l.addWidget(self.cap_lbl, 1)
        root.addWidget(self.cap_card)

        # Boot options
        opts_box = QGroupBox("Boot Mode & Partitioning")
        ob = QVBoxLayout(opts_box)
        self.boot_combo = QComboBox()
        self.boot_combo.addItems([
            "Both  (UEFI + Legacy MBR)",
            "UEFI only  (GPT / Modern PCs)",
            "Legacy only  (MBR / Older BIOS)",
        ])
        self.dual_chk = QCheckBox(
            "Use Dual-Partition layout  "
            "(FAT32 EFI Boot + NTFS Data — handles install.wim >4 GB)"
        )
        self.dual_chk.setToolTip(
            "Recommended for Windows 11 ISOs where install.wim exceeds 4 GB FAT32 limit."
        )
        ob.addWidget(QLabel("Boot mode:"))
        ob.addWidget(self.boot_combo)
        ob.addSpacing(6)
        ob.addWidget(self.dual_chk)
        root.addWidget(opts_box)
        root.addStretch()

    def refresh(self) -> None:
        self.combo.clear()
        devices = USBDetector().list_devices()
        self.state["usb_devices"] = devices
        if not devices:
            self.combo.addItem("No USB drives found — insert drive and click Refresh")
        for d in devices:
            self.combo.addItem(
                f"  {d.name}  ·  {d.size_gb:.1f} GB  ·  {d.filesystem or 'Unknown FS'}  [{d.path}]",
                d,
            )
        self._validate()
        _fade_in(self.combo)

    def _health_check(self) -> None:
        device: USBDevice | None = self.combo.currentData()
        if not device:
            QMessageBox.warning(self, "No USB", "Select a USB drive first.")
            return
        try:
            from winiso_toolkit.usb.health import USBHealthChecker
            rep = USBHealthChecker().run_quick_health_check(Path(device.path))
            icon = "✔" if rep.capacity_verified else "✖"
            QMessageBox.information(
                self, "USB Health Report",
                f"Drive:   {device.name}  [{device.path}]\n"
                f"Speed:   {rep.write_speed_mbps:.1f} MB/s\n"
                f"Capacity verified:  {icon}\n\n"
                f"Status:  {rep.status_message}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Health Check Error", str(exc))

    def _validate(self) -> None:
        device: USBDevice | None = self.combo.currentData()
        output: Path | None = self.state.get("output_iso")
        if not device or not output or not output.exists():
            self.cap_icon.setStyleSheet("color:#64748b;font-size:14px;background:transparent;")
            self.cap_lbl.setText("Select a USB drive to check capacity.")
            self.next_enabled.emit(False)
            return
        ok, msg = USBCreator().validate_capacity(device.size_bytes, output.stat().st_size)
        if ok:
            self.cap_icon.setStyleSheet("color:#4ade80;font-size:14px;background:transparent;")
            self.cap_lbl.setText(
                f"<span style='color:#4ade80'>✔  Sufficient capacity</span>"
                f"  —  {device.size_gb:.1f} GB drive ≥ {output.stat().st_size/(1024**3):.1f} GB required"
            )
            self.state["usb_device"] = device
            self.next_enabled.emit(True)
        else:
            self.cap_icon.setStyleSheet("color:#f87171;font-size:14px;background:transparent;")
            self.cap_lbl.setText(f"<span style='color:#f87171'>✖  {msg}</span>")
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

        hdr = QLabel("Confirm & Start Burn")
        hdr.setStyleSheet("color:#f1f5f9;font-size:22px;font-weight:700;")
        root.addWidget(hdr)
        root.addWidget(_sep())

        # Summary card
        self.summary_card = _card()
        sc = QVBoxLayout(self.summary_card)
        sc.setSpacing(8)
        self.sum_lbl = QLabel("")
        self.sum_lbl.setWordWrap(True)
        self.sum_lbl.setStyleSheet("color:#e2e8f0;font-size:13px;line-height:1.6;")
        sc.addWidget(self.sum_lbl)
        root.addWidget(self.summary_card)

        # Warning
        warn = _card()
        wl = QHBoxLayout(warn)
        wl.setContentsMargins(14, 12, 14, 12)
        warn_ico = QLabel("⚠️")
        warn_ico.setStyleSheet("font-size:22px;background:transparent;")
        warn_txt = QLabel(
            "<b style='color:#fde68a'>WARNING:</b>"
            " <span style='color:#fca5a5'>ALL DATA on the target USB drive"
            " will be permanently erased. This cannot be undone.</span>"
        )
        warn_txt.setWordWrap(True)
        wl.addWidget(warn_ico)
        wl.addWidget(warn_txt, 1)
        root.addWidget(warn)

        # Confirm checkbox
        self.confirm_chk = QCheckBox(
            "I understand — erase the USB drive and create a bootable Windows installer"
        )
        self.confirm_chk.setStyleSheet(
            "font-size:13px; font-weight:600; color:#f1f5f9;"
        )
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

        edition_str = "All (keep-all mode)" if indices == [0] else str(indices)

        iso_size = (
            f"{iso.stat().st_size / (1024**3):.2f} GB" if iso and iso.exists() else "?"
        )

        self.sum_lbl.setText(
            f"<table style='border-spacing:0 6px;'>"
            f"<tr><td style='color:#64748b;width:160px'>Output ISO</td>"
            f"<td style='color:#38bdf8'>{iso}</td></tr>"
            f"<tr><td style='color:#64748b'>ISO Size</td>"
            f"<td style='color:#e2e8f0'>{iso_size}</td></tr>"
            f"<tr><td style='color:#64748b'>Editions kept</td>"
            f"<td style='color:#e2e8f0'>{edition_str}</td></tr>"
            f"<tr><td style='color:#64748b'>USB Target</td>"
            f"<td style='color:#f87171'><b>{usb.path if usb else '—'}</b>"
            f" ({usb.name if usb else ''})</td></tr>"
            f"<tr><td style='color:#64748b'>Boot Mode</td>"
            f"<td style='color:#e2e8f0'>{boot.value}</td></tr>"
            f"<tr><td style='color:#64748b'>Partitioning</td>"
            f"<td style='color:#e2e8f0'>"
            f"{'Dual-Partition (FAT32+NTFS)' if dual else 'Single-Partition'}"
            f"</td></tr>"
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

        hdr = QLabel("Creating Bootable USB…")
        hdr.setStyleSheet("color:#f1f5f9;font-size:22px;font-weight:700;")
        root.addWidget(hdr)
        root.addWidget(_sep())

        pcard = _card()
        pc = QVBoxLayout(pcard)
        pc.setSpacing(10)
        self.status_lbl = _label("Preparing…", muted=True)
        self.bar = QProgressBar()
        self.bar.setMinimumHeight(22)
        pc.addWidget(self.status_lbl)
        pc.addWidget(self.bar)
        root.addWidget(pcard)

        stats = _card()
        sl = QHBoxLayout(stats)
        sl.setContentsMargins(16, 10, 16, 10)
        self.stat_speed = self._stat(sl, "Write Speed", "—")
        self.stat_eta   = self._stat(sl, "ETA", "—")
        self.stat_done  = self._stat(sl, "Written", "—")
        root.addWidget(stats)
        root.addStretch()

    @staticmethod
    def _stat(layout: QHBoxLayout, key: str, val: str) -> QLabel:
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        c = QVBoxLayout(w)
        c.setSpacing(2)
        c.setContentsMargins(0, 0, 0, 0)
        c.addWidget(_label(key, muted=True, size=11))
        v = QLabel(val)
        v.setStyleSheet("color:#38bdf8;font-size:16px;font-weight:700;background:transparent;")
        c.addWidget(v)
        layout.addWidget(w)
        return v

    def start(self) -> None:
        iso: Path | None = self.state.get("output_iso")
        usb: USBDevice | None = self.state.get("usb_device")
        if not iso or not usb:
            QMessageBox.critical(self, "Missing Data", "ISO or USB device not configured.")
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
            # Extract MB/s from message if present
            import re
            m = re.search(r"([\d.]+)\s*MB/s", msg)
            if m:
                self.stat_speed.setText(f"{m.group(1)} MB/s")
            written_bytes = (pct / 100) * (self.state.get("output_iso").stat().st_size
                                           if self.state.get("output_iso") else 0)
            self.stat_done.setText(_fmt_gb(int(written_bytes)))


# ─────────────────────────────────────────────────────────────
# STEP 8 — DONE
# ─────────────────────────────────────────────────────────────

class StepResult(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state

        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(0, 0, 0, 0)

        # Success header
        hdr = QLabel("✔  Bootable USB Created")
        hdr.setStyleSheet(
            "color:#4ade80;font-size:24px;font-weight:700;letter-spacing:-0.5px;"
        )
        root.addWidget(hdr)
        root.addWidget(_sep())

        # Result card
        self.result_card = _card()
        rl = QVBoxLayout(self.result_card)
        rl.setSpacing(10)
        self.result_lbl = QLabel()
        self.result_lbl.setWordWrap(True)
        self.result_lbl.setStyleSheet("color:#e2e8f0;font-size:13px;line-height:1.6;")
        rl.addWidget(self.result_lbl)
        root.addWidget(self.result_card)

        # Verification checklist
        chk_card = _card()
        cl = QVBoxLayout(chk_card)
        cl.setSpacing(8)
        cl.addWidget(_label("Verification Checklist", bold=True, color="#38bdf8"))
        cl.addWidget(_sep())
        for item in [
            ("El Torito boot record", True),
            ("BCD boot configuration", True),
            ("Post-write file checksums", True),
            ("EFI/UEFI boot files", True),
        ]:
            row = QHBoxLayout()
            icon = QLabel("✔" if item[1] else "✖")
            icon.setStyleSheet(
                f"color:{'#4ade80' if item[1] else '#f87171'};"
                "font-size:14px;font-weight:700;background:transparent;"
            )
            icon.setFixedWidth(24)
            row.addWidget(icon)
            row.addWidget(_label(item[0]))
            row.addStretch()
            row.addWidget(_label("VERIFIED" if item[1] else "FAILED",
                                 color="#4ade80" if item[1] else "#f87171",
                                 bold=True, size=11))
            cl.addLayout(row)
        root.addWidget(chk_card)

        # Action buttons
        act = QHBoxLayout()
        vm_btn = QPushButton("  Test in QEMU VM")
        vm_btn.setProperty("secondary", True)
        vm_btn.clicked.connect(self._test_vm)
        eject_btn = QPushButton("  Safely Eject USB")
        eject_btn.setProperty("secondary", True)
        eject_btn.clicked.connect(self._eject)
        act.addWidget(vm_btn)
        act.addWidget(eject_btn)
        act.addStretch()
        root.addLayout(act)
        root.addStretch()

    def refresh(self) -> None:
        usb: USBDevice | None = self.state.get("usb_device")
        iso: Path | None = self.state.get("output_iso")
        iso_size = (
            f"{iso.stat().st_size / (1024**3):.2f} GB" if iso and iso.exists() else "—"
        )
        self.result_lbl.setText(
            f"<table style='border-spacing:0 6px;'>"
            f"<tr><td style='color:#64748b;width:140px'>USB Drive</td>"
            f"<td><b style='color:#4ade80'>{usb.path if usb else '—'}</b>"
            f"  ({usb.name if usb else ''})</td></tr>"
            f"<tr><td style='color:#64748b'>Output ISO</td>"
            f"<td style='color:#38bdf8'>{iso}</td></tr>"
            f"<tr><td style='color:#64748b'>Output Size</td>"
            f"<td style='color:#e2e8f0'>{iso_size}</td></tr>"
            f"</table>"
        )
        _fade_in(self.result_card)

    def _test_vm(self) -> None:
        iso: Path | None = self.state.get("output_iso")
        if not iso or not iso.exists():
            QMessageBox.warning(self, "No ISO", "Output ISO not found.")
            return
        from winiso_toolkit.utils.vm import QEMUTester
        tester = QEMUTester()
        if not tester.is_qemu_available():
            QMessageBox.information(
                self, "QEMU Not Found",
                "QEMU is not installed.\n\n"
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
            QMessageBox.warning(self, "No USB", "No target USB drive on record.")
            return
        from winiso_toolkit.usb.ejector import USBEjector
        ok, msg = USBEjector().safe_eject(usb.path)
        if ok:
            QMessageBox.information(self, "Safe to Remove", msg)
        else:
            QMessageBox.warning(self, "Eject Warning", msg)


# ─────────────────────────────────────────────────────────────
# MAIN WINDOW
# ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WinISO Toolkit Supercharged")
        self.setMinimumSize(880, 660)
        self.resize(960, 720)
        self.state: dict = {}

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Step bar ──────────────────────────────────────────
        self.step_bar = StepIndicatorWidget()
        root.addWidget(self.step_bar)

        # ── Wizard area ───────────────────────────────────────
        wiz = QWidget()
        wiz_l = QVBoxLayout(wiz)
        wiz_l.setContentsMargins(24, 18, 24, 14)
        wiz_l.setSpacing(12)

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
            self.stack.addWidget(w)

        wiz_l.addWidget(self.stack, 1)

        # Navigation bar
        nav = QHBoxLayout()
        self.back_btn = QPushButton("  ← Back")
        self.back_btn.setProperty("secondary", True)
        self.back_btn.setFixedWidth(110)
        self.back_btn.setMinimumHeight(40)
        self.next_btn = QPushButton("Next  →")
        self.next_btn.setFixedWidth(130)
        self.next_btn.setMinimumHeight(40)
        self.back_btn.clicked.connect(self.go_back)
        self.next_btn.clicked.connect(self.go_next)
        nav.addWidget(self.back_btn)
        nav.addStretch()
        nav.addWidget(self.next_btn)
        wiz_l.addLayout(nav)

        root.addWidget(wiz, 1)

        # ── Live console ──────────────────────────────────────
        console_box = QGroupBox("  Live Process Output Console")
        console_box.setObjectName("console_group")
        cl = QVBoxLayout(console_box)
        cl.setContentsMargins(10, 6, 10, 8)
        cl.setSpacing(4)

        ctb = QHBoxLayout()
        self.console_toggle = QPushButton("Hide ▼")
        self.console_toggle.setProperty("secondary", True)
        self.console_toggle.setFixedWidth(80)
        self.console_toggle.setFixedHeight(26)
        self.console_toggle.clicked.connect(self._toggle_console)
        clear_btn = QPushButton("Clear")
        clear_btn.setProperty("secondary", True)
        clear_btn.setFixedWidth(60)
        clear_btn.setFixedHeight(26)
        clear_btn.clicked.connect(lambda: self.console.clear())
        ctb.addStretch()
        ctb.addWidget(self.console_toggle)
        ctb.addWidget(clear_btn)
        cl.addLayout(ctb)

        self.console = QTextEdit()
        self.console.setObjectName("live_log_console")
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(140)
        self.console.setMinimumHeight(140)
        cl.addWidget(self.console)

        console_wrap = QWidget()
        cw_l = QVBoxLayout(console_wrap)
        cw_l.setContentsMargins(16, 0, 16, 12)
        cw_l.addWidget(console_box)
        root.addWidget(console_wrap)

        # ── Logging bridge ────────────────────────────────────
        self.log_handler = QObjectLogHandler()
        self.log_handler.new_log.connect(self.console.append)
        logging.getLogger("winiso_toolkit").addHandler(self.log_handler)

        # ── Signal wiring ─────────────────────────────────────
        self.step_iso.next_enabled.connect(self._set_next)
        self.step_editions.next_enabled.connect(self._set_next)
        self.step_usb.next_enabled.connect(self._set_next)
        self.step_confirm.next_enabled.connect(self._set_next)

        self._step = 0
        self._update_nav()

    # ── Navigation ────────────────────────────────────────────

    def log_message(self, msg: str) -> None:
        logging.getLogger("winiso_toolkit").info(msg)

    def _toggle_console(self) -> None:
        visible = self.console.isVisible()
        self.console.setVisible(not visible)
        self.console_toggle.setText("Show ▲" if visible else "Hide ▼")

    def _set_next(self, enabled: bool) -> None:
        if self._step not in (3, 6, 7):
            self.next_btn.setEnabled(enabled)

    def _update_nav(self) -> None:
        self.step_bar.set_step(self._step)
        auto = self._step in (3, 6, 7)
        self.back_btn.setEnabled(self._step > 0 and not auto)
        self.next_btn.setEnabled(not auto)
        self.next_btn.setText("Finish  ✓" if self._step == 7 else "Next  →")

    def set_back_enabled(self, v: bool) -> None:
        self.back_btn.setEnabled(v)

    def go_back(self) -> None:
        if self._step > 0:
            self._step -= 1
            self.stack.setCurrentIndex(self._step)
            self._update_nav()

    def advance(self) -> None:
        """Called by background workers when an async step completes."""
        self._step += 1
        self.stack.setCurrentIndex(self._step)
        self._update_nav()
        self._on_step_entered()

    def go_next(self) -> None:
        if self._step == 1:
            self.step_editions.save_selection()
            if not self.state.get("indices"):
                QMessageBox.warning(self, "No editions", "Select at least one edition.")
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


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

def run_gui() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("WinISO Toolkit")
    app.setApplicationVersion("1.0.0")
    from winiso_toolkit.gui.theme import DARK_THEME_QSS
    app.setStyleSheet(DARK_THEME_QSS)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run_gui())
