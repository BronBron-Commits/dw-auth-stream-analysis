#!/usr/bin/env python3
import sys
import re

def main():
    if len(sys.argv) != 3:
        print("usage: stream_normalize.py <input_hex.txt> <output.bin>")
        sys.exit(1)

    with open(sys.argv[1], "r", errors="ignore") as f:
        text = f.read()

    # Strip everything except hex digits
    cleaned = re.sub(r"[^0-9a-fA-F]", "", text)

    if len(cleaned) % 2 != 0:
        print("Error: odd number of hex digits after cleaning")
        sys.exit(1)

    data = bytes.fromhex(cleaned)

    with open(sys.argv[2], "wb") as f:
        f.write(data)

    print(f"Wrote {len(data)} bytes to {sys.argv[2]}")

if __name__ == "__main__":
    main()
