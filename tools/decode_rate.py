"""Per-word decode rate for one ISA over a blob. Run one ISA per process (pypcode can crash otherwise).

Usage: python3 tools/decode_rate.py <file> <offset_hex> <size> <base_hex> <sleigh_lang>
"""
import sys, pypcode
path, off, size, base, lang = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3]), int(sys.argv[4], 16), sys.argv[5]
blob = open(path, "rb").read()[off:off + size]
ctx = pypcode.Context(lang)
ok = n = 0
for o in range(0, len(blob) - 4, 4):
    n += 1
    try:
        if ctx.disassemble(blob[o:o + 4], base + o).instructions: ok += 1
    except Exception:
        pass
print(f"{lang:24s} {path.split('/')[-1]:18s} off={off:#x} rate={ok/n:.3f} words={n}")
