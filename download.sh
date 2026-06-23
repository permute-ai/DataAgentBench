#!/usr/bin/env bash
set -euo pipefail

# DataAgentBench dataset downloader.
#
# Most dataset files are tracked with Git LFS and arrive automatically when you
# clone the repo with LFS enabled. Two things still need this script:
#
#   1. The PATENTS database `patent_publication.db` (~5GB) is too large for Git
#      LFS, so it lives on Google Drive.
#   2. If Git LFS failed (not installed, quota/bandwidth limits, network
#      errors), some tracked files will be missing or left as tiny pointer
#      stubs. A complete mirror of every dataset is available on the Hugging
#      Face Hub as a fallback.
#
# Modes (selected via --mode, default 1):
#
#   Mode 1 — Git LFS succeeded.
#     bash download.sh
#     bash download.sh --mode 1
#       Downloads only the PATENTS database from Google Drive. Everything else
#       is assumed to have come down via Git LFS.
#
#   Mode 2 — some Git LFS files failed; fall back to the Hugging Face mirror.
#     bash download.sh --mode 2
#       Downloads ALL dataset files from Hugging Face and verifies each one
#       against the sha256 checksum recorded in dataset_manifest.tsv.
#     bash download.sh --mode 2 PATENTS imdb
#       Downloads only the specified dataset(s) from Hugging Face. A dataset is
#       named by its `query_<NAME>` directory; both `PATENTS` and
#       `query_PATENTS` are accepted.
#
# Re-running is safe: files already present with the expected size are skipped.

cd "$(dirname "$0")"

# --- Google Drive (PATENTS) config -----------------------------------------
# db link: https://drive.google.com/file/d/1pALQ1UH-OwaEUeGYAx47uCyzClfK94XC/view?usp=sharing
PATENT_FILE_ID="1pALQ1UH-OwaEUeGYAx47uCyzClfK94XC"
PATENT_OUTPUT_PATH="query_PATENTS/query_dataset/patent_publication.db"

# --- Hugging Face mirror config ---------------------------------------------
REPO_ID="${DAB_HF_REPO:-ruiyingm/DataAgentBench-data}"
MANIFEST="${DAB_MANIFEST:-dataset_manifest.tsv}"

# --- Argument parsing -------------------------------------------------------
MODE=1
DATASETS=()

usage() {
    sed -n '3,40p' "$0"
    exit "${1:-0}"
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --mode)
            MODE="${2:-}"
            shift 2
            ;;
        --mode=*)
            MODE="${1#*=}"
            shift
            ;;
        -h|--help)
            usage 0
            ;;
        -*)
            echo "ERROR: unknown option '$1'" >&2
            usage 1
            ;;
        *)
            DATASETS+=("$1")
            shift
            ;;
    esac
done

if [ "$MODE" != "1" ] && [ "$MODE" != "2" ]; then
    echo "ERROR: --mode must be 1 or 2 (got '$MODE')." >&2
    usage 1
fi

if [ "$MODE" = "1" ] && [ "${#DATASETS[@]}" -gt 0 ]; then
    echo "ERROR: dataset names are only valid with --mode 2." >&2
    usage 1
fi

# --- Mode 1: download the PATENTS database from Google Drive ----------------
download_patent_from_gdrive() {
    if [ -f "$PATENT_OUTPUT_PATH" ]; then
        FILE_SIZE=$(stat -c%s "$PATENT_OUTPUT_PATH")
        if [ "$FILE_SIZE" -gt 5368709120 ]; then
            echo "PATENTS database already exists and is larger than 5GB. Skipping download."
            return 0
        else
            echo "PATENTS database exists but is smaller than 5GB. Re-downloading..."
            rm "$PATENT_OUTPUT_PATH"
        fi
    fi

    echo "Downloading PATENTS database (~5GB) from Google Drive..."
    mkdir -p "$(dirname "$PATENT_OUTPUT_PATH")"

    if ! command -v gdown &> /dev/null; then
        echo "gdown not found. Installing..."
        pip install gdown
    fi

    gdown --id "$PATENT_FILE_ID" -O "$PATENT_OUTPUT_PATH"

    echo "Download complete."
    echo "Verifying file size..."
    du -sh "$PATENT_OUTPUT_PATH"
}

# --- Mode 2: download datasets from the Hugging Face mirror -----------------
download_from_huggingface() {
    if [ ! -f "$MANIFEST" ]; then
        echo "ERROR: manifest '$MANIFEST' not found (run from the repo root)." >&2
        exit 1
    fi

    if ! python -c "import huggingface_hub" >/dev/null 2>&1; then
        echo "huggingface_hub not found. Installing..."
        pip install -q "huggingface_hub>=0.23"
    fi

    if [ "${#DATASETS[@]}" -gt 0 ]; then
        echo "Downloading datasets [${DATASETS[*]}] from https://huggingface.co/datasets/${REPO_ID}"
    else
        echo "Downloading ALL datasets from https://huggingface.co/datasets/${REPO_ID}"
    fi

    REPO_ID="$REPO_ID" MANIFEST="$MANIFEST" \
    DATASETS="${DATASETS[*]:-}" VERIFY_ALL="${VERIFY_ALL:-0}" python - <<'PY'
import hashlib
import os
import sys

from huggingface_hub import hf_hub_download

repo_id = os.environ["REPO_ID"]
manifest = os.environ["MANIFEST"]
verify_all = os.environ.get("VERIFY_ALL", "0") == "1"

# Optional whitelist of datasets. A dataset is its `query_<NAME>` directory;
# accept both `PATENTS` and `query_PATENTS` (case-insensitive).
raw = os.environ.get("DATASETS", "").split()
wanted = set()
for name in raw:
    name = name.strip()
    if not name:
        continue
    name = name[len("query_"):] if name.lower().startswith("query_") else name
    wanted.add(name.lower())


def dataset_of(path):
    top = path.split("/", 1)[0]  # e.g. "query_PATENTS"
    return top[len("query_"):].lower() if top.lower().startswith("query_") else top.lower()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


entries = []
with open(manifest) as f:
    for line in f:
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        path, digest, size = line.split("\t")
        entries.append((path, digest, int(size)))

if wanted:
    available = {dataset_of(p) for p, _, _ in entries}
    unknown = wanted - available
    if unknown:
        print(f"ERROR: unknown dataset(s): {', '.join(sorted(unknown))}")
        print(f"Available: {', '.join(sorted(available))}")
        sys.exit(1)
    entries = [e for e in entries if dataset_of(e[0]) in wanted]

downloaded = skipped = 0
failures = []

for path, digest, size in entries:
    # Skip if already present and the right size (and, when VERIFY_ALL, the
    # right hash). This avoids re-hashing many GB on every run.
    if os.path.isfile(path) and os.path.getsize(path) == size:
        if not verify_all or sha256(path) == digest:
            print(f"  [skip] {path}")
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
print(f"Downloaded: {downloaded}, skipped: {skipped}, failed: {len(failures)}")
if failures:
    print("Failed files:")
    for p in failures:
        print(f"  - {p}")
    sys.exit(1)
print("All requested datasets present and verified.")
PY
}

# --- Dispatch ---------------------------------------------------------------
if [ "$MODE" = "1" ]; then
    download_patent_from_gdrive
else
    download_from_huggingface
fi

echo "Done."
