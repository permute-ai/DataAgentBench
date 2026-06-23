#!/usr/bin/env bash
set -euo pipefail

# DataAgentBench dataset downloader.
#
# Run this once after cloning the repo, regardless of whether Git LFS was
# installed or succeeded. The large dataset files (PostgreSQL dumps,
# SQLite/DuckDB databases, MongoDB BSON, the ~5GB PATENTS database, etc.) are
# mirrored on the Hugging Face Hub.
#
#   bash download.sh
#
# For every file listed in dataset_manifest.tsv, the script checks whether the
# local copy's content matches the recorded sha256 checksum. If it is missing,
# the wrong size (e.g. an un-resolved Git LFS pointer stub), or its hash does
# not match, the file is (re)downloaded from Hugging Face and re-verified.
# Files that already match are left untouched, so re-running is cheap and safe.

REPO_ID="${DAB_HF_REPO:-ruiyingm/DataAgentBench-data}"
MANIFEST="${DAB_MANIFEST:-dataset_manifest.tsv}"

cd "$(dirname "$0")"

if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: manifest '$MANIFEST' not found (run from the repo root)." >&2
    exit 1
fi

# huggingface_hub powers the download. Auto-install if absent.
if ! python -c "import huggingface_hub" >/dev/null 2>&1; then
    echo "huggingface_hub not found. Installing..."
    pip install -q "huggingface_hub>=0.23"
fi

echo "Verifying datasets against $MANIFEST and downloading any that don't match"
echo "from https://huggingface.co/datasets/${REPO_ID}"

REPO_ID="$REPO_ID" MANIFEST="$MANIFEST" python - <<'PY'
import hashlib
import os
import sys

from huggingface_hub import hf_hub_download

repo_id = os.environ["REPO_ID"]
manifest = os.environ["MANIFEST"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def matches(path, digest, size):
    # A file's content matches only if it is present, the right size, and the
    # right hash. The size check is a fast pre-filter: a missing file or a tiny
    # Git LFS pointer stub fails it immediately, so we avoid hashing those.
    if not os.path.isfile(path) or os.path.getsize(path) != size:
        return False
    return sha256(path) == digest


entries = []
with open(manifest) as f:
    for line in f:
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        path, digest, size = line.split("\t")
        entries.append((path, digest, int(size)))

downloaded = skipped = 0
failures = []

for path, digest, size in entries:
    if matches(path, digest, size):
        print(f"  [ok  ] {path}")
        skipped += 1
        continue

    print(f"  [get ] {path} ({size / 1e6:.1f} MB)")
    try:
        hf_hub_download(
            repo_id=repo_id,
            repo_type="dataset",
            filename=path,
            local_dir=".",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"  [FAIL] download error for {path}: {exc}")
        failures.append(path)
        continue

    actual = sha256(path)
    if actual != digest:
        print(f"  [FAIL] checksum mismatch for {path}")
        print(f"         expected {digest}")
        print(f"         actual   {actual}")
        failures.append(path)
        continue
    downloaded += 1

print()
print(f"Downloaded: {downloaded}, already matched: {skipped}, failed: {len(failures)}")
if failures:
    print("Failed files:")
    for p in failures:
        print(f"  - {p}")
    sys.exit(1)
print("All datasets present and verified.")
PY

echo "Done."
