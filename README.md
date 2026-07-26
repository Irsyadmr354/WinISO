# WinISO Toolkit Supercharged 🚀

**Cross-platform Windows ISO Compressor, Debloater, Customizer & Bootable USB Creator**
— runs on **Linux** and **Windows** (macOS/BSD best-effort).

---

## ✨ Features

| Feature | CLI | GUI |
|---|---|---|
| LZMS ESD compression (removes unused editions) | ✅ | ✅ |
| Windows 11 TPM / SecureBoot / RAM / CPU bypass | ✅ | ✅ |
| Microsoft Account bypass (BypassNRO) | ✅ | ✅ |
| Telemetry & bloatware removal | ✅ | ✅ |
| Cumulative update slipstreaming (.msu/.cab) | ✅ | ✅ |
| Driver slipstreaming (.inf) | ✅ | ✅ |
| Bootable USB creation (UEFI + Legacy) | ✅ | ✅ |
| Dual-partition layout (FAT32 EFI + NTFS Data) | ✅ | ✅ |
| Windows To Go live USB deployer | ✅ | — |
| WinPE rescue media builder | ✅ | — |
| Official MS ISO downloader | ✅ | — |
| SHA-256 checksum verifier (official MS hashes) | ✅ | ✅ |
| USB health & fake-capacity detector | ✅ | ✅ |
| QEMU VM boot tester | ✅ | ✅ |
| Auto dependency installer | ✅ | ✅ |

---

## 📦 Requirements

- **Python 3.11+**
- **pycdlib** — ISO reading (installed automatically via pip)
- **PyQt6** — GUI (installed automatically via pip)

### External Tools (auto-installable via `--install-deps`)

| Tool | Linux | Windows |
|---|---|---|
| **wimlib** (`wimlib-imagex`) | `apt/pacman/dnf/zypper/apk` | winget or auto-download from wimlib.net |
| **xorriso** | `apt/pacman/dnf/zypper` | optional (fallback for oscdimg) |
| **oscdimg** (Windows ADK) | not needed | optional (preferred over xorriso) |
| **parted**, **ntfs-3g** | `apt/pacman/dnf` | not needed (diskpart used) |

---

## 📥 Installation

```bash
pip install -e .
```

Or with requirements:

```bash
pip install -r requirements.txt
```

### Install external tools automatically

```bash
# Linux — detects distro and runs apt/pacman/dnf/zypper/apk
winiso-toolkit --install-deps

# Windows — tries winget first, then direct download from wimlib.net
winiso-toolkit --install-deps
```

Supported Linux distros: Debian, Ubuntu, Mint, Pop!_OS, Kali, Raspbian, Arch, Manjaro, EndeavourOS, Garuda, Fedora, RHEL, CentOS, Rocky, AlmaLinux, openSUSE Leap/Tumbleweed, SLES, Alpine, Void, Gentoo.

---

## 🚀 Usage

### GUI (PyQt6 dark wizard)

```bash
winiso-toolkit --gui
```

8-step wizard: ISO → Editions → Customize → Compress → USB → Confirm → Burn → Done.

---

### CLI — compress ISO, apply bypasses, burn to USB

```bash
winiso-toolkit \
  --iso win11.iso \
  --bypass-tpm --bypass-msa --debloat \
  --output win11_lean.iso \
  --target /dev/sdb \
  --confirm
```

### List editions inside an ISO

```bash
winiso-toolkit --iso win11.iso --analyze-only
```

### Keep only specific editions

```bash
winiso-toolkit --iso win11.iso --edition "Home" --edition "Pro" --output win11_homeandpro.iso
```

### Slipstream updates + inject drivers

```bash
winiso-toolkit --iso win11.iso \
  --slipstream-updates ./updates \
  --inject-drivers ./drivers \
  --output win11_updated.iso
```

### Download official Microsoft ISO

```bash
winiso-toolkit --download-iso win11
winiso-toolkit --download-iso win10
```

### Windows To Go live USB

```bash
winiso-toolkit --iso win11.iso --target /dev/sdb --wtg --confirm
```

### Build WinPE rescue media

```bash
winiso-toolkit --iso win11.iso --build-pe-rescue --output rescue.iso
```

### USB health check

```bash
winiso-toolkit --target /dev/sdb --health-check
```

### Test ISO in QEMU

```bash
winiso-toolkit --iso win11_lean.iso --test-vm
```

### Install missing dependencies

```bash
winiso-toolkit --install-deps --confirm
```

---

## 📂 Project Structure

```
winiso_toolkit/
├── cli.py              CLI parser & command dispatcher
├── pipeline.py         End-to-end compress → inject → rebuild pipeline
├── deps/
│   └── installer.py    Multi-platform dependency installer (21 distros)
├── iso/
│   ├── analyzer.py     pycdlib ISO probe, UDF/Joliet/ISO9660, wimlib + DISM
│   ├── builder.py      xorriso / oscdimg bootable ISO builder
│   ├── compressor.py   LZMS wimexport ESD compressor
│   ├── debloat.py      AppX bloatware & telemetry stripper (offline DISM)
│   ├── drivers.py      INF driver slipstream injector
│   ├── extract.py      pycdlib ISO extractor (UDF-aware)
│   ├── pebuilder.py    WinPE rescue media builder
│   ├── scraper.py      Microsoft CDN ISO resolver + downloader
│   ├── unattended.py   autounattend.xml bypass generator
│   ├── updates.py      Windows update (.msu/.cab) slipstreamer
│   ├── verifier.py     SHA-256 + official MS hash matcher
│   └── winpe.py        WinPE recovery tool injector
├── usb/
│   ├── creator.py      USB format + write + verify (Linux & Windows)
│   ├── detector.py     USB device lister (lsblk / Get-Disk / wmic)
│   ├── ejector.py      Safe buffer-flush eject
│   ├── health.py       Write speed benchmark + fake capacity detector
│   ├── partitioner.py  Dual-partition FAT32+NTFS UEFI layout
│   └── wtg.py          Windows To Go deployer
├── utils/
│   ├── logger.py       Rotating log handler (~/.winiso_toolkit/)
│   ├── platform.py     Cross-platform subprocess helpers
│   ├── progress.py     Clamped ProgressCallback type
│   └── vm.py           QEMU sandbox boot tester
└── gui/
    ├── main_window.py  8-step PyQt6 wizard with live terminal console
    └── theme.py        Deep Space dark theme (glassmorphism QSS)
tests/                  11 unit tests (python run_tests.py)
build.py                PyInstaller standalone exe builder
```

---

## 🧪 Tests

```bash
python run_tests.py
```

11/11 pass. Covers: ISO analyzer, WIM parser, unattended XML, driver discovery, USB capacity, SHA-256 verifier, debloat script, update scanner, scraper, PE builder.

---

## 📦 Build standalone executable

```bash
python build.py
# → dist/WinISO-Toolkit.exe
```

---

## 🔒 Security notes

- All USB device paths validated with regex before use — no shell injection
- Diskpart scripts written to unique temp files (`mkstemp`) — no TOCTOU race
- Windows disk numbers validated as non-negative integers before any interpolation
- No credentials, tokens, or PII collected or transmitted

---

## 📄 License

MIT — see [LICENSE](LICENSE)
