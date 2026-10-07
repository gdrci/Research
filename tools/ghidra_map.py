"""Build ghidra/import_map.json from data/inventory.json: one entry per boot-chain ELF with
its load segments and a suggested Ghidra language (verify in your Ghidra version).

Usage: python3 tools/ghidra_map.py data/inventory.json ghidra/import_map.json
"""
import json, sys
# Suggested SLEIGH language IDs (Ghidra 11.x naming). XBL is UNRESOLVED on purpose; see docs/03.
LANG = {
    "EM_ARM": "ARM:LE:32:v8",
    "EM_AARCH64": "AARCH64:LE:64:v8A",
    "EM_RISCV": "RISCV:LE:32:RV32GC",
    "EM_QDSP6": "Hexagon:LE:32:default",
}
CHAIN = ["xbl", "xbl_config", "xbl_ramdump", "abl", "uefi", "uefisecapp", "tz", "hyp", "devcfg",
         "keymaster", "featenabler", "imagefv", "aop", "aop_config", "cpucp", "shrm", "qupfw",
         "multiimgqti", "multiimgoem"]
inv = json.load(open(sys.argv[1]))
out = []
for item in inv:
    name = item["image"][:-4]
    if "elf" not in item or name not in CHAIN: continue
    elf = item["elf"]
    loads = [s for s in elf["segments"] if s["type"] == "PT_LOAD" and s["memsz"] > 0]
    out.append({
        "image": item["image"], "sha256": item["sha256"], "elf_class": elf["class"],
        "machine": elf["machine"], "entry": hex(elf["entry"]),
        "suggested_language": LANG.get(elf["machine"], "UNRESOLVED"),
        "load_segments": [{"vaddr": hex(s["vaddr"]), "file_offset": hex(s["offset"]),
                           "filesz": hex(s["filesz"]), "memsz": hex(s["memsz"]),
                           "flags": s["flags"]} for s in loads],
    })
json.dump(out, open(sys.argv[2], "w"), indent=2)
print(f"{len(out)} chain images -> {sys.argv[2]}")
