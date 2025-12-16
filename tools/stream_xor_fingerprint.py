#!/usr/bin/env python3
import sys
import math
from collections import Counter

def entropy(buf):
    if not buf:
        return 0.0
    counts = Counter(buf)
    total = len(buf)
    ent = 0.0
    for c in counts.values():
        p = c / total
        ent -= p * math.log2(p)
    return ent

def main():
    if len(sys.argv) != 3:
        print("usage: stream_xor_fingerprint.py <frame_a.bin> <frame_b.bin>")
        sys.exit(1)

    a = open(sys.argv[1], "rb").read()
    b = open(sys.argv[2], "rb").read()

    minlen = min(len(a), len(b))
    a = a[:minlen]
    b = b[:minlen]

    xor = bytes(x ^ y for x, y in zip(a, b))

    ent_a = entropy(a)
    ent_b = entropy(b)
    ent_x = entropy(xor)

    print(f"A len={len(a)} entropy={ent_a:.2f}")
    print(f"B len={len(b)} entropy={ent_b:.2f}")
    print(f"A xor B entropy={ent_x:.2f}")

    if ent_x < 5.0:
        print("LIKELY STREAM CIPHER / AEAD (keystream cancels)")
    else:
        print("LIKELY BLOCK / STRONG AEAD (structure destroyed)")

if __name__ == "__main__":
    main()
