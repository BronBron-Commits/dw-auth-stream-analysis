#!/usr/bin/env python3
import sys
import struct
import re

# ------------------------------------------------------------
# Canonical mask ranges (session-variant regions)
# Derived mechanically from multi-stream diffs
# ------------------------------------------------------------
MASK_RANGES = {
    0: [(0, 7)],

    2: [(32, 66), (68, 169), (171, 397)],
    5: [(14, 195), (197, 397)],
    6: [(0, 56), (57, 129)],
    7: [(0, 149), (150, 314)],
    8: [(0, 122), (123, 238)],
    9: [(0, 20), (21, 313)],
    10: [(0, 215), (216, 319)],
}

PHASE_1_LAST_MSG = 1  # deterministic handshake
PHASE_2_FIRST_MSG = 2  # negotiated / session-bound

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

        msgs.append(bytearray(data[off:off+length]))
        off += length

    return msgs

def apply_mask(payload, msg_index):
    if msg_index not in MASK_RANGES:
        return payload

    out = bytearray(payload)
    for start, end in MASK_RANGES[msg_index]:
        for i in range(start, end + 1):
            if i < len(out):
                out[i] = 0x00
    return out

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
    ok = diff = 0

    for i in range(count):
        pa, pb = msgs_a[i], msgs_b[i]
        ma, mb = apply_mask(pa, i), apply_mask(pb, i)

        if ma == mb:
            print(f"[OK] A[{i}] == B[{i}] (len={len(pa)})")
            ok += 1
            continue

        diff += 1
        print(f"[DIFF] A[{i}] vs B[{i}]")
        print(f"  A len={len(pa)} B len={len(pb)}")

        minlen = min(len(pa), len(pb))
        first = None
        for j in range(minlen):
            if ma[j] != mb[j]:
                first = j
                break

        if first is not None:
            print(f"  first differing byte @ offset {first}")
            print(f"  A: {hexdump_slice(pa, first)}")
            print(f"  B: {hexdump_slice(pb, first)}")
        else:
            print("  difference is length-only")

    print("-" * 50)
    print(f"OK: {ok}")
    print(f"DIFF: {diff}")
    print(f"Remaining A: {len(msgs_a) - count}")
    print(f"Remaining B: {len(msgs_b) - count}")
    print()
    print("Protocol Phases:")
    print(f"  Phase 1 (deterministic): messages 0–{PHASE_1_LAST_MSG}")
    print(f"  Phase 2 (session-bound): messages {PHASE_2_FIRST_MSG}+")
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
