#!/usr/bin/env python3
import sys
import struct

MIN_LEN = 1
MAX_LEN = 4096  # conservative upper bound

def read_bin(path):
    with open(path, "rb") as f:
        return f.read()

def extract_frames(data):
    frames = []
    i = 0
    n = len(data)

    while i + 2 <= n:
        length = struct.unpack(">H", data[i:i+2])[0]

        if MIN_LEN <= length <= MAX_LEN and i + 2 + length <= n:
            payload = data[i+2:i+2+length]
            frames.append(payload)
            i += 2 + length
        else:
            # resync: advance by one byte and retry
            i += 1

    return frames

def main():
    if len(sys.argv) != 2:
        print("usage: stream_frames.py <stream.bin>")
        sys.exit(1)

    data = read_bin(sys.argv[1])
    frames = extract_frames(data)

    print(f"Total bytes: {len(data)}")
    print(f"Extracted frames: {len(frames)}")
    print("-" * 60)

    for i, f in enumerate(frames):
        print(f"frame[{i:02d}] len={len(f)}")

if __name__ == "__main__":
    main()
