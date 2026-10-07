"""Build data/inventory.json: hashes, sizes and container type for every extracted image.

Usage: python3 tools/inventory.py <img_dir> <out_json>
"""
import hashlib, json, os, struct, sys
from elftools.elf.elffile import ELFFile

MACHINE_NAMES = {"EM_M32": "EM_M32 (1; odd for XBL, see docs/03)"}

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def elf_info(path):
    with open(path, "rb") as f:
        try:
            e = ELFFile(f)
        except Exception:
            return None
        machine = e["e_machine"]  # pyelftools returns the name string, e.g. 'EM_ARM'
        machine = MACHINE_NAMES.get(machine, machine)
        segs = []
        for s in e.iter_segments():
            h = s.header
            segs.append({"type": h.p_type, "vaddr": h.p_vaddr, "offset": h.p_offset,
                         "filesz": h.p_filesz, "memsz": h.p_memsz,
                         "flags": h.p_flags})
        return {"class": e.elfclass, "machine": machine, "entry": e["e_entry"],
                "segments": segs}

def classify(path):
    with open(path, "rb") as f:
        head = f.read(8)
    if head[:4] == b"AVB0": return "avb-vbmeta"
    if head == b"ANDROID!": return "android-boot"
    if head == b"VNDRBOOT": return "android-vendor-boot"
    if head[:4] == b"\x7fELF": return "elf"
    if head[:4] == b"\xd7\xb7\xab\x1e": return "dtbo"
    return "other"

def main(img_dir, out_json):
    items = []
    for name in sorted(os.listdir(img_dir)):
        p = os.path.join(img_dir, name)
        if not name.endswith(".img") or not os.path.isfile(p): continue  # payload partitions only
        kind = classify(p)
        item = {"image": name, "bytes": os.path.getsize(p), "sha256": sha256(p), "kind": kind}
        if kind == "elf":
            info = elf_info(p)
            if info: item["elf"] = info
        items.append(item)
    with open(out_json, "w") as f:
        json.dump(items, f, indent=2)
    print(f"wrote {len(items)} entries -> {out_json}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
