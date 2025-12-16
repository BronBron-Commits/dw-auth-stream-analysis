#!/usr/bin/env python3
import sys
import struct
import math
import re
from collections import Counter

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
    if len(sys.argv) < 2:
        print("usage: stream_entropy.py <stream1> [stream2 ...]")
        sys.exit(1)

    streams = []
    for path in sys.argv[1:]:
        data = read_stream(path)
        msgs = parse_messages(data)
        streams.append((path, msgs))

    max_msgs = max(len(m) for _, m in streams)

    print("Entropy by message index")
    print("-" * 80)

    for i in range(max_msgs):
        print(f"msg[{i:02d}]")
        for path, msgs in streams:
            if i >= len(msgs):
                print(f"  {path:<15} <missing>")
                continue

            e = entropy(msgs[i])
            print(
                f"  {path:<15} len={len(msgs[i]):4d} "
                f"entropy={e:5.2f} {classify(e)}"
            )
        print()

if __name__ == "__main__":
    main()
