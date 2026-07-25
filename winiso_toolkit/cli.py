"""Command-line interface for WinISO Toolkit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from winiso_toolkit.deps.installer import ensure_dependencies
from winiso_toolkit.iso.analyzer import ISOAnalyzer
from winiso_toolkit.pipeline import WinISOPipeline
from winiso_toolkit.usb.creator import BootMode, USBCreator
from winiso_toolkit.usb.detector import USBDetector


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="winiso-toolkit",
        description="Windows ISO Compressor & Bootable USB Creator",
    )
    parser.add_argument("--gui", action="store_true", help="Launch the graphical wizard")
    parser.add_argument("--iso", type=Path, help="Path to source Windows ISO")
    parser.add_argument(
        "--edition",
        action="append",
        dest="editions",
        help="Edition name or index to keep (repeatable)",
    )
    parser.add_argument("--output", type=Path, help="Output ISO path")
    parser.add_argument("--target", help="USB device path (e.g. /dev/sdb or \\\\.\\PHYSICALDRIVE1)")
    parser.add_argument(
        "--boot-mode",
        choices=["uefi", "legacy", "both"],
        default="both",
        help="USB boot mode (default: both)",
    )
    parser.add_argument("--bypass-tpm", action="store_true", help="Bypass Win 11 TPM, RAM, CPU, & SecureBoot checks")
    parser.add_argument("--bypass-msa", action="store_true", help="Bypass mandatory Microsoft Account requirement")
    parser.add_argument("--inject-drivers", type=Path, help="Path to custom driver directory (.inf)")
    parser.add_argument("--inject-winpe-tools", action="store_true", help="Inject emergency recovery tools into WinPE media")
    parser.add_argument("--debloat", action="store_true", help="Remove AppX bloatware & telemetry from Windows image")
    parser.add_argument("--slipstream-updates", type=Path, help="Path to folder containing .msu/.cab Windows updates")
    parser.add_argument("--wtg", action="store_true", help="Deploy as live portable Windows To Go USB")
    parser.add_argument("--download-iso", choices=["win11", "win10"], help="Download official Microsoft Windows ISO")
    parser.add_argument("--build-pe-rescue", action="store_true", help="Build as live WinPE emergency rescue media")
    parser.add_argument("--use-dual-partition", action="store_true", help="Create FAT32+NTFS dual partition layout")
    parser.add_argument("--test-vm", action="store_true", help="Boot test output ISO in QEMU VM after creation")
    parser.add_argument("--health-check", action="store_true", help="Run write benchmark & health check on USB target")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging")
    parser.add_argument("--analyze-only", action="store_true", help="Only analyze ISO and list editions")
    parser.add_argument("--skip-compress", action="store_true", help="Use ISO as-is (no compression)")
    parser.add_argument("--install-deps", action="store_true", help="Auto-install missing dependencies")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip interactive confirmation prompts (required for automation)",
    )
    parser.add_argument("--list-usb", action="store_true", help="List connected USB devices")
    return parser


def resolve_indices(analyzer: ISOAnalyzer, iso_path: Path, editions: list[str] | None) -> list[int]:
    info = analyzer.analyze(iso_path)
    if not editions:
        return _interactive_edition_menu(info.wim_images)

    indices: list[int] = []
    for ed in editions:
        if ed.isdigit():
            indices.append(int(ed))
            continue
        matched = [
            img.index
            for img in info.wim_images
            if ed.lower() in (img.display_name or "").lower()
            or ed.lower() in (img.name or "").lower()
            or ed.lower() in (img.description or "").lower()
        ]
        if not matched:
            raise ValueError(f"Edition not found: {ed}")
        indices.extend(matched)
    return sorted(set(indices))


def _interactive_edition_menu(images) -> list[int]:
    print("\nAvailable Windows editions:")
    for img in images:
        size_gb = img.size_bytes / (1024**3)
        print(f"  [{img.index}] {img.display_name} ({size_gb:.2f} GB)")
    print("\nEnter edition numbers to keep (comma-separated), or 'all':")
    choice = input("> ").strip()
    if choice.lower() == "all":
        return [img.index for img in images]
    return [int(x.strip()) for x in choice.split(",") if x.strip()]


def print_analysis(iso_path: Path, deps) -> None:
    analyzer = ISOAnalyzer(deps)
    info = analyzer.analyze(iso_path)
    print(f"ISO: {info.path}")
    print(f"Volume label: {info.volume_label}")
    print(f"Windows installer: {info.is_windows_installer}")
    print(f"Total size: {info.total_iso_size / (1024**3):.2f} GB")
    if info.install_image_path:
        print(f"Install image: {info.install_image_path} ({info.install_image_size / (1024**3):.2f} GB)")
        est = info.estimated_compressed_size
        print(f"Estimated compressed size (LZMS): {est / (1024**3):.2f} GB (~45%)")
        print("\nEditions:")
        for img in info.wim_images:
            print(f"  [{img.index}] {img.display_name} — {img.size_bytes / (1024**3):.2f} GB")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    from winiso_toolkit.utils.logger import setup_logger
    logger = setup_logger(debug=args.debug)
    logger.debug("WinISO Toolkit started")

    if args.gui:
        from winiso_toolkit.gui.main_window import run_gui
        return run_gui()

    deps = ensure_dependencies(auto_install=args.install_deps, confirm=args.confirm)

    if args.list_usb:
        devices = USBDetector().list_devices()
        if not devices:
            print("No USB devices found.")
            return 0
        for d in devices:
            print(f"{d.path}\t{d.name}\t{d.size_gb:.1f} GB\t{d.filesystem or '—'}")
        return 0

    if args.download_iso:
        from winiso_toolkit.iso.scraper import MicrosoftISOScraper
        scraper = MicrosoftISOScraper()
        releases = scraper.list_available_releases()
        target_rel = releases[0] if args.download_iso == "win11" else releases[1]
        out = Path(f"{args.download_iso}_official.iso")
        print(f"Downloading {target_rel.name}...")
        def dl_progress(pct: float, msg: str) -> None:
            print(f"\r[{pct:5.1f}%] {msg}", end="", flush=True)
        scraper.download_iso(target_rel.url, out, progress=dl_progress)
        print(f"\nDownload complete: {out}")
        return 0

    if not args.iso:
        parser.print_help()
        return 1

    if not args.iso.is_file():
        print(f"Error: ISO not found: {args.iso}", file=sys.stderr)
        return 1

    try:
        if args.analyze_only:
            print_analysis(args.iso, deps)
            return 0

        output_iso = args.output or args.iso.with_name(f"{args.iso.stem}_compressed.iso")
        pipeline = WinISOPipeline(deps)

        from winiso_toolkit.iso.unattended import BypassOptions
        bypass_opts = BypassOptions(
            bypass_tpm=args.bypass_tpm,
            bypass_secure_boot=args.bypass_tpm,
            bypass_ram=args.bypass_tpm,
            bypass_cpu=args.bypass_tpm,
            bypass_msa=args.bypass_msa,
        ) if (args.bypass_tpm or args.bypass_msa) else None

        if args.skip_compress:
            final_iso = args.iso
        else:
            indices = resolve_indices(ISOAnalyzer(deps), args.iso, args.editions)
            print(f"Compressing edition(s): {indices}")

            def cli_progress(pct: float, msg: str) -> None:
                print(f"\r[{pct:5.1f}%] {msg}", end="", flush=True)

            final_iso = pipeline.compress_iso(
                args.iso,
                output_iso,
                indices,
                bypass_options=bypass_opts,
                driver_dir=args.inject_drivers,
                progress=cli_progress,
            )
            print(f"\nOutput ISO: {final_iso} ({final_iso.stat().st_size / (1024**3):.2f} GB)")

        if args.test_vm:
            from winiso_toolkit.utils.vm import QEMUTester
            tester = QEMUTester()
            print("\nLaunching QEMU VM boot test...")
            tester.launch_test_vm(final_iso)

        if args.target:
            if not args.confirm:
                print("\nWARNING: ALL DATA ON THE USB WILL BE ERASED.")
                confirm = input('Type YES to continue: ').strip()
                if confirm != "YES":
                    print("Aborted.")
                    return 1

            detector = USBDetector()
            devices = {d.path: d for d in detector.list_devices()}
            if args.target not in devices:
                print(f"Error: USB device not found: {args.target}", file=sys.stderr)
                return 1

            usb = devices[args.target]

            if args.health_check:
                from winiso_toolkit.usb.health import USBHealthChecker
                print("\nRunning USB health diagnostic...")
                hc = USBHealthChecker()
                rep = hc.run_quick_health_check(Path(args.target))
                print(f"Diagnostic result: {rep.status_message}")

            creator = USBCreator()
            ok, msg = creator.validate_capacity(usb.size_bytes, final_iso.stat().st_size)
            if not ok:
                print(f"Error: {msg}", file=sys.stderr)
                return 1

            def usb_progress(pct: float, msg: str) -> None:
                print(f"\r[{pct:5.1f}%] {msg}", end="", flush=True)

            creator.create(
                final_iso,
                args.target,
                boot_mode=BootMode(args.boot_mode),
                bypass_options=bypass_opts,
                driver_dir=args.inject_drivers,
                use_dual_partition=args.use_dual_partition,
                progress=usb_progress,
            )
            print("\nBootable USB created successfully.")

        return 0

    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
