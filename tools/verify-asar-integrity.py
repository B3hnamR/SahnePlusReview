#!/usr/bin/env python3
"""
Verify the ASAR integrity record embedded in an Electron executable against the
actual application archive.

Electron stores this record as a PE resource:

    INTEGRITY > ELECTRONASAR > #1033

containing UTF-8 JSON:

    [{"file":"resources\\app.asar","alg":"SHA256","value":"<hex>"}]

The validated scope is the ASAR header JSON, which begins at offset 16 in the
archive (after a 4-field little-endian header). Hashing the whole file will
report a mismatch -- that is expected and is not a discrepancy.

Usage:
    python verify-asar-integrity.py <electron.exe> <path/to/app.asar>

Example:
    python verify-asar-integrity.py "Sahne Plus.exe" resources/app.asar

Exit codes:
    0  record found and hash matches
    1  record found but hash differs
    2  no integrity record found, or the archive could not be parsed
"""

import hashlib
import json
import os
import struct
import sys


def read_pe_resource(exe_path, want_type="INTEGRITY", want_name="ELECTRONASAR"):
    """Walk the PE resource directory and return the first matching data blob."""
    d = open(exe_path, "rb").read()

    pe = struct.unpack_from("<I", d, 0x3C)[0]
    if d[pe:pe + 4] != b"PE\x00\x00":
        raise ValueError("not a PE file")

    n_sections = struct.unpack_from("<H", d, pe + 6)[0]
    opt_size = struct.unpack_from("<H", d, pe + 20)[0]
    opt = pe + 24
    magic = struct.unpack_from("<H", d, opt)[0]

    # data directory offset differs between PE32 and PE32+
    dd = opt + (112 if magic == 0x20B else 96)
    rsrc_rva, _rsrc_size = struct.unpack_from("<II", d, dd + 2 * 8)

    sections = []
    for i in range(n_sections):
        o = opt + opt_size + i * 40
        vsize, va, raw_size, raw_ptr = struct.unpack_from("<IIII", d, o + 8)
        sections.append((va, vsize, raw_ptr, raw_size))

    def rva_to_off(rva):
        for va, vsize, raw_ptr, raw_size in sections:
            if va <= rva < va + max(vsize, raw_size):
                return raw_ptr + (rva - va)
        return None

    base = rva_to_off(rsrc_rva)
    if base is None:
        return None

    found = []

    def label_of(entry_off, nameval):
        if nameval & 0x80000000:
            no = base + (nameval & 0x7FFFFFFF)
            length = struct.unpack_from("<H", d, no)[0]
            return d[no + 2:no + 2 + length * 2].decode("utf-16-le")
        return "#%d" % nameval

    def walk(off, path):
        n_named, n_id = struct.unpack_from("<HH", d, off + 12)
        for i in range(n_named + n_id):
            e = off + 16 + i * 8
            nameval, = struct.unpack_from("<I", d, e)
            sub, = struct.unpack_from("<I", d, e + 4)
            label = label_of(e, nameval)
            if sub & 0x80000000:
                walk(base + (sub & 0x7FFFFFFF), path + [label])
            else:
                de = base + sub
                data_rva, data_size, _cp, _res = struct.unpack_from("<IIII", d, de)
                doff = rva_to_off(data_rva)
                if doff is None:
                    continue
                found.append((" > ".join(path + [label]), d[doff:doff + data_size]))

    walk(base, [])

    for name, blob in found:
        parts = [p.upper() for p in name.split(" > ")]
        if want_type.upper() in parts and want_name.upper() in parts:
            return blob
    return None


def asar_header_hash(asar_path):
    """SHA-256 of the ASAR header JSON (the scope Electron validates)."""
    a = open(asar_path, "rb").read()
    if len(a) < 16:
        raise ValueError("file too small to be an ASAR archive")

    header_size, json_size = struct.unpack_from("<II", a, 4)[:2]
    json_size = struct.unpack_from("<I", a, 12)[0]
    header_json = a[16:16 + json_size]

    return hashlib.sha256(header_json).hexdigest(), len(a), header_size, json_size


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2

    exe_path, asar_path = sys.argv[1], sys.argv[2]
    for p in (exe_path, asar_path):
        if not os.path.isfile(p):
            print("error: no such file: %s" % p)
            return 2

    blob = read_pe_resource(exe_path)
    if blob is None:
        print("no INTEGRITY > ELECTRONASAR resource found in the executable")
        print("this build does not use embedded ASAR integrity validation")
        return 2

    try:
        record = json.loads(blob.decode("utf-8"))
    except Exception as exc:
        print("could not parse integrity record: %s" % exc)
        return 2

    entry = record[0] if isinstance(record, list) and record else record
    embedded = str(entry.get("value", "")).lower()
    algorithm = entry.get("alg", "SHA256")

    measured, size, header_size, json_size = asar_header_hash(asar_path)

    print("executable        %s" % exe_path)
    print("archive           %s" % asar_path)
    print("algorithm         %s" % algorithm)
    print("archive size      %d bytes" % size)
    print("header size       %d bytes" % header_size)
    print("header JSON size  %d bytes" % json_size)
    print()
    print("embedded          %s" % embedded)
    print("measured          %s" % measured)

    if embedded == measured:
        print("\nRESULT  MATCH - archive matches its embedded integrity record")
        return 0

    print("\nRESULT  MISMATCH - archive does not match the embedded record")
    return 1


if __name__ == "__main__":
    sys.exit(main())
