#!/usr/bin/env python3
import sys
import struct
import re
import zlib
import math
from collections import Counter

ZLIB_HEADERS = (b"\x78\x01", b"\x78\x9c", b"\x78\xda")

def read_stream(path):
    with open(path, "rb") as f:
        data = f.read()

    try:
        text = data.decode("ascii")
        cleaned = re.sub(r"[^0-9a-fA-F]", "", text)
        if len(cleaned) >= len(text) * 0.6:
            return bytes.fromhex(cleaned)
    except UnicodeDecodeError:
        pass

    return data

def parse_messages(data):
    msgs = []
    off = 0
    total = len(data)

    while off + 2 <= total:
        length = struct.unpack(">H", data[off:off+2])[0]
        off += 2

        if length == 0 or off + length > total:
            break

        msgs.append(data[off:off+length])
        off += length

    return msgs

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

def is_zlib(buf):
    return len(buf) >= 2 and buf[:2] in ZLIB_HEADERS

def main():
    if len(sys.argv) != 2:
        print("usage: stream_compress.py <stream>")
        sys.exit(1)

    data = read_stream(sys.argv[1])
    msgs = parse_messages(data)

    print(f"Messages: {len(msgs)}")
    print("-" * 80)

    for i, m in enumerate(msgs):
        ent_before = entropy(m)

        print(f"msg[{i:02d}] len={len(m):4d} entropy={ent_before:5.2f}", end="")

        if is_zlib(m):
            try:
                decompressed = zlib.decompress(m)
                ent_after = entropy(decompressed)
                print(
                    f" ZLIB "
                    f"decompressed_len={len(decompressed)} "
                    f"entropy_after={ent_after:5.2f}"
                )
            except Exception as e:
                print(" ZLIB (decompression failed)")
        else:
            print("")

if __name__ == "__main__":
    main()
