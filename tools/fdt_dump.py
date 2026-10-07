"""Minimal flattened-device-tree (DTB) dumper: prints node paths and properties.

Usage: python3 tools/fdt_dump.py <file.dtb> [name_filter_substring]
Only needs the standard library.
"""
import struct, sys

def parse(blob):
    magic, total, off_struct, off_strings, off_rsv, version, last_comp, boot_cpu, size_strings, size_struct = struct.unpack_from(">10I", blob, 0)
    assert magic == 0xD00DFEED, "not a DTB"
    strings = blob[off_strings:off_strings + size_strings]
    def cstr(o):
        return strings[o:strings.index(b"\0", o)].decode(errors="replace")
    out = []  # (path, {prop: bytes})
    path = []; props = None; o = off_struct; cur = None
    while True:
        tok = struct.unpack_from(">I", blob, o); o += 4
        t = tok[0]
        if t == 1:  # BEGIN_NODE
            name = blob[o:blob.index(b"\0", o)].decode(errors="replace"); o = (o + len(name) + 1 + 3) & ~3
            path.append(name); cur = (("/" + "/".join(p for p in path if p)) or "/", {}); out.append(cur)
        elif t == 2:  # END_NODE
            path.pop()
        elif t == 3:  # PROP
            ln, nameoff = struct.unpack_from(">II", blob, o); o += 8
            val = blob[o:o + ln]; o = (o + ln + 3) & ~3
            cur[1][cstr(nameoff)] = val
        elif t == 4:  # NOP
            continue
        elif t == 9:  # END
            break
        else:
            raise ValueError(f"bad token {t} at {o-4}")
    return out

def fmt(v):
    if v == b"": return "<empty>"
    if all(32 <= c < 127 or c == 0 for c in v) and v.endswith(b"\0"):
        return '"' + v.rstrip(b"\0").decode(errors="replace") + '"'
    if len(v) % 4 == 0:
        return "<" + " ".join(f"0x{x:x}" for x in struct.unpack(f">{len(v)//4}I", v)) + ">"
    return v.hex()

if __name__ == "__main__":
    blob = open(sys.argv[1], "rb").read()
    flt = sys.argv[2] if len(sys.argv) > 2 else ""
    for path, props in parse(blob):
        if flt and flt not in path: continue
        print(path)
        for k, v in props.items():
            print(f"    {k} = {fmt(v)}")
