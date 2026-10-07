"""Scan images for 32-bit little-endian literals (candidate MMIO base addresses).

Usage: python3 tools/literal_scan.py <img_dir> <out_json> <addr_hex> [<addr_hex> ...]
Hits are CANDIDATES only: a literal can be an unrelated constant. Confirm by xref in Ghidra.
"""
import json, os, struct, sys
img_dir, out_json, *addrs = sys.argv[1:]
addrs = [int(a, 16) for a in addrs]
results = {}
for name in sorted(os.listdir(img_dir)):
    if not name.endswith(".img") or name.startswith(("system", "product", "vendor.img", "odm", "bluetooth", "modem", "dsp")):
        continue  # firmware / boot-chain images only; skip the large Android filesystems
    data = open(os.path.join(img_dir, name), "rb").read()
    hits = {hex(a): data.count(struct.pack("<I", a)) for a in addrs}
    hits = {k: v for k, v in hits.items() if v}
    if hits: results[name] = hits
json.dump(results, open(out_json, "w"), indent=2)
for k, v in results.items(): print(f"{k:16s} {v}")
