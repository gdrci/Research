"""Verify AVB vbmeta signatures and recompute hash / dm-verity root digests from images.

Usage: python3 tools/avb_verify.py <img_dir> <vbmeta.img> [<vbmeta_system.img> ...]
Needs: pip install cryptography
Checks:
  1. The vbmeta RSA signature (PKCS#1 v1.5, SHA-256) over header + auxiliary block.
  2. The vbmeta authentication hash over the same data.
  3. Hash descriptors: SHA of the first image_size bytes of the named partition.
  4. Hashtree descriptors: recomputed dm-verity root digest (v1 layout, salt prepended).
"""
import hashlib, os, struct, sys
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

def u32(b, o): return struct.unpack_from(">I", b, o)[0]
def u64(b, o): return struct.unpack_from(">Q", b, o)[0]

def parse_pubkey(pk):
    bits = struct.unpack_from(">I", pk, 0)[0]
    n = int.from_bytes(pk[8:8 + bits // 8], "big")
    return rsa.RSAPublicNumbers(65537, n).public_key()

def descriptors(b, aux, desc_off, desc_sz):
    o, end = aux + desc_off, aux + desc_off + desc_sz
    while o < end:
        tag, nb = u64(b, o), u64(b, o + 8)
        yield tag, b[o + 16:o + 16 + nb]
        o = (o + 16 + nb + 7) & ~7

def dm_verity_root(path, data_size, block, salt, alg):
    h = hashlib.new(alg)
    nblocks = (data_size + block - 1) // block
    digests = []
    with open(path, "rb") as f:
        for _ in range(nblocks):
            chunk = f.read(block)
            chunk = chunk + b"\0" * (block - len(chunk))
            digests.append(hashlib.new(alg, salt + chunk).digest())
    per = block // len(digests[0])
    level = digests
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), per):
            blk = b"".join(level[i:i + per]).ljust(block, b"\0")
            nxt.append(hashlib.new(alg, salt + blk).digest())
        level = nxt
    return level[0]

def verify_vbmeta(img_dir, path):
    b = open(path, "rb").read()
    auth_sz, aux_sz = u64(b, 12), u64(b, 20)
    alg = u32(b, 28)
    h_off, h_sz = u64(b, 32), u64(b, 40)
    s_off, s_sz = u64(b, 48), u64(b, 56)
    pk_off, pk_sz = u64(b, 64), u64(b, 72)
    aux = 256 + auth_sz
    signed = b[0:256] + b[aux:aux + aux_sz]
    digest = hashlib.sha256(signed).digest()
    stored = b[256 + h_off:256 + h_off + h_sz]
    pub = parse_pubkey(b[aux + pk_off:aux + pk_off + pk_sz])
    print(f"== {os.path.basename(path)}")
    print(f"   authentication hash matches signed data: {stored == digest}")
    try:
        pub.verify(b[256 + s_off:256 + s_off + s_sz], signed, padding.PKCS1v15(), hashes.SHA256())
        print("   RSA signature: VALID")
    except Exception as e:
        print(f"   RSA signature: INVALID ({type(e).__name__})")
    print(f"   public key sha256: {hashlib.sha256(b[aux + pk_off:aux + pk_off + pk_sz]).hexdigest()}")
    for tag, d in descriptors(b, aux, u64(b, 96), u64(b, 104)):
        if tag == 2:  # hash descriptor
            size = u64(d, 0); halg = d[8:40].split(b"\0")[0].decode()
            nlen, slen, dlen = u32(d, 40), u32(d, 44), u32(d, 48)
            name = d[116:116 + nlen].decode()
            salt = d[116 + nlen:116 + nlen + slen]
            want = d[116 + nlen + slen:116 + nlen + slen + dlen]
            img = os.path.join(img_dir, name + ".img")
            if not os.path.exists(img):
                print(f"   hash {name}: image missing"); continue
            hh = hashlib.new(halg, salt + open(img, "rb").read()[:size]).digest()
            print(f"   hash {name}: {'OK' if hh == want else 'MISMATCH'} ({size} bytes, {halg})")
        elif tag == 1:  # hashtree descriptor
            size = u64(d, 4); halg = d[56:88].split(b"\0")[0].decode()
            block = u32(d, 28); hblock = u32(d, 32)
            nlen, slen, dlen = u32(d, 88), u32(d, 92), u32(d, 96)
            name = d[164:164 + nlen].decode()
            salt = d[164 + nlen:164 + nlen + slen]
            want = d[164 + nlen + slen:164 + nlen + slen + dlen]
            img = os.path.join(img_dir, name + ".img")
            if not os.path.exists(img):
                print(f"   hashtree {name}: image missing"); continue
            print(f"   hashtree {name}: computing ({size} bytes, {halg}) ...", flush=True)
            got = dm_verity_root(img, size, block, salt, halg)
            print(f"   hashtree {name}: {'OK' if got == want else 'MISMATCH'} (root {got.hex()[:16]}..)")

if __name__ == "__main__":
    img_dir, *vbs = sys.argv[1:]
    for v in vbs:
        verify_vbmeta(img_dir, v)
