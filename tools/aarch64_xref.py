"""Find AArch64 code that loads a 32-bit constant: LDR (literal) and MOVZ/MOVK pairs.

Usage: python3 tools/aarch64_xref.py <elf> <hex_value>
Reads PT_LOAD segments from the ELF to map file offsets to virtual addresses.
Needs: pip install pyelftools
"""
import struct, sys
from elftools.elf.elffile import ELFFile

path, target = sys.argv[1], int(sys.argv[2], 16)
data = open(path, "rb").read()
with open(path, "rb") as fh:
    elf = ELFFile(fh)
    segs = [(s["p_vaddr"], s["p_offset"], s["p_filesz"], s["p_flags"]) for s in elf.iter_segments()
            if s["p_type"] == "PT_LOAD" and s["p_filesz"] > 0]
    loads = [(v, o, z) for v, o, z, f in segs if f & 1]        # executable segments: code
    allloads = [(v, o, z) for v, o, z, f in segs]               # all segments: data too

def v2o(va):
    for vaddr, off, sz in loads:
        if vaddr <= va < vaddr + sz:
            return off + (va - vaddr)
    return None

def o2v(off):
    for vaddr, o, sz in allloads:
        if o <= off < o + sz:
            return vaddr + (off - o)
    return None

# 1) literal pool entries holding the constant
pool = [o for o in range(0, len(data) - 3, 4) if struct.unpack_from("<I", data, o)[0] == target]
pool_va = {o2v(o): o for o in pool if o2v(o) is not None}
print(f"literal pool entries for {target:#x}: {[hex(v) for v in pool_va]}")

hits = []
# 2) LDR (literal), 32-bit (0x18000000) and 64-bit (0x58000000)
for vaddr, off, sz in loads:
    for o in range(off, off + sz - 3, 4):
        w = struct.unpack_from("<I", data, o)[0]
        if (w & 0x3B000000) == 0x18000000:          # LDR literal (w or x)
            imm19 = (w >> 5) & 0x7FFFF
            if imm19 & 0x40000: imm19 -= 0x80000
            ia = o2v(o)
            if ia is None: continue
            tgt = ia + imm19 * 4
            if tgt in pool_va:
                hits.append((ia, "LDR literal", f"pool @ {tgt:#x}"))
        # 3) MOVZ/MOVK pair building the constant: check MOVK (hw=1) for the high half
        if (w & 0x7F800000) == 0x72800000 or (w & 0x7F800000) == 0x72A00000:
            pass
# MOVK with hw=1 (lsl 16) and imm16 = high half, optional MOVZ with low half nearby
hi, lo = (target >> 16) & 0xFFFF, target & 0xFFFF
for vaddr, off, sz in loads:
    for o in range(off, off + sz - 3, 4):
        w = struct.unpack_from("<I", data, o)[0]
        if (w & 0xFFE00000) in (0x72A00000, 0xF2A00000) and ((w >> 5) & 0xFFFF) == hi:
            ia = o2v(o)
            for d in range(-16, 17, 4):
                if d == 0: continue
                p = o + d
                if off <= p < off + sz - 3:
                    w2 = struct.unpack_from("<I", data, p)[0]
                    if (w2 & 0xFFE00000) in (0x52800000, 0xD2800000) and ((w2 >> 5) & 0xFFFF) == lo:
                        hits.append((ia, "MOVZ/MOVK pair", f"low @ {o2v(p):#x}"))
                        break
# 4) ADRP + LDR/ADD pair: ADRP Xn, page; then LDR Xt/Wt,[Xn,#off] (or ADD Xn,Xn,#off) with off == slot & 0xFFF
slot_offs = {slot & 0xFFF: slot for slot in pool_va}
for vaddr, off, sz in loads:
    for o in range(off, off + sz - 3, 4):
        w = struct.unpack_from("<I", data, o)[0]
        if (w & 0x9F000000) != 0x90000000: continue           # ADRP
        rd = w & 0x1F
        ia = o2v(o)
        imm = (((w >> 5) & 0x7FFFF) << 2 | ((w >> 29) & 3))
        if imm & 0x100000: imm -= 0x200000
        page = (ia & ~0xFFF) + (imm << 12)
        for k in range(1, 7):
            p2 = o + 4 * k
            if p2 >= off + sz - 3: break
            w2 = struct.unpack_from("<I", data, p2)[0]
            # LDR (unsigned imm), 64-bit 0xF9400000 / 32-bit 0xB9400000
            if (w2 & 0xFFC00000) in (0xF9400000, 0xB9400000):
                scale = 8 if (w2 & 0xFFC00000) == 0xF9400000 else 4
                base = (w2 >> 5) & 0x1F
                ofs = ((w2 >> 10) & 0xFFF) * scale
            elif (w2 & 0xFFC00000) == 0x91000000:             # ADD Xd, Xn, #imm
                base = (w2 >> 5) & 0x1F
                ofs = (w2 >> 10) & 0xFFF
            else:
                continue
            if base != rd: break
            addr = page + ofs
            if addr in pool_va:
                hits.append((ia, "ADRP+LDR/ADD", f"slot {addr:#x} via x{rd} at +{k*4}"))
                break
print(f"code references: {len(hits)}")
for ia, kind, note in hits:
    print(f"  {ia:#x}  {kind}  {note}")
