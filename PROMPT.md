# PROMPT: Windows ISO Compressor & Auto-Bootable USB Creator

## CONTEXT & GOAL
Build a cross-platform application (Linux + Windows) called **"WinISO Toolkit"** with two modes:
1. **CLI** — for automation/scripting
2. **GUI** — for non-technical users (desktop app)

This application solves two main problems:
- **Problem A**: Windows ISO files (especially ones containing multiple editions bundled into a single `install.wim`) are often too large to fit on small-capacity USB flash drives (8GB/16GB).
- **Problem B**: Turning that USB drive into a valid, bootable Windows installer, with automatic detection of whether the USB capacity is sufficient.

Recommended tech stack: **Python 3.11+** for cross-platform logic, with **PyQt6 or Tkinter** for the GUI (prefer PyQt6 for a more modern UI), packaged into a single executable per OS using **PyInstaller**.

---

## MODULE 1: ISO Analyzer & Compressor

### Required features:
1. **Input**: accept a path to a Windows `.iso` file (drag-and-drop in the GUI, or a CLI argument).
2. **Auto-detect** whether the ISO is a valid Windows installer image — check for `sources/install.wim` or `sources/install.esd` inside the ISO (mount via loop device on Linux, or use the Python library `pycdlib` to read the ISO without mounting — PREFERRED, since it doesn't require root/admin permissions).
3. If a large `install.wim`/`install.esd` file is found, do the following:
   - **Read image metadata** — list all Windows editions (Home, Pro, Education, etc.) with their index number and size. Use the `wimlib` library via a Python binding (`pip install pywimlib` if available, or subprocess calls to the `wimlib-imagex`/`wimexport`/`wiminfo` binaries) — MUST be cross-platform: on Linux use `wimlib` from the package manager (apt/pacman/dnf); on Windows use a bundled `wimlib-imagex.exe` or native DISM.
   - **Show the choice to the user** (GUI: checkbox list, CLI: numbered menu) — the user selects one or more editions to keep, and the rest are dropped.
   - **Compress** the selected edition(s) into `.esd` format using **LZMS** compression (`wimlib` command: `wimexport source.wim <index> dest.esd --solid --compress=LZMS`).
   - Show a **real-time progress bar** (parse `wimexport`'s percentage output, not just a generic spinner).
4. **Estimate size before processing** — calculate an estimated compressed size based on typical LZMS compression ratios (~40-50% of original size), and show this to the user BEFORE they commit to the process (so they know upfront whether the result will fit their USB drive).
5. **Rebuild a new ISO** with a CORRECT and VALID boot structure — this is the critical part that frequently fails:
   - MUST use a tool that preserves the boot record correctly. Recommended: **`oscdimg.exe`** (Windows, from the Windows ADK) or **`xorriso`** (Linux) with complete, FIELD-TESTED boot parameters (verified working on Windows 11 25H2 Pro, successful boot on a ThinkPad in UEFI mode):
     ```
     xorriso -as mkisofs \
       -iso-level 3 \
       -full-iso9660-filenames \
       -J \
       -joliet-long \
       -r \
       -V "<VOLUME_LABEL_FROM_ORIGINAL_ISO>" \
       -o output.iso \
       -c boot/boot.cat \
       -b boot/etfsboot.com \
       -no-emul-boot \
       -boot-load-size 8 \
       -boot-info-table \
       -eltorito-alt-boot \
       -e efi/microsoft/boot/efisys.bin \
       -no-emul-boot \
       -isohybrid-gpt-basdat \
       .
     ```
     (must be run from INSIDE the extracted ISO folder, using `.` as the source — not an absolute path)

     **Critical points that MUST be included** (lessons learned from real trial-and-error — commands missing these points failed to boot):
     - `-c boot/boot.cat` — REQUIRED. This explicitly sets the boot catalog location (the El Torito boot record index). Without it, xorriso often fails to generate a correct boot record even though the build "appears" to complete without error — the resulting ISO is NOT bootable, usually flagged by the warning "No proposals available for boot related commands," which is EASILY MISSED because the build still "finishes."
     - `-V "<volume label>"` — MUST be taken from the original ISO's volume label (read it first with `isoinfo -d -i original.iso | grep "Volume id"` or equivalent). Do NOT leave it blank or set it arbitrarily — some Windows Setup processes are sensitive to this.
     - `-J -joliet-long -full-iso9660-filenames -r` — this combination preserves long-filename compatibility in the Windows style and Rock Ridge extensions, helping Windows Setup read the file structure correctly.
   - **MANDATORY validation after building**: verify the resulting ISO has a valid El Torito boot record (use `xorriso -indev output.iso -report_el_torito plain` to check, or `isoinfo -d -i output.iso` to confirm a boot record exists). **DO NOT consider the ISO complete if the warning "No proposals available for boot related commands" appears during the build** — this indicates the ISO is NOT bootable. The application must automatically detect this warning (by parsing xorriso's stderr) and either retry with corrected parameters or clearly report the failure to the user instead of silently producing a broken ISO.
   - Optional extra test: if `qemu` is available on the system, optionally boot-test the resulting ISO in a headless virtual machine before offering it to the user (nice-to-have, not required).

### Required error handling:
- If `wimlib` is not installed, the application must **auto-install** it (see Module 3).
- If the ISO is corrupted or unreadable, show a clear error message (not a raw crash/traceback to the user).
- If the compression process is interrupted (user cancels midway), ensure temporary/partial files are automatically deleted — do NOT leave half-finished files that could confuse the next run.

---

## MODULE 2: USB Detector & Bootable Creator

### Required features:
1. **Detect all connected removable devices**, cross-platform:
   - Linux: parse `lsblk -J` (JSON output) or use the `pyudev` library, filtering devices with the `RM=1` (removable) flag and excluding internal disks.
   - Windows: use `wmic diskdrive` or the more modern `Get-Disk` via a PowerShell subprocess, filtering for `BusType -eq 'USB'`.
2. **Display info for each device**: name/label, total capacity, current filesystem (if any).
3. **Validate capacity BEFORE processing**: compare the ISO size (from Module 1's output, or an existing ISO) against the USB's capacity. If insufficient:
   - Show a clear message: "Your USB is X GB, this ISO requires Y GB. Choose: (a) compress the ISO further if more editions/languages can still be dropped, (b) use a larger USB drive."
   - **DO NOT** let the user proceed to burning if the capacity is clearly insufficient — prevent this upfront rather than letting it fail midway (this is what wastes the most user time).
4. **Create the bootable USB**:
   - MUST support both **UEFI (GPT)** and **Legacy (MBR)** — auto-detect from BIOS mode where possible, or give the user an explicit choice with a brief explanation of when to use which.
   - Process: format the device (mandatory confirmation warning — ALL DATA WILL BE ERASED, require the user to type "YES" or check an explicit confirmation box before proceeding), write the partition table, copy the extracted ISO files, write the boot sector.
   - **Use native per-OS approaches for maximum reliability** (do NOT reinvent already-proven tools):
     - On Linux: use `parted`/`sfdisk` libraries for partitioning, `mkfs.ntfs`/`mkfs.vfat` for formatting, then manually copy files + write the Windows boot sector (use `ms-sys`, or the `bootsect.exe` approach if available from the Windows ISO itself — Windows ISOs typically already include `boot/bootsect.exe`; USE THIS instead of GRUB like WoeUSB does, since Windows doesn't need GRUB).
     - On Windows: can invoke `diskpart` via subprocess with an automated script (clean, create partition, format fs=ntfs quick, assign), then `xcopy`/`robocopy` to copy files, and `bootsect.exe /nt60 <drive>` to write the boot sector.
   - **Accurate progress reporting** — this is a critical point. DO NOT use a counter that can overflow/crash like a bug encountered in practice (real example: WoeUSB's `wxAssertionError: pos <= m_rangeMax` caused by the progress counter exceeding the total). Instead: calculate the total bytes to be copied UPFRONT before starting, then progress = bytes_copied / total_bytes, with an explicit `min(progress, 100)` clamp so the display can never overflow.
5. **Post-write verification**: after the process finishes, MUST run a checksum verification (re-read critical files from the USB, compare MD5/SHA256 against the source) to ensure there's no silent corruption. This is IMPORTANT because USB flash drives sometimes have I/O issues that don't always throw an explicit error during writing, yet the data ends up corrupted.

---

## MODULE 3: Dependency Auto-Installer

### Required features:
The application must detect the OS and available package manager, then auto-install any missing dependencies:

**Linux (detect the distro first via `/etc/os-release`):**
- Arch/Manjaro: `pacman -S --needed wimlib xorriso ntfs-3g parted usbutils`
- Debian/Ubuntu: `apt install wimtools genisoimage ntfs-3g parted usbutils`
- Fedora: `dnf install wimlib-utils xorriso ntfs-3g parted usbutils`

**Windows:**
- Check whether the **Windows ADK** (for `oscdimg.exe`, `dism.exe`) is installed. If not, download the official installer from Microsoft (provide the official link, do NOT re-host a third-party installer) and invoke it, OR use a portable alternative such as the Windows build of `wimlib` (downloaded from the official wimlib.net) which doesn't require a full ADK installation.
- MUST ask for user confirmation before installing anything (no silent installs without permission, especially for large software like the Windows ADK).

### Important principles:
- ALL dependency installations must be **idempotent** — check whether something is already installed before attempting to install it again (`which wimlib-imagex` or `command -v` on Linux, `where.exe` on Windows).
- Provide clear logging to the user about what is being installed and why.
- **DO NOT** request sudo/administrator privileges beyond what's strictly necessary — separate operations that require root (formatting a device, installing packages) from those that don't (reading an ISO, compressing a file in the user's folder).

---

## MODULE 4: GUI Layer

- Build a step-by-step wizard (not a single page with all options at once):
  1. Step 1: Select the source ISO file
  2. Step 2: Show edition info, let the user pick which to keep
  3. Step 3: Compress (with an accurate progress bar)
  4. Step 4: Select the target USB (with automatic capacity validation)
  5. Step 5: Final confirmation (summary of everything that will happen + warning that USB data will be erased)
  6. Step 6: Burning process with progress + estimated time remaining
  7. Step 7: Automatic verification + final result (success/failure with details)
- Provide a **non-interactive CLI mode** covering all the steps above via flags, e.g.:
  ```
  winiso-toolkit --iso path/to/win11.iso --edition Pro --target /dev/sda --confirm
  ```

---

## IMPORTANT NOTES FOR THE AI WORKING ON THIS

1. **This is a large project** — build it modularly, test each module independently before full integration. Do not attempt to generate everything at once in one large file.
2. **Prioritize reliability over fancy UX** — silent failure is far more dangerous than a less polished UI, especially for operations that can damage USB data or produce an installer that fails to boot.
3. **Test under real-world conditions**: a USB drive with barely-enough capacity, genuine multi-edition Windows ISOs from Microsoft, both boot modes (UEFI+GPT and Legacy+MBR), and interrupting the process midway (make sure state doesn't get corrupted).
4. Do not assume external tools (`wimlib`, `xorriso`, etc.) always succeed — always check exit codes and parse stderr to detect real failures, rather than trusting a process that "finished without an exception" as proof of success.
