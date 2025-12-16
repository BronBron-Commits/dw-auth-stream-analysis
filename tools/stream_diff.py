#!/usr/bin/env python3
import sys
import struct
import re

# ------------------------------------------------------------
# Mask ranges
# message_index -> list of (start, end) ranges [inclusive]
# ------------------------------------------------------------
MASK_RANGES = {
    0: [(0, 7)],      # H01
    2: [(0, 31)],     # Client msg 2 variable header (expanded)
}

RESYNC_WINDOW = 6

def read_stream(path):
    with open(path, "rb") as f:
        data = f.read()
    try:
        return data.decode("ascii")
    except UnicodeDecodeError:
        return data

def parse_length_prefixed(data: bytes):
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

def parse_hex_lines(text: str):
    msgs = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msgs.append(bytearray(bytes.fromhex(line)))
        except ValueError:
            pass
    return msgs

def parse_messages(raw):
    if isinstance(raw, (bytes, bytearray)):
        msgs = parse_length_prefixed(raw)
        if msgs:
            return msgs
        return []

    if isinstance(raw, str):
        try:
            collapsed = re.sub(r"[^0-9a-fA-F]", "", raw)
            if collapsed:
                binary = bytes.fromhex(collapsed)
                msgs = parse_length_prefixed(binary)
                if len(msgs) > 1:
                    return msgs
        except ValueError:
            pass
        return parse_hex_lines(raw)

    return []

def apply_mask(payload, msg_index):
    if msg_index not in MASK_RANGES:
        return payload
    masked = bytearray(payload)
    for start, end in MASK_RANGES[msg_index]:
        for i in range(start, end + 1):
            if i < len(masked):
                masked[i] = 0x00
    return masked

def first_diff_offset(a, b):
    minlen = min(len(a), len(b))
    for i in range(minlen):
        if a[i] != b[i]:
            return i
    if len(a) != len(b):
        return minlen
    return None

def hexdump_slice(b, start, count=16):
    end = min(start + count, len(b))
    return " ".join(f"{x:02x}" for x in b[start:end])

def try_resync(msgs_a, msgs_b, ia, ib):
    # Try to find a forward alignment based on equal length
    for da in range(1, RESYNC_WINDOW + 1):
        for db in range(1, RESYNC_WINDOW + 1):
            na = ia + da
            nb = ib + db
            if na < len(msgs_a) and nb < len(msgs_b):
                if len(msgs_a[na]) == len(msgs_b[nb]):
                    return na, nb

    # Fallback: force progress (never stay on same pair)
    return ia + 1, ib + 1

def main():
    if len(sys.argv) != 3:
        print("usage: stream_diff.py <stream_a> <stream_b>")
        sys.exit(1)

    msgs_a = parse_messages(read_stream(sys.argv[1]))
    msgs_b = parse_messages(read_stream(sys.argv[2]))

    print(f"Stream A messages: {len(msgs_a)}")
    print(f"Stream B messages: {len(msgs_b)}")

    ia = ib = 0
    diffs = oks = 0
    seen = set()

    while ia < len(msgs_a) and ib < len(msgs_b):
        if (ia, ib) in seen:
            ia += 1
            ib += 1
            continue
        seen.add((ia, ib))

        pa = msgs_a[ia]
        pb = msgs_b[ib]

        ma = apply_mask(pa, ia)
        mb = apply_mask(pb, ib)

        if ma == mb:
            print(f"[OK] A[{ia}] == B[{ib}] (len={len(pa)})")
            oks += 1
            ia += 1
            ib += 1
            continue

        off = first_diff_offset(ma, mb)
        print(f"[DIFF] A[{ia}] vs B[{ib}]")
        print(f"  A len={len(pa)} B len={len(pb)}")
        if off is not None:
            print(f"  first differing byte @ offset {off}")
            print(f"  A: {hexdump_slice(pa, off)}")
            print(f"  B: {hexdump_slice(pb, off)}")

        diffs += 1
        ia, ib = try_resync(msgs_a, msgs_b, ia, ib)

    print("--------------------------------------------------")
    print(f"OK: {oks}")
    print(f"DIFF: {diffs}")
    print(f"Remaining A: {len(msgs_a) - ia}")
    print(f"Remaining B: {len(msgs_b) - ib}")

if __name__ == "__main__":
    main()
