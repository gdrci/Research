"""Minimal AVB 1.x vbmeta parser (layout per libavb avb_vbmeta_image.h / avb_descriptor.h).
Usage: python3 tools/avb_dump.py vbmeta.img [vbmeta_system.img ...]
"""

import sys, struct
ALG = {0:"NONE",1:"SHA256_RSA2048",2:"SHA256_RSA4096",3:"SHA256_RSA8192",4:"SHA512_RSA2048",5:"SHA512_RSA4096",6:"SHA512_RSA8192"}
TAGS = {0:"property",1:"hashtree",2:"hash",3:"kernel_cmdline",4:"chain_partition"}
def u32(b,o): return struct.unpack_from(">I",b,o)[0]
def u64(b,o): return struct.unpack_from(">Q",b,o)[0]
def dump(path):
    b = open(path,'rb').read()
    if b[:4] != b"AVB0":
        print(f"{path}: not a vbmeta image (magic {b[:4]!r})"); return
    maj,mnr = u32(b,4),u32(b,8)
    auth_sz,aux_sz = u64(b,12),u64(b,20)
    alg = u32(b,28)
    pk_off,pk_sz = u64(b,64),u64(b,72)
    desc_off,desc_sz = u64(b,96),u64(b,104)
    rb = u64(b,112); flags = u32(b,120); rb_loc = u32(b,124)
    rel = b[128:176].split(b"\0")[0].decode(errors="replace")
    pk = b[256+auth_sz+pk_off : 256+auth_sz+pk_off+pk_sz]
    import hashlib
    print(f"== {path}")
    print(f"   public key sha256 = {hashlib.sha256(pk).hexdigest()}")
    print(f"   libavb {maj}.{mnr}  release='{rel}'  algorithm={ALG.get(alg,alg)}  rollback_index={rb} (location {rb_loc})  flags={flags:#x}  pubkey_bytes={pk_sz}")
    aux = 256 + auth_sz
    o, end = aux + desc_off, aux + desc_off + desc_sz
    while o < end:
        tag, nb = u64(b,o), u64(b,o+8)
        d = b[o+16:o+16+nb]
        name = TAGS.get(tag, f"tag{tag}")
        if tag == 2:  # hash descriptor (body fields after 16-byte header)
            img_size = u64(d,0); halg = d[8:40].split(b"\0")[0].decode()
            nlen = u32(d,40); slen = u32(d,44); dlen = u32(d,48)
            pname = d[116:116+nlen].decode(errors="replace")
            print(f"   [hash] partition={pname!r} size={img_size} alg={halg} digest_len={dlen}")
        elif tag == 1:  # hashtree descriptor
            dv_ver = u32(d,0); img_size = u64(d,4)
            halg = d[56:88].split(b"\0")[0].decode()
            nlen = u32(d,88)
            pname = d[164:164+nlen].decode(errors="replace")
            print(f"   [hashtree] partition={pname!r} size={img_size} alg={halg} dm_verity_ver={dv_ver}")
        elif tag == 4:  # chain partition
            rbi = u32(d,0); nlen = u32(d,4); pklen = u32(d,8)
            pname = d[76:76+nlen].decode(errors="replace")
            print(f"   [chain] partition={pname!r} rollback_loc={rbi} pubkey_bytes={pklen}")
        elif tag == 3:
            print(f"   [cmdline] {d.decode(errors='replace')[:160]!r}")
        elif tag == 0:
            kl = u64(d,0); vl = u64(d,8)
            key = d[16:16+kl].decode(errors="replace"); val = d[16+kl+1:16+kl+1+vl].decode(errors="replace")
            print(f"   [property] {key} = {val[:120]}")
        else:
            print(f"   [{name}] len={nb}")
        o += 16 + nb
        o = (o + 7) & ~7
for p in sys.argv[1:]:
    dump(p)
