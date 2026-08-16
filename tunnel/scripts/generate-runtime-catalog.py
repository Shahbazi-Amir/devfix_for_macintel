#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def die(msg: str) -> None:
    raise SystemExit(msg)


if len(sys.argv) != 3:
    die("usage: generate-runtime-catalog.py PT_CONFIG_JSON OUTPUT_TSV")

src = Path(sys.argv[1])
out = Path(sys.argv[2])
data = json.loads(src.read_text(encoding="utf-8"))
bridges = data.get("bridges", {})

rows = []
for transport in ("snowflake", "meek", "obfs4"):
    values = bridges.get(transport, [])
    if not isinstance(values, list):
        die(f"{transport} bridge catalog is not a list")
    for idx, bridge in enumerate(values, 1):
        if not isinstance(bridge, str) or not bridge.strip():
            die(f"invalid {transport} bridge entry #{idx}")
        if "\t" in bridge or "\n" in bridge or "\r" in bridge:
            die(f"unsafe whitespace in {transport} bridge entry #{idx}")
        rows.append((transport, idx, bridge.strip()))

if len(bridges.get("snowflake", [])) < 2:
    die("expected at least two bundled Snowflake bridge definitions")
if not bridges.get("meek"):
    die("expected at least one bundled meek bridge definition")
if not bridges.get("obfs4"):
    die("expected at least one bundled obfs4 bridge definition")

out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", encoding="utf-8", newline="\n") as f:
    f.write("# DevFix Tunnel runtime transport catalog\n")
    f.write("# Generated from the exact Tor Expert Bundle pt_config.json at package build time.\n")
    f.write("# transport<TAB>candidate<TAB>bridge-line\n")
    for transport, idx, bridge in rows:
        f.write(f"{transport}\t{idx}\t{bridge}\n")
