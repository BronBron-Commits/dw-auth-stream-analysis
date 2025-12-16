#!/usr/bin/env python3
import sys
import struct
import os

MIN_LEN = 1
MAX_LEN = 4096

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
            i += 1

    return frames

def main():
    if len(sys.argv) != 3:
        print("usage: stream_extract_frames.py <stream.bin> <out_dir>")
        sys.exit(1)

    data = open(sys.argv[1], "rb").read()
    out_dir = sys.argv[2]

    os.makedirs(out_dir, exist_ok=True)

    frames = extract_frames(data)

    for i, f in enumerate(frames):
        path = os.path.join(out_dir, f"frame_{i:02d}.bin")
        with open(path, "wb") as out:
            out.write(f)
        print(f"Wrote {path} ({len(f)} bytes)")

    print(f"Total frames: {len(frames)}")

if __name__ == "__main__":
    main()
