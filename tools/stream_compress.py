#!/usr/bin/env python3
import sys
import zlib
import math
from collections import Counter

ZLIB_HEADERS = (b"\x78\x01", b"\x78\x9c", b"\x78\xda")

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

def classify(ent):
    if ent < 2.0:
        return "STRUCTURED"
    elif ent < 5.0:
        return "COMPRESSED"
    elif ent < 7.2:
        return "HIGH-ENTROPY"
    else:
        return "ENCRYPTED / RANDOM"

def main():
    if len(sys.argv) != 2:
        print("usage: stream_compress.py <frame.bin>")
        sys.exit(1)

    path = sys.argv[1]
    data = open(path, "rb").read()

    ent_before = entropy(data)
    print(f"{path}")
    print("-" * 80)
    print(f"len={len(data)} entropy={ent_before:.2f} {classify(ent_before)}")

    if len(data) >= 2 and data[:2] in ZLIB_HEADERS:
        try:
            decompressed = zlib.decompress(data)
            ent_after = entropy(decompressed)
            out_path = path + ".zlib.dec"

            with open(out_path, "wb") as f:
                f.write(decompressed)

            print("ZLIB detected")
            print(f"decompressed_len={len(decompressed)}")
            print(f"entropy_after={ent_after:.2f} {classify(ent_after)}")
            print(f"wrote {out_path}")
        except Exception as e:
            print("ZLIB header detected but decompression failed")
    else:
        print("no zlib header detected")

if __name__ == "__main__":
    main()
