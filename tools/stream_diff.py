#!/usr/bin/env python3
import sys
import struct
import re

# ------------------------------------------------------------
# Mask ranges
# message_index -> list of (start, end) ranges [inclusive]
# ------------------------------------------------------------
MASK_RANGES = {
    0: [(0, 5)],   # H01 variable header region (proven by diff)
}

def read_stream(path):
    with open(path, "rb") as f:
        data = f.read()

    # Detect hex-text dumps and convert to binary
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

        if length == 0:
            break

        if off + length > total:
            break

        payload = bytearray(data[off:off+length])
        msgs.append(payload)
        off += length

    return msgs

def apply_mask(payload, msg_index):
    if msg_index not in MASK_RANGES:
        return payload

    masked = bytearray(payload)
    for start, end in MASK_RANGES[msg_index]:
        for i in range(start, end + 1):
            if i < len(masked):
                masked[i] = 0x00
    return masked

def hexdump_slice(b, start, count=16):
    end = min(start + count, len(b))
    return " ".join(f"{x:02x}" for x in b[start:end])

def main():
    if len(sys.argv) != 3:
        print("usage: stream_diff.py <stream_a> <stream_b>")
        sys.exit(1)

    a = read_stream(sys.argv[1])
    b = read_stream(sys.argv[2])

    msgs_a = parse_messages(a)
    msgs_b = parse_messages(b)

    print(f"Stream A messages: {len(msgs_a)}")
    print(f"Stream B messages: {len(msgs_b)}")

    count = min(len(msgs_a), len(msgs_b))

    for i in range(count):
        pa = msgs_a[i]
        pb = msgs_b[i]

        ma = apply_mask(pa, i)
        mb = apply_mask(pb, i)

        if ma == mb:
            print(f"[OK] message {i} identical after masking (len={len(pa)})")
            continue

        print(f"[DIFF] message {i}")
        print(f"  A len={len(pa)} B len={len(pb)}")

        minlen = min(len(pa), len(pb))
        diff_off = None
        for j in range(minlen):
            if ma[j] != mb[j]:
                diff_off = j
                break

        if diff_off is not None:
            print(f"  first differing byte @ offset {diff_off}")
            print(f"  A: {hexdump_slice(pa, diff_off)}")
            print(f"  B: {hexdump_slice(pb, diff_off)}")
        else:
            print("  difference is length-only")

        break
    else:
        print("No differences found in compared message range")

if __name__ == "__main__":
    main()
