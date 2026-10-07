"""List files in a FAT12/16/32 image, including long file names (LFN).

Usage: python3 tools/fat_list.py <image> [max_entries]
Standard library only.
"""
import struct, sys

def load(path):
    return open(path, "rb").read()

def bpb(img):
    bps, spc, rsv, nfats = struct.unpack_from("<HBHB", img, 11)
    root_ents = struct.unpack_from("<H", img, 17)[0]
    tot16 = struct.unpack_from("<H", img, 19)[0]
    spf16 = struct.unpack_from("<H", img, 22)[0]
    spf = spf16 or struct.unpack_from("<I", img, 36)[0]
    tot = tot16 or struct.unpack_from("<I", img, 32)[0]
    root_cluster = struct.unpack_from("<I", img, 44)[0] if spf16 == 0 else 0
    data_start = (rsv + nfats * spf + (root_ents * 32 + bps - 1) // bps) * bps
    return dict(bps=bps, spc=spc, rsv=rsv, nfats=nfats, root_ents=root_ents, spf=spf,
                data_start=data_start, root_cluster=root_cluster, fat32=spf16 == 0)

def fat_next(img, B, cluster):
    fat_off = B["rsv"] * B["bps"]
    if B["fat32"]:
        return struct.unpack_from("<I", img, fat_off + cluster * 4)[0] & 0x0FFFFFFF
    return struct.unpack_from("<H", img, fat_off + cluster * 2)[0]

def chain(img, B, first):
    out, c = [], first
    while 2 <= c < (0x0FFFFFF8 if B["fat32"] else 0xFFF8) and len(out) < 1 << 20:
        out.append(c); c = fat_next(img, B, c)
    return out

def cluster_bytes(img, B, c):
    off = B["data_start"] + (c - 2) * B["spc"] * B["bps"]
    return img[off:off + B["spc"] * B["bps"]]

def read_dir(img, B, raw):
    entries, lfn = [], []
    for i in range(0, len(raw), 32):
        e = raw[i:i + 32]
        if e[0] == 0: break
        if e[0] == 0xE5: lfn = []; continue
        if e[11] == 0x0F:
            lfn.insert(0, e[1:11] + e[14:26] + e[28:32]); continue
        name = e[0:8].decode("latin-1").rstrip()
        ext = e[8:11].decode("latin-1").rstrip()
        short = name + ("." + ext if ext else "")
        if lfn:
            raw_name = b"".join(lfn).decode("utf-16-le", errors="replace").split("\x00")[0]
            short = raw_name
        lfn = []
        attr = e[11]
        hi, lo = struct.unpack_from("<HH", e, 20)[0], struct.unpack_from("<H", e, 26)[0]
        first = (hi << 16) | lo if B["fat32"] else lo
        size = struct.unpack_from("<I", e, 28)[0]
        entries.append(dict(name=short, dir=bool(attr & 0x10), first=first, size=size))
    return entries

def walk(img, B, cluster_list_raw, prefix, out, depth, maxd=6):
    for ent in read_dir(img, B, cluster_list_raw(prefix)):
        if ent["name"] in (".", ".."): continue
        path = prefix + ent["name"]
        if ent["dir"]:
            out.append(("D", path, 0))
            if depth < maxd and ent["first"] >= 2:
                raw = b"".join(cluster_bytes(img, B, c) for c in chain(img, B, ent["first"]))
                walk(img, B, lambda _p, r=raw: r, path + "/", out, depth + 1, maxd)
        else:
            out.append(("F", path, ent["size"]))

if __name__ == "__main__":
    img = load(sys.argv[1]); B = bpb(img)
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    out = []
    if B["fat32"]:
        root_raw = b"".join(cluster_bytes(img, B, c) for c in chain(img, B, B["root_cluster"]))
    else:
        root_raw = img[(B["rsv"] + B["nfats"] * B["spf"]) * B["bps"]:][:B["root_ents"] * 32]
    walk(img, B, lambda _p: root_raw, "/", out, 0)
    files = [o for o in out if o[0] == "F"]
    print(f"type={'FAT32' if B['fat32'] else 'FAT16/12'} dirs={sum(1 for o in out if o[0]=='D')} files={len(files)} total_bytes={sum(o[2] for o in files)}")
    for kind, path, size in out[:limit]:
        print(f"{kind} {size:>12} {path}")
