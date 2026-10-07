#!/usr/bin/env bash
# Reproduce the extraction of the Ray-Ban Display OTA used in this research.
# Usage: tools/extract_ota.sh <work_dir> [ota_url]
# Output: <work_dir>/zip/  (original zip + metadata)  and  <work_dir>/img/  (partition images)
set -euo pipefail
WORK="${1:?usage: extract_ota.sh <work_dir> [ota_url]}"
URL="${2:-https://files.cocaine.trade/firmware/meta/Ray-Ban%20Display/greatwhite_65394930092600080.zip}"
EXPECTED_SHA256="6411fd4f52782e576b6ff7662fa3d62e7af838ae64f4843736a8fa1ef67b1068"
mkdir -p "$WORK/zip" "$WORK/img"
ZIP="$WORK/zip/greatwhite_65394930092600080.zip"
[ -f "$ZIP" ] || curl -sSL --retry 3 -C - -o "$ZIP" "$URL"
GOT=$(sha256sum "$ZIP" | cut -d' ' -f1)
[ "$GOT" = "$EXPECTED_SHA256" ] || { echo "SHA-256 mismatch: $GOT"; exit 1; }
unzip -q -o "$ZIP" -d "$WORK/zip/unpacked"
# payload_dumper: pip install payload-dumper
payload_dumper --out "$WORK/img" "$WORK/zip/unpacked/payload.bin"
echo "Extracted $(ls "$WORK/img" | wc -l) images to $WORK/img"
