#!/usr/bin/env python3
"""Restore the complete, exact ARCHIUM 5.3.2 standalone HTML from Git objects."""
import hashlib
from pathlib import Path
root = Path(__file__).resolve().parent
parts = sorted((root / "chunks").glob("part-*.txt"))
if len(parts) != 11:
    raise SystemExit(f"Expected 11 chunks, found {len(parts)}")
data = b"".join(p.read_bytes() for p in parts)
actual = hashlib.sha256(data).hexdigest()
expected = "425af8dc18e02a89d137920b24d76d98be2920526e2289677d9e74f0d9aa5cdb"
if actual != expected:
    raise SystemExit(f"Checksum mismatch: {actual} != {expected}")
out = root / "ARCHIUM_5_3_2_IPHONE_BUTTON_FIX_FULL.html"
out.write_bytes(data)
print(f"Restored {out} ({len(data)} bytes, SHA256 {actual})")
