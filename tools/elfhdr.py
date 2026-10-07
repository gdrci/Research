import sys, struct
from elftools.elf.elffile import ELFFile
for path in sys.argv[1:]:
    with open(path,'rb') as fh:
        try:
            e = ELFFile(fh)
        except Exception as ex:
            print(path, 'not ELF', ex); continue
        print(f"== {path}: class={e.elfclass} machine={e['e_machine']} entry={hex(e['e_entry'])} phnum={e.num_segments()}")
        for seg in e.iter_segments():
            h = seg.header
            print(f"   PH type={h.p_type:<14} off={hex(h.p_offset):<10} vaddr={hex(h.p_vaddr):<12} filesz={hex(h.p_filesz):<10} memsz={hex(h.p_memsz):<10} flags={h.p_flags:#x}")
