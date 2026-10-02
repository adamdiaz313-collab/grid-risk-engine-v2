"""Download selected EAGLE-I files from the official Figshare record.

The downloader is intentionally explicit: it lists available files first and
requires the caller to request filenames or years. This avoids accidentally
pulling the entire multi-year archive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import requests

from training.config import (
    EAGLEI_FIGSHARE_API_URL,
    EAGLEI_RAW_DIR,
    ensure_project_directories,
)

CHUNK_SIZE = 1024 * 1024


def fetch_article_metadata() -> dict:
    response = requests.get(EAGLEI_FIGSHARE_API_URL, timeout=30)
    response.raise_for_status()
    return response.json()


def available_files(metadata: dict) -> list[dict]:
    files = metadata.get("files", [])
    if not isinstance(files, list):
        raise ValueError("Unexpected Figshare metadata: 'files' is not a list.")
    return files


def infer_year(filename: str) -> int | None:
    match = re.search(r"(20\d{2})", filename)
    return int(match.group(1)) if match else None


def select_files(
    files: list[dict],
    *,
    years: list[int] | None = None,
    filenames: list[str] | None = None,
) -> list[dict]:
    selected = []

    requested_names = set(filenames or [])
    requested_years = set(years or [])

    for item in files:
        name = item.get("name", "")
        year = infer_year(name)

        if requested_names and name in requested_names:
            selected.append(item)
        elif requested_years and year in requested_years:
            selected.append(item)

    if requested_names:
        found = {item.get("name") for item in selected}
        missing = requested_names - found
        if missing:
            raise ValueError(
                "Requested EAGLE-I files were not found in official metadata: "
                + ", ".join(sorted(missing))
            )

    return selected


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_file(item: dict, destination_dir: Path) -> Path:
    name = item.get("name")
    download_url = item.get("download_url")

    if not name or not download_url:
        raise ValueError(f"Figshare file metadata is missing name/url: {item}")

    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / name
    temporary = destination.with_suffix(destination.suffix + ".part")

    if destination.exists():
        print(f"Already present: {destination}")
        return destination

    print(f"Downloading {name}...")
    with requests.get(download_url, stream=True, timeout=300) as response:
        response.raise_for_status()
        with temporary.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    handle.write(chunk)

    temporary.replace(destination)
    print(f"Saved: {destination}")
    return destination


def write_manifest(metadata: dict, downloaded: list[Path]) -> Path:
    manifest = {
        "source": EAGLEI_FIGSHARE_API_URL,
        "article_id": metadata.get("id"),
        "title": metadata.get("title"),
        "version": metadata.get("version"),
        "downloaded_files": [
            {
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in downloaded
        ],
    }

    manifest_path = EAGLEI_RAW_DIR / "download_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def print_available(files: list[dict]) -> None:
    for item in files:
        name = item.get("name", "<unnamed>")
        size = item.get("size")
        size_text = f"{size / (1024 ** 2):.1f} MiB" if isinstance(size, int) else "size unknown"
        print(f"{name}  ({size_text})")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--list",
        action="store_true",
        help="List files in the official EAGLE-I Figshare record.",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        help="Download files whose names contain these years.",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="Download exact filenames from the Figshare record.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_project_directories()

    metadata = fetch_article_metadata()
    files = available_files(metadata)

    if args.list or (not args.years and not args.files):
        print_available(files)
        if not args.years and not args.files:
            print("\nNo download requested. Use --years or --files.")
        return

    selected = select_files(files, years=args.years, filenames=args.files)
    if not selected:
        raise SystemExit("No files matched the requested years/files.")

    downloaded = [download_file(item, EAGLEI_RAW_DIR) for item in selected]
    manifest_path = write_manifest(metadata, downloaded)

    print(f"Download manifest: {manifest_path}")


if __name__ == "__main__":
    main()
