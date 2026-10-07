"""Parse the hypervisor's peripheral mapping table (6 x u64 records, stride 0x30).

Usage: python3 tools/hyp_mmio_table.py <hyp.img> <table_vaddr_hex> <records>
Record layout observed in hyp.img at 0x9C010: [va, pa, attr, perm, 0, size].
Also used to read the TrustZone (tz.img) table, which is 16-byte (base, count) pairs.
"""
import struct, sys
from elftools.elf.elffile import ELFFile
path, start, n = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3])
data = open(path, "rb").read()
with open(path, "rb") as fh:
    segs = [(s["p_vaddr"], s["p_offset"], s["p_filesz"]) for s in ELFFile(fh).iter_segments()
            if s["p_type"] == "PT_LOAD" and s["p_filesz"] > 0]
def v2o(va):
    for v, o, z in segs:
        if v <= va < v + z: return o + (va - v)
print("va\tpa\tattr\tperm\tsize")
for i in range(n):
    base = start + i * 0x30
    q = struct.unpack_from("<6Q", data, v2o(base))
    print(f"{q[0]:#x}\t{q[1]:#x}\t{q[2]:#x}\t{q[3]:#x}\t{q[5]:#x}")
