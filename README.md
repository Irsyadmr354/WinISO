# WinISO Toolkit Supercharged

> **Cross-platform Windows ISO compressor, debloater, customizer & bootable USB creator.**
> Runs on **Windows** and **Linux** (macOS best-effort). Built with Python 3.11+ and PyQt6.

---

## Features

| Category | Feature |
|---|---|
| **ISO Analysis** | UDF + Joliet + ISO9660 filesystem detection (Windows 11 UDF-only ISOs fully supported) |
| **Compression** | LZMS ESD compression via wimlib — typically 40–50% size reduction |
| **Edition Control** | Select individual Windows editions to keep; remove unwanted SKUs |
| **Win 11 Bypass** | `autounattend.xml` injection — bypasses TPM 2.0, SecureBoot, RAM, CPU, MSA requirements |
| **Debloat** | Offline DISM removal of AppX bloatware, telemetry & Cortana from install image |
| **Drivers** | Slipstream `.inf` storage / network / Wi-Fi drivers into Setup media |
| **Updates** | Slipstream `.msu` / `.cab` cumulative updates offline before installation |
| **USB Creation** | Full format + file copy with speed/ETA meter and post-write SHA-256 verification |
| **Dual Partition** | FAT32 EFI boot + NTFS data layout — handles `install.wim` files > 4 GB |
| **Windows To Go** | Deploy live portable Windows OS onto USB via WIM apply |
| **WinPE Rescue** | Inject 7-Zip, DiskGenius, HWMonitor and recovery tools into boot media |
| **ISO Download** | Resolve and download official Windows 10/11 ISOs from Microsoft CDN |
| **SHA-256 Verify** | Compare downloaded ISO against official Microsoft hash database |
| **USB Health** | Write-speed benchmark + write-then-read-back fake-capacity detection |
| **QEMU Testing** | 1-click boot test of built ISO in QEMU VM sandbox |
| **GUI Wizard** | 8-step PyQt6 wizard with Deep Space dark theme, live console, animated progress |
| **CLI** | Full command-line interface for scripting and automation |

---

## Requirements

**Python 3.11+** and the following external tools:

| Tool | Platform | Purpose | Auto-install |
|---|---|---|---|
| **wimlib** (`wimlib-imagex`) | Windows + Linux | WIM/ESD read, compress, export | ✅ |
| **xorriso** | Linux (Windows optional) | Build bootable ISO | ✅ Linux |
| **oscdimg** (Windows ADK) | Windows | Build bootable ISO | Manual |
| **parted** | Linux | USB partitioning | ✅ Linux |
| **ntfs-3g** | Linux | NTFS USB formatting | ✅ Linux |

Run `winiso-toolkit --install-deps` or click **Install wimlib now** in the GUI to auto-install.

**Windows fallback:** If wimlib isn't installed, the app tries Windows built-in `DISM /Get-WimInfo` to enumerate editions, then falls back to a "keep all editions" mode so you can still proceed.

---

## Installation

```bash
# From source
git clone https://github.com/youruser/WinISO.git
cd WinISO
pip install -e .

# Or just install deps
pip install -r requirements.txt
```

### Linux — install external tools

```bash
# Debian / Ubuntu / Mint / Kali
sudo apt install wimtools xorriso ntfs-3g parted usbutils

# Arch / Manjaro / EndeavourOS
sudo pacman -S wimlib xorriso ntfs-3g parted usbutils

# Fedora / RHEL / Rocky / AlmaLinux
sudo dnf install wimlib-utils xorriso ntfs-3g parted usbutils

# openSUSE
sudo zypper install wimlib xorriso ntfs-3g parted

# Alpine
sudo apk add wimlib xorriso ntfs-3g parted

# Or let the toolkit do it:
winiso-toolkit --install-deps --confirm
```

### Windows — install wimlib

The GUI has a built-in **Install wimlib now** button that:
1. Tries `winget install Wimlib.Wimlib` first
2. Falls back to direct download from [wimlib.net](https://wimlib.net/downloads/) (no admin required)

---

## Usage

### GUI Wizard

```bash
winiso-toolkit --gui
```

8-step wizard: **ISO → Editions → Customize → Compress → USB → Confirm → Build → Done**

---

### CLI

#### Analyze an ISO
```bash
winiso-toolkit --iso win11.iso --analyze-only
```

#### Compress + bypass Win 11 requirements
```bash
winiso-toolkit --iso win11.iso --bypass-tpm --bypass-msa --output win11_slim.iso
```

#### Keep only specific editions
```bash
winiso-toolkit --iso win11.iso --edition "Home" --edition "Pro" --output win11_homepro.iso
```

#### Compress + slipstream drivers + burn to USB
```bash
winiso-toolkit --iso win11.iso \
  --inject-drivers ./drivers \
  --target /dev/sdb \
  --boot-mode both \
  --confirm
```

#### Download official Windows 11 ISO
```bash
winiso-toolkit --download-iso win11
```

#### USB health check
```bash
winiso-toolkit --target /dev/sdb --health-check
```

#### Auto-install missing dependencies
```bash
winiso-toolkit --install-deps --confirm
```

#### Test built ISO in QEMU
```bash
winiso-toolkit --iso win11_compressed.iso --test-vm
```

#### Full beast-mode pipeline
```bash
winiso-toolkit --iso win11.iso \
  --bypass-tpm --bypass-msa \
  --debloat \
  --slipstream-updates ./updates \
  --inject-drivers ./drivers \
  --inject-winpe-tools \
  --output win11_beast.iso \
  --target /dev/sdb \
  --boot-mode both \
  --use-dual-partition \
  --confirm
```

---

## Cross-Platform Notes

| Feature | Windows | Linux | macOS |
|---|---|---|---|
| ISO analysis (UDF/Joliet/ISO9660) | ✅ | ✅ | ✅ |
| WIM metadata (wimlib) | ✅ | ✅ | ✅ |
| WIM metadata fallback (DISM) | ✅ | — | — |
| ISO rebuild (oscdimg) | ✅ | — | — |
| ISO rebuild (xorriso) | ✅ optional | ✅ | ✅ |
| USB partitioning (parted) | — | ✅ | — |
| USB partitioning (diskpart) | ✅ | — | — |
| USB detection | ✅ | ✅ | — |
| Auto-install deps | ✅ winget+direct | ✅ apt/dnf/pacman/zypper/apk | manual |
| GUI wizard | ✅ | ✅ | ✅ |

---

## Running Tests

```bash
python run_tests.py
# 11 tests — all pass
```

---

## Build Standalone Executable

```bash
python build.py
# Output: dist/WinISO-Toolkit.exe  (Windows)
# Output: dist/WinISO-Toolkit      (Linux)
```

---

## Project Structure

```
winiso_toolkit/
├── cli.py                # CLI argument parser & command dispatcher
├── pipeline.py           # End-to-end compress + rebuild pipeline
├── deps/
│   └── installer.py      # Cross-platform dependency checker + auto-installer
│                         # (winget / direct download / apt / dnf / pacman / zypper / apk)
├── iso/
│   ├── analyzer.py       # ISO probe: UDF/Joliet/ISO9660, wimlib + DISM fallback
│   ├── builder.py        # Bootable ISO builder: xorriso (all platforms) + oscdimg (Windows)
│   ├── compressor.py     # LZMS wimexport compressor
│   ├── debloat.py        # Offline DISM AppX bloatware removal
│   ├── drivers.py        # .inf driver slipstream injector
│   ├── extract.py        # pycdlib ISO extractor (no mount, UDF-aware)
│   ├── pebuilder.py      # WinPE rescue suite builder
│   ├── scraper.py        # Microsoft CDN ISO resolver + downloader (retry + resume)
│   ├── unattended.py     # autounattend.xml bypass generator
│   ├── updates.py        # .msu/.cab update slipstreamer
│   ├── verifier.py       # SHA-256 calculator + official MS hash matcher
│   └── winpe.py          # WinPE recovery tool injector
├── usb/
│   ├── creator.py        # USB format + write + speed/ETA + post-write SHA-256 verify
│   ├── detector.py       # Removable USB detector (lsblk / Get-Disk / wmic fallback)
│   ├── ejector.py        # Safe buffer-flush ejector
│   ├── health.py         # Write-speed benchmark + fake-capacity detector
│   ├── partitioner.py    # Dual FAT32+NTFS partition layout
│   └── wtg.py            # Windows To Go live USB deployer
├── utils/
│   ├── logger.py         # Rotating file logger (~/.winiso_toolkit/)
│   ├── platform.py       # is_windows(), is_linux(), which(), run_command()
│   ├── progress.py       # ProgressCallback type + clamp_progress()
│   └── vm.py             # QEMU VM boot tester
├── gui/
│   ├── main_window.py    # 8-step PyQt6 wizard + live console + fade animations
│   └── theme.py          # Deep Space dark QSS theme with neon accents
└── tools/                # Auto-created: wimlib-imagex.exe extracted here on Windows
tests/                    # 11 unit tests
build.py                  # PyInstaller one-click build script
winiso_toolkit.spec       # PyInstaller spec (no block_cipher)
run_tests.py              # unittest runner
```

---

## License

MIT — see [LICENSE](LICENSE)
