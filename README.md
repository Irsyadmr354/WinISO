# WinISO Toolkit Supercharged Beast-Mode 🚀

Cross-platform **Windows ISO Compressor, Debloater, Customizer & Auto-Bootable USB Creator** for Linux and Windows.

---

## 🔥 Beast-Mode Features

- **🔓 Windows 11 Hardware & MSA Bypass** — Automatically generates `autounattend.xml` to bypass TPM 2.0, Secure Boot, RAM, CPU, and mandatory Microsoft Account requirement (`BypassNRO`).
- **🗑️ WIM Debloater & Bloatware Stripper** — Removes OneDrive, Xbox bloatware, Cortana, News, Weather, and disables telemetry (`--debloat`).
- **⚡ Cumulative Windows Update Slipstreamer** — Pre-installs `.msu` and `.cab` Windows update packages directly into `install.wim` offline (`--slipstream-updates`).
- **🚀 Windows To Go (WTG) Live USB Deployer** — Deploys live portable Windows OS directly onto USB drives so you can boot full Windows on any PC (`--wtg`).
- **🌐 In-App Official MS ISO Downloader** — Direct CDN resolver and downloader for official Windows 11 & Windows 10 ISOs (`--download-iso win11`).
- **🧰 WinPE Live Rescue Suite Builder** — Injects 7-Zip, DiskGenius, HWMonitor, and password recovery tools into boot media (`--build-pe-rescue`).
- **💾 Dual-Partition UEFI Engine** — Creates FAT32 ESP Boot + NTFS Data dual-partition scheme so strict UEFI motherboards can boot >4GB `install.wim` files natively without splitting!
- **🔌 Driver Slipstreaming** — Pre-injects storage (NVMe/RAID) and network (Wi-Fi/LAN) `.inf` driver packages into Windows Setup media.
- **🧪 1-Click QEMU VM Boot Tester** — Boot test built ISOs in a lightweight QEMU virtual machine sandbox before burning to physical USB drives (`--test-vm`).
- **🩺 USB Health & Speed Diagnostic Engine** — Measures write speed in MB/s with ETA estimation and detects fake capacity flash drives (`--health-check`).
- **🎨 Glassmorphism PyQt6 Dark Theme** — Sleek dark theme with live MB/s, ETA progress bar, and VM sandbox launcher.
- **📦 Standalone PyInstaller Packaging** — Build a portable `WinISO-Toolkit.exe` binary with 1-click script (`python build.py`).
- **🧪 100% Passing Unit Test Suite** — 11 automated unit tests (`python run_tests.py`).

---

## 📦 Requirements

- Python 3.11+
- External tools (auto-installable on Linux via `--install-deps`):
  - **wimlib** — WIM/ESD LZMS compression & metadata
  - **xorriso** (Linux) or **oscdimg** (Windows ADK) — Bootable ISO rebuilding
  - **parted**, **ntfs-3g**, **dosfstools** — USB partitioning & formatting

---

## 📥 Installation

```bash
pip install -e .
# or
pip install -r requirements.txt
```

---

## 🚀 Usage Guide

### 🎨 Graphical Wizard (PyQt6 Dark Theme)

```bash
winiso-toolkit --gui
```

### 🔓 Debloat & Bypass Windows 11 Requirements (TPM 2.0, RAM, MSA)

```bash
winiso-toolkit --iso win11.iso --bypass-tpm --bypass-msa --debloat --output win11_clean.iso
```

### ⚡ Slipstream Windows Updates & Drivers into ISO

```bash
winiso-toolkit --iso win11.iso --slipstream-updates ./my_updates --inject-drivers ./my_drivers
```

### 🚀 Deploy Live Windows To Go (WTG) Portable USB

```bash
winiso-toolkit --iso win11.iso --target /dev/sdb --wtg --confirm
```

### 🌐 Download Official Microsoft Windows 11 ISO

```bash
winiso-toolkit --download-iso win11
```

### 🧪 Test Built ISO in QEMU VM Sandbox

```bash
winiso-toolkit --iso win11_compressed.iso --test-vm
```

### 🩺 USB Diagnostic & Write Speed Test

```bash
winiso-toolkit --target /dev/sdb --health-check
```

---

## 🧪 Running Unit Tests

```bash
python run_tests.py
```

---

## 📦 Building Standalone Executable (.exe)

```bash
python build.py
```
Output executable is saved to `dist/WinISO-Toolkit.exe`.

---

## 📂 Project Structure

```
winiso_toolkit/
├── cli.py              # CLI parser & command orchestrator
├── pipeline.py         # End-to-end compression & build pipeline
├── deps/               # Dependency auto-installer (apt/dnf/pacman)
├── iso/                # ISO & WIM core engine
│   ├── analyzer.py     # pycdlib ISO probe & wiminfo parser
│   ├── builder.py      # xorriso & oscdimg bootable ISO builder
│   ├── compressor.py   # LZMS wimexport compressor
│   ├── debloat.py      # AppX bloatware & telemetry stripper
│   ├── downloader.py   # Official MS ISO download resolver
│   ├── drivers.py      # INF driver slipstream injector
│   ├── extract.py      # pycdlib non-mounting ISO extractor
│   ├── pebuilder.py    # WinPE rescue suite builder
│   ├── scraper.py      # Microsoft CDN ISO link downloader
│   ├── unattended.py   # autounattend.xml bypass generator
│   ├── updates.py      # Windows update (.msu/.cab) slipstreamer
│   ├── verifier.py     # SHA-256 calculator & official MS hash matcher
│   └── winpe.py        # WinPE recovery tool injector
├── usb/                # USB creation engine
│   ├── creator.py      # USB partition, write, speed/ETA calculator & validator
│   ├── detector.py     # Removable USB storage detector (lsblk -Jb / Get-Disk)
│   ├── ejector.py      # Buffer flusher & safe ejection helper
│   ├── health.py       # Speed benchmark & fake capacity detector
│   ├── partitioner.py  # Dual-partition FAT32+NTFS UEFI layout engine
│   └── wtg.py          # Windows To Go live portable OS deployer
├── utils/              # System Utilities
│   ├── logger.py       # Rotating log handler (winiso_toolkit.log) & diagnostic dumps
│   ├── platform.py     # Cross-platform subprocess runner
│   ├── progress.py     # Clamped progress callback types
│   └── vm.py           # QEMU VM sandbox boot tester
└── gui/                # PyQt6 Wizard & Theme System
    ├── main_window.py  # 7-step wizard & QEMU launcher
    └── theme.py        # Glassmorphic Dark QSS theme
tests/                  # Automated test suite (11 unit tests)
build.py                # Standalone PyInstaller build script
winiso_toolkit.spec     # PyInstaller spec file
run_tests.py            # Test runner
```

---

## 📄 License

MIT License
