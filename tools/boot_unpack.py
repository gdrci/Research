"""Unpack Android boot / vendor_boot (v3/v4) images, legacy-LZ4 ramdisks and newc cpio archives.

Usage: python3 tools/boot_unpack.py <image> <out_dir>
Needs: pip install lz4
"""
import io, os, re, struct, sys
import lz4.block

def legacy_lz4(data, cap=8 << 20):
    """Android legacy LZ4 container: repeated [u32 size][lz4 block]; blocks up to 8 MiB."""
    out = io.BytesIO(); o = 4
    while o + 4 <= len(data):
        n = struct.unpack_from("<I", data, o)[0]; o += 4
        if n in (0x184C2102, 0x184D2204): continue
        if n == 0 or o + n > len(data): break
        out.write(lz4.block.decompress(data[o:o + n], uncompressed_size=cap)); o += n
    return out.getvalue()

def cpio_extract(blob, dest):
    o = 0; files = 0; links = 0
    while o < len(blob) and blob[o:o + 6] == b"070701":
        f = lambda i: int(blob[o + 6 + i * 8:o + 14 + i * 8], 16)
        mode, fsz, nsz = f(1), f(6), f(11)
        name = blob[o + 110:o + 110 + nsz - 1].decode(errors="replace")
        o = (o + 110 + nsz + 3) & ~3
        if name == "TRAILER!!!": break
        t = os.path.join(dest, name)
        kind = mode & 0o170000
        if kind == 0o040000: os.makedirs(t, exist_ok=True)
        elif kind == 0o120000:
            os.makedirs(os.path.dirname(t), exist_ok=True)
            if not os.path.lexists(t): os.symlink(blob[o:o + fsz].decode(), t); links += 1
        elif kind == 0o100000:
            os.makedirs(os.path.dirname(t), exist_ok=True)
            with open(t, "wb") as fh: fh.write(blob[o:o + fsz])
            files += 1
        o = (o + fsz + 3) & ~3
    return files, links

def main(img, out):
    b = open(img, "rb").read(); os.makedirs(out, exist_ok=True)
    if b[:8] == b"ANDROID!":
        ksz, rsz, osver, hsz = struct.unpack_from("<4I", b, 8)
        cmd = b[44:44 + 1536].split(b"\0")[0].decode(errors="replace")
        print(f"boot header v4: kernel={ksz} ramdisk={rsz} cmdline={cmd!r}")
        kern = b[4096:4096 + ksz]
        open(os.path.join(out, "kernel.bin"), "wb").write(kern)
        m = re.search(rb"Linux version [^\n\x00]{0,100}", kern)
        if m: print("kernel:", m.group(0).decode(errors="replace"))
        rd = b[4096 + ((ksz + 4095) // 4096) * 4096:][:rsz]
        blob = legacy_lz4(rd)
        print("ramdisk files:", cpio_extract(blob, os.path.join(out, "ramdisk")))
    elif b[:8] == b"VNDRBOOT":
        page, = struct.unpack_from("<I", b, 12)
        vrd = struct.unpack_from("<I", b, 24)[0]
        cmd = b[28:28 + 2048].split(b"\0")[0].decode(errors="replace")
        hsz, dtb = struct.unpack_from("<I", b, 2096)[0], struct.unpack_from("<I", b, 2100)[0]
        pg = lambda x: (x + page - 1) // page * page
        print(f"vendor_boot v4: page={page} ramdisk={vrd} dtb={dtb}\ncmdline: {cmd}")
        rd = b[pg(hsz):pg(hsz) + vrd]
        open(os.path.join(out, "vendor.dtb"), "wb").write(b[pg(hsz) + pg(vrd):][:dtb])
        blob = legacy_lz4(rd, cap=8 << 20)
        print("vendor ramdisk files:", cpio_extract(blob, os.path.join(out, "ramdisk")))
    else:
        raise SystemExit("unsupported image")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
