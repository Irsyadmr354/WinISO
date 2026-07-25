"""Step-by-step wizard GUI for WinISO Toolkit."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
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
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from winiso_toolkit.deps.installer import DependencyInstaller
from winiso_toolkit.iso.analyzer import ISOAnalyzer, ISOInfo, WIMImageInfo
from winiso_toolkit.pipeline import WinISOPipeline
from winiso_toolkit.usb.creator import BootMode, USBCreator
from winiso_toolkit.usb.detector import USBDevice, USBDetector


class WorkerThread(QThread):
    progress = pyqtSignal(float, str)
    finished_ok = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = self._fn(
                *self._args,
                progress=lambda p, m: self.progress.emit(p, m),
                **self._kwargs,
            )
            self.finished_ok.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class StepIsoSelect(QWidget):
    next_enabled = pyqtSignal(bool)

    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<h2>Step 1: Select Windows ISO</h2>"))
        layout.addWidget(QLabel("Choose a Windows installer ISO file."))

        row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Path to .iso file…")
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        row.addWidget(self.path_edit)
        row.addWidget(browse)
        layout.addLayout(row)

        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        layout.addStretch()

        self.path_edit.textChanged.connect(self._on_path_changed)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select ISO", "", "ISO Files (*.iso)")
        if path:
            self.path_edit.setText(path)

    def _on_path_changed(self) -> None:
        path = Path(self.path_edit.text().strip())
        if not path.is_file():
            self.info_label.setText("")
            self.next_enabled.emit(False)
            return
        try:
            deps = DependencyInstaller()
            info = ISOAnalyzer(deps).analyze(path)
            self.state["iso_path"] = path
            self.state["iso_info"] = info
            est = info.estimated_compressed_size / (1024**3)
            self.info_label.setText(
                f"<b>{info.volume_label}</b><br>"
                f"Windows installer: {'Yes' if info.is_windows_installer else 'No'}<br>"
                f"Install image: {info.install_image_size / (1024**3):.2f} GB<br>"
                f"Estimated compressed: ~{est:.2f} GB"
            )
            self.next_enabled.emit(info.is_windows_installer)
        except Exception as exc:
            self.info_label.setText(f"<span style='color:red'>{exc}</span>")
            self.next_enabled.emit(False)


class StepEditionSelect(QWidget):
    next_enabled = pyqtSignal(bool)

    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Step 2: Select Editions to Keep</h2>"))
        layout.addWidget(QLabel("Uncheck editions you want to remove to save space."))

        self.list = QListWidget()
        layout.addWidget(self.list)
        layout.addStretch()

    def refresh(self) -> None:
        self.list.clear()
        info: ISOInfo = self.state.get("iso_info")
        if not info:
            self.next_enabled.emit(False)
            return
        for img in info.wim_images:
            item = QListWidgetItem(
                f"[{img.index}] {img.display_name} ({img.size_bytes / (1024**3):.2f} GB)"
            )
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, img.index)
            self.list.addItem(item)
        self.next_enabled.emit(True)

    def save_selection(self) -> None:
        indices = []
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                indices.append(item.data(Qt.ItemDataRole.UserRole))
        self.state["indices"] = indices


class StepCustomization(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<h2>Windows Customization & Bypasses</h2>"))

        bypasses_box = QGroupBox("Windows 11 Bypasses")
        box_layout = QVBoxLayout(bypasses_box)
        self.tpm_check = QCheckBox("Bypass TPM 2.0, SecureBoot, RAM, and CPU checks")
        self.tpm_check.setChecked(True)
        self.msa_check = QCheckBox("Bypass mandatory Microsoft Account requirement (BypassNRO)")
        self.msa_check.setChecked(True)
        self.telemetry_check = QCheckBox("Disable Windows Telemetry & Data Collection")
        self.telemetry_check.setChecked(True)

        box_layout.addWidget(self.tpm_check)
        box_layout.addWidget(self.msa_check)
        box_layout.addWidget(self.telemetry_check)
        layout.addWidget(bypasses_box)

        user_box = QGroupBox("User & System Setup")
        user_form = QFormLayout(user_box)
        self.username_edit = QLineEdit("User")
        self.computer_edit = QLineEdit("WinISO-PC")
        user_form.addRow("Local Username:", self.username_edit)
        user_form.addRow("Computer Name:", self.computer_edit)
        layout.addWidget(user_box)

        row = QHBoxLayout()
        self.driver_edit = QLineEdit()
        self.driver_edit.setPlaceholderText("Optional path to custom driver folder (.inf)…")
        browse_driver = QPushButton("Browse Drivers…")
        browse_driver.clicked.connect(self._browse_drivers)
        row.addWidget(self.driver_edit)
        row.addWidget(browse_driver)
        layout.addLayout(row)

        self.verify_btn = QPushButton("Verify Source ISO SHA-256 Checksum")
        self.verify_btn.clicked.connect(self._verify_sha256)
        layout.addWidget(self.verify_btn)
        layout.addStretch()

    def _browse_drivers(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Driver Folder")
        if folder:
            self.driver_edit.setText(folder)

    def _verify_sha256(self) -> None:
        iso_path = self.state.get("iso_path")
        if not iso_path:
            QMessageBox.warning(self, "No ISO", "Select an ISO file first.")
            return
        from winiso_toolkit.iso.verifier import ISOVerifier
        verifier = ISOVerifier()
        res = verifier.verify_iso(iso_path)
        QMessageBox.information(
            self,
            "SHA-256 Checksum Result",
            f"Calculated Hash:\n{res.calculated_hash}\n\nMatch Status: {res.official_name}",
        )

    def save_settings(self) -> None:
        from winiso_toolkit.iso.unattended import BypassOptions
        self.state["bypass_options"] = BypassOptions(
            bypass_tpm=self.tpm_check.isChecked(),
            bypass_secure_boot=self.tpm_check.isChecked(),
            bypass_ram=self.tpm_check.isChecked(),
            bypass_cpu=self.tpm_check.isChecked(),
            bypass_msa=self.msa_check.isChecked(),
            disable_telemetry=self.telemetry_check.isChecked(),
            username=self.username_edit.text().strip() or "User",
            computer_name=self.computer_edit.text().strip() or "WinISO-PC",
        )
        drv = self.driver_edit.text().strip()
        self.state["driver_dir"] = Path(drv) if drv else None


class StepCompress(QWidget):
    def __init__(self, state: dict, parent_window: "MainWindow") -> None:
        super().__init__()
        self.state = state
        self.parent_window = parent_window
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Step 3: Compress ISO</h2>"))
        self.status = QLabel("Ready to compress.")
        self.bar = QProgressBar()
        layout.addWidget(self.status)
        layout.addWidget(self.bar)
        layout.addStretch()

    def start(self) -> None:
        iso_path: Path = self.state["iso_path"]
        indices: list[int] = self.state.get("indices", [1])
        output = iso_path.with_name(f"{iso_path.stem}_compressed.iso")
        self.state["output_iso"] = output

        pipeline = WinISOPipeline()
        self.worker = WorkerThread(pipeline.compress_iso, iso_path, output, indices)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_ok.connect(self._on_done)
        self.worker.failed.connect(self._on_fail)
        self.worker.start()

    def _on_progress(self, pct: float, msg: str) -> None:
        self.bar.setValue(int(pct))
        self.status.setText(msg)

    def _on_done(self, result) -> None:
        self.state["output_iso"] = Path(result)
        self.parent_window.advance()

    def _on_fail(self, msg: str) -> None:
        QMessageBox.critical(self, "Compression Failed", msg)
        self.parent_window.set_back_enabled(True)
        self.parent_window.next_btn.setEnabled(True)


class StepUsbSelect(QWidget):
    next_enabled = pyqtSignal(bool)

    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Step 4: Select USB Drive</h2>"))

        refresh_btn = QPushButton("Refresh USB list")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)

        self.combo = QComboBox()
        layout.addWidget(self.combo)

        self.capacity_label = QLabel("")
        self.capacity_label.setWordWrap(True)
        layout.addWidget(self.capacity_label)

        boot_box = QGroupBox("Boot mode")
        boot_layout = QVBoxLayout(boot_box)
        self.boot_combo = QComboBox()
        self.boot_combo.addItems(["Both (UEFI + Legacy)", "UEFI only", "Legacy (MBR) only"])
        boot_layout.addWidget(self.boot_combo)
        layout.addWidget(boot_box)
        layout.addStretch()

        self.combo.currentIndexChanged.connect(self._validate)

    def refresh(self) -> None:
        self.combo.clear()
        devices = USBDetector().list_devices()
        self.state["usb_devices"] = devices
        for d in devices:
            self.combo.addItem(f"{d.name} — {d.size_gb:.1f} GB ({d.path})", d)
        self._validate()

    def _validate(self) -> None:
        device: USBDevice | None = self.combo.currentData()
        output: Path | None = self.state.get("output_iso")
        if not device or not output or not output.exists():
            self.capacity_label.setText("")
            self.next_enabled.emit(False)
            return

        creator = USBCreator()
        ok, msg = creator.validate_capacity(device.size_bytes, output.stat().st_size)
        if ok:
            self.capacity_label.setText(
                f"<span style='color:green'>USB capacity sufficient "
                f"({device.size_gb:.1f} GB ≥ {output.stat().st_size / (1024**3):.1f} GB required)</span>"
            )
            self.state["usb_device"] = device
            self.next_enabled.emit(True)
        else:
            self.capacity_label.setText(f"<span style='color:red'>{msg}</span>")
            self.next_enabled.emit(False)

    def save_selection(self) -> None:
        modes = [BootMode.BOTH, BootMode.UEFI, BootMode.LEGACY]
        self.state["boot_mode"] = modes[self.boot_combo.currentIndex()]


class StepConfirm(QWidget):
    next_enabled = pyqtSignal(bool)

    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Step 5: Confirm</h2>"))
        self.summary = QLabel("")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        layout.addWidget(QLabel("<b style='color:red'>ALL DATA ON THE USB WILL BE ERASED.</b>"))
        self.confirm_check = QCheckBox('I understand and want to proceed')
        self.confirm_check.stateChanged.connect(
            lambda: self.next_enabled.emit(self.confirm_check.isChecked())
        )
        layout.addWidget(self.confirm_check)
        layout.addStretch()

    def refresh(self) -> None:
        iso = self.state.get("output_iso")
        usb: USBDevice = self.state.get("usb_device")
        indices = self.state.get("indices", [])
        self.summary.setText(
            f"<b>Output ISO:</b> {iso}<br>"
            f"<b>Editions kept:</b> {indices}<br>"
            f"<b>USB target:</b> {usb.path if usb else '—'} ({usb.name if usb else ''})<br>"
            f"<b>Boot mode:</b> {self.state.get('boot_mode', BootMode.BOTH).value}"
        )
        self.confirm_check.setChecked(False)
        self.next_enabled.emit(False)


class StepBurn(QWidget):
    def __init__(self, state: dict, parent_window: "MainWindow") -> None:
        super().__init__()
        self.state = state
        self.parent_window = parent_window
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Step 6: Creating Bootable USB</h2>"))
        self.status = QLabel("")
        self.bar = QProgressBar()
        layout.addWidget(self.status)
        layout.addWidget(self.bar)
        layout.addStretch()

    def start(self) -> None:
        iso: Path = self.state["output_iso"]
        usb: USBDevice = self.state["usb_device"]
        mode: BootMode = self.state.get("boot_mode", BootMode.BOTH)
        creator = USBCreator()
        self.worker = WorkerThread(
            creator.create,
            iso,
            usb.path,
            boot_mode=mode,
            bypass_options=self.state.get("bypass_options"),
            driver_dir=self.state.get("driver_dir"),
            verify=True,
        )
        self.worker.progress.connect(lambda p, m: (self.bar.setValue(int(p)), self.status.setText(m)))
        self.worker.finished_ok.connect(lambda _: self.parent_window.advance())
        self.worker.failed.connect(lambda msg: QMessageBox.critical(self, "USB Creation Failed", msg))
        self.worker.start()


class StepResult(QWidget):
    def __init__(self, state: dict) -> None:
        super().__init__()
        self.state = state
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Step 7: Complete</h2>"))
        self.result = QLabel("")
        self.result.setWordWrap(True)
        layout.addWidget(self.result)

        btn_layout = QHBoxLayout()
        self.vm_btn = QPushButton("Test ISO in QEMU VM Sandbox")
        self.vm_btn.clicked.connect(self._test_vm)
        self.eject_btn = QPushButton("Safely Eject USB Drive")
        self.eject_btn.clicked.connect(self._safe_eject)

        btn_layout.addWidget(self.vm_btn)
        btn_layout.addWidget(self.eject_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()

    def refresh(self) -> None:
        usb = self.state.get('usb_device')
        usb_info = f"{usb.path}" if usb else "N/A"
        self.result.setText(
            "<span style='color:#38bdf8;font-size:14pt'>Success!</span><br><br>"
            f"Bootable USB created on <b>{usb_info}</b>.<br>"
            f"Output ISO saved at <b>{self.state.get('output_iso')}</b>.<br>"
            "Critical files were checksum-verified after writing."
        )

    def _safe_eject(self) -> None:
        usb = self.state.get("usb_device")
        if not usb:
            QMessageBox.warning(self, "No USB", "No target USB drive found.")
            return
        from winiso_toolkit.usb.ejector import USBEjector
        ejector = USBEjector()
        ok, msg = ejector.safe_eject(usb.path)
        if ok:
            QMessageBox.information(self, "Safe to Remove", msg)
        else:
            QMessageBox.warning(self, "Eject Warning", msg)

    def _test_vm(self) -> None:
        output_iso = self.state.get("output_iso")
        if not output_iso or not Path(output_iso).exists():
            QMessageBox.warning(self, "No ISO", "Output ISO file not found.")
            return
        from winiso_toolkit.utils.vm import QEMUTester
        tester = QEMUTester()
        if not tester.is_qemu_available():
            QMessageBox.information(
                self,
                "QEMU Not Found",
                "QEMU is not installed on your system. Install qemu-system-x86_64 to test ISOs in a virtual machine.",
            )
            return
        try:
            tester.launch_test_vm(output_iso)
            QMessageBox.information(self, "VM Started", "QEMU Virtual Machine launched!")
        except Exception as exc:
            QMessageBox.critical(self, "VM Error", str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WinISO Toolkit Supercharged")
        self.resize(680, 520)
        self.state: dict = {}

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        self.stack = QStackedWidget()
        self.step_iso = StepIsoSelect(self.state)
        self.step_editions = StepEditionSelect(self.state)
        self.step_compress = StepCompress(self.state, self)
        self.step_usb = StepUsbSelect(self.state)
        self.step_confirm = StepConfirm(self.state)
        self.step_burn = StepBurn(self.state, self)
        self.step_result = StepResult(self.state)

        for w in (
            self.step_iso,
            self.step_editions,
            self.step_compress,
            self.step_usb,
            self.step_confirm,
            self.step_burn,
            self.step_result,
        ):
            self.stack.addWidget(w)

        root.addWidget(self.stack)

        nav = QHBoxLayout()
        self.back_btn = QPushButton("Back")
        self.next_btn = QPushButton("Next")
        self.back_btn.clicked.connect(self.go_back)
        self.next_btn.clicked.connect(self.go_next)
        nav.addWidget(self.back_btn)
        nav.addStretch()
        nav.addWidget(self.next_btn)
        root.addLayout(nav)

        self.step_iso.next_enabled.connect(self._set_next)
        self.step_editions.next_enabled.connect(self._set_next)
        self.step_usb.next_enabled.connect(self._set_next)
        self.step_confirm.next_enabled.connect(self._set_next)

        self._step = 0
        self._update_nav()

    def _set_next(self, enabled: bool) -> None:
        if self._step in (0, 1, 3, 4):
            self.next_btn.setEnabled(enabled)

    def _update_nav(self) -> None:
        self.back_btn.setEnabled(self._step > 0 and self._step not in (2, 5, 6))
        self.next_btn.setEnabled(self._step not in (2, 5, 6))
        self.next_btn.setText("Finish" if self._step == 6 else "Next")

    def set_back_enabled(self, enabled: bool) -> None:
        self.back_btn.setEnabled(enabled)

    def go_back(self) -> None:
        if self._step > 0:
            self._step -= 1
            self.stack.setCurrentIndex(self._step)
            self._update_nav()

    def advance(self) -> None:
        self._step += 1
        self.stack.setCurrentIndex(self._step)
        self._update_nav()
        if self._step == 2:
            self.step_compress.start()
        elif self._step == 5:
            self.step_burn.start()
        elif self._step == 6:
            self.step_result.refresh()

    def go_next(self) -> None:
        if self._step == 1:
            self.step_editions.save_selection()
            if not self.state.get("indices"):
                QMessageBox.warning(self, "No editions", "Select at least one edition.")
                return
        elif self._step == 3:
            self.step_usb.save_selection()
        elif self._step == 4:
            pass
        elif self._step == 6:
            self.close()
            return

        self._step += 1
        self.stack.setCurrentIndex(self._step)
        self._update_nav()

        if self._step == 1:
            self.step_editions.refresh()
        elif self._step == 2:
            self.step_compress.start()
        elif self._step == 3:
            self.step_usb.refresh()
        elif self._step == 4:
            self.step_confirm.refresh()
        elif self._step == 5:
            self.step_burn.start()
        elif self._step == 6:
            self.step_result.refresh()


def run_gui() -> int:
    app = QApplication(sys.argv)
    from winiso_toolkit.gui.theme import DARK_THEME_QSS
    app.setStyleSheet(DARK_THEME_QSS)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run_gui())
