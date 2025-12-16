#!/usr/bin/env python3
import sys
import struct
import re

# ------------------------------------------------------------
# Existing mask ranges (manually confirmed)
# ------------------------------------------------------------
MASK_RANGES = {
    0: [(0, 7)],     # H01
    2: [(0, 31)],    # Client msg 2 (partial header)
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

def diff_ranges(a, b):
    ranges = []
    i = 0
    n = min(len(a), len(b))
    while i < n:
        if a[i] != b[i]:
            start = i
            while i < n and a[i] != b[i]:
                i += 1
            ranges.append((start, i - 1))
        else:
            i += 1
    if len(a) != len(b):
        ranges.append((n, max(len(a), len(b)) - 1))
    return ranges

def hexdump_slice(b, start, count=16):
    end = min(start + count, len(b))
    return " ".join(f"{x:02x}" for x in b[start:end])

def try_resync(msgs_a, msgs_b, ia, ib):
    for da in range(1, RESYNC_WINDOW + 1):
        for db in range(1, RESYNC_WINDOW + 1):
            na = ia + da
            nb = ib + db
            if na < len(msgs_a) and nb < len(msgs_b):
                if len(msgs_a[na]) == len(msgs_b[nb]):
                    return na, nb
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
    oks = diffs = 0
    suggested = {}

    while ia < len(msgs_a) and ib < len(msgs_b):
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

        print(f"[DIFF] A[{ia}] vs B[{ib}]")
        print(f"  A len={len(pa)} B len={len(pb)}")

        ranges = diff_ranges(ma, mb)
        for start, end in ranges:
            print(f"  diff range {start}-{end}")
            print(f"    A: {hexdump_slice(pa, start)}")
            print(f"    B: {hexdump_slice(pb, start)}")
            suggested.setdefault(ia, []).append((start, end))

        diffs += 1
        ia, ib = try_resync(msgs_a, msgs_b, ia, ib)

    print("--------------------------------------------------")
    print(f"OK: {oks}")
    print(f"DIFF: {diffs}")
    print("--------------------------------------------------")
    print("SUGGESTED MASK_RANGES (copy/paste):")
    print("{")
    for msg, ranges in sorted(suggested.items()):
        print(f"  {msg}: {ranges},")
    print("}")

if __name__ == "__main__":
    main()
