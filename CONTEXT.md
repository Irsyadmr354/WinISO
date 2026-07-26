# Context: Windows Installation Troubleshooting

Rangkuman troubleshooting instalasi Windows yang menjadi latar belakang project WinISO Toolkit.

---

## Kondisi Awal

- Laptop **tanpa OS** (Windows hilang), BIOS masih bisa diakses
- OS sebelumnya: **Arch Linux**
- HP: **Redmi 13 (HyperOS / Android 14+)**
- Tidak punya USB flashdisk cadangan

---

## Percobaan Boot dari HP via Kabel USB-C

**Kesimpulan: Tidak bisa.**

Android modern (6+) hanya menyediakan MTP / PTP / RNDIS / MIDI lewat USB.
Mode **USB Mass Storage** sudah dihapus total dari Android sejak Android 6+.
BIOS/UEFI hanya bisa membaca **USB Mass Storage Class** — tidak bisa baca MTP.
Developer Options tidak membantu karena fiturnya dihapus di kernel level, bukan sekadar disembunyikan.

---

## Media Instalasi: Flashdisk

Flashdisk dicek dengan `badblocks`:

- **0 bad block** — flashdisk sehat secara fisik

---

## Percobaan WoeUSB

- Proses sering macet di tengah
- GUI crash
- Kadang I/O error
- Tidak pernah selesai stabil

**Kesimpulan:** Bug WoeUSB, bukan hardware.

---

## Beralih ke Ventoy + ISO Custom

ISO Windows asli terlalu besar → dilakukan konversi:

```
install.wim → install.esd (LZMS compression via wimlib)
```

Ukuran ISO hasil: **≈ 5.8 GB** (dari aslinya ≈ 7.9 GB)

ISO baru dibuat ulang dari folder hasil ekstrak (`~/win11_new_iso`) menggunakan **xorriso**.

### Masalah saat build xorriso

Muncul warning:

```
No proposals available for boot related commands
```

Artinya **El Torito boot record tidak terbentuk sempurna** — ISO dibuat tapi struktur boot-nya tidak identik dengan ISO resmi Microsoft.

---

## Hasil Boot di Ventoy (Normal Mode)

Alur yang terjadi:

```
BIOS → Ventoy → Pilih ISO → Layar hitam beberapa detik → Kembali ke menu Ventoy
```

- Tidak ada error BCD
- Tidak ada blue screen
- Tidak ada logo Windows
- Ventoy fallback ke menu utama

**Analisis:** ISO terbaca dan dicoba di-boot oleh Ventoy, tapi bootloader Windows gagal melanjutkan karena boot record tidak lengkap. Ventoy fallback ke menu.

---

## Dugaan Penyebab Loop

ISO hasil rebuild kehilangan atau tidak memiliki boot metadata lengkap:

- El Torito boot catalog
- `boot/etfsboot.com` (Legacy BIOS boot)
- `efi/microsoft/boot/efisys.bin` (UEFI boot)
- GPT hybrid MBR information
- `-isohybrid-gpt-basdat` flag

---

## Solusi yang Direncanakan

Rebuild ISO dengan parameter boot **lengkap**:

```bash
xorriso -as mkisofs \
  -o ~/Win11_Pro_Small_v2.iso \
  -iso-level 3 \
  -allow-limited-size \
  -b boot/etfsboot.com \
  -no-emul-boot \
  -boot-load-size 8 \
  -boot-info-table \
  -eltorito-alt-boot \
  -e efi/microsoft/boot/efisys.bin \
  -no-emul-boot \
  -isohybrid-gpt-basdat \
  ~/win11_new_iso
```

Sebelum rebuild, verifikasi dulu apakah ISO hasil modifikasi memang punya boot entries (BIOS dan UEFI) menggunakan:

```bash
xorriso -indev ~/Win11_Pro_Small.iso -report_el_torito plain
```

---

## Status Saat Ini

| Item | Status |
|---|---|
| Laptop bisa boot Ventoy | ✅ |
| Flashdisk sehat | ✅ |
| Ventoy berfungsi normal | ✅ |
| ISO terbaca oleh Ventoy | ✅ |
| Error BCD hilang | ✅ |
| Windows Setup muncul | ❌ |
| Boot ISO tidak loop ke Ventoy | ❌ |

---

## Relevansi ke WinISO Toolkit

Pengalaman troubleshooting ini adalah **latar belakang langsung** dari project WinISO Toolkit:

- Kebutuhan compress `install.wim` → `install.esd` untuk muat di flashdisk kecil → fitur **LZMS ESD compressor**
- Kebutuhan rebuild ISO dengan boot record yang benar → fitur **xorriso/oscdimg ISO builder** dengan El Torito validation
- Masalah boot record yang tidak lengkap → fitur **`_validate_boot_record()`** di `builder.py`
- Kebutuhan tool yang bisa dipakai dari Linux → **cross-platform support** (Linux + Windows)
- Pemilihan edisi Windows yang akan di-keep → fitur **edition selector** di GUI/CLI

---

## Cara Cek Edisi di dalam WIM/ESD

**Linux (wimlib):**

```bash
wiminfo ~/win11_new_iso/sources/install.esd
```

**Windows (DISM):**

```cmd
dism /Get-WimInfo /WimFile:D:\sources\install.wim
```

**Windows (PowerShell):**

```powershell
Get-WindowsImage -ImagePath D:\sources\install.wim
```
