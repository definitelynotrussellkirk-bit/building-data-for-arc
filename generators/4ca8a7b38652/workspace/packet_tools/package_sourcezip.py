#!/usr/bin/env python3
"""Opt-in local packaging proposal; leaves the stock wrapper/modules unchanged."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ORIGINAL_SHA256 = "a021d00ec056acbdf0958955f5d08f110bff934375a6dac397fc3f86089a2f74"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work", type=Path, help="Review WORK directory")
    parser.add_argument("--source-zip", type=Path, help="Opt in to strict archive-backed immutable sources")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--bundle-evidence", action="store_true")
    args = parser.parse_args(argv)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(HERE))
    runtime = args.work / "repo/src"
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
    try:
        # Pin the current proposal to the exact stock infrastructure it extends.
        spec = importlib.util.find_spec("arcpuzzles.review_full_return")
        if spec is None or spec.origin is None:
            raise ValueError("Official arcpuzzles runtime is unavailable; set PYTHONPATH to its src directory")
        stock_path = Path(spec.origin)
        actual = hashlib.sha256(stock_path.read_bytes()).hexdigest()
        if actual != ORIGINAL_SHA256:
            raise ValueError("Official builder differs from this proposal's pinned original; review/regenerate the proposal")
        from arcpuzzles.review_full_return import validate_full_return
        candidate_spec = importlib.util.spec_from_file_location(
            "arcpuzzles.review_full_return_sourcezip_proposal", HERE / "review_full_return_sourcezip.py")
        candidate = importlib.util.module_from_spec(candidate_spec)
        candidate_spec.loader.exec_module(candidate)
        result = candidate.build_full_return(args.work, args.out, bundle_evidence=args.bundle_evidence,
                                             source_zip=args.source_zip)
        manifest = json.loads((args.work / "PACKET-MANIFEST.json").read_text())
        with zipfile.ZipFile(result["zip"]) as archive:
            official = validate_full_return(archive, manifest)
        print(json.dumps({"local_proposal": True, "source_zip_mode": args.source_zip is not None,
                          "stock_builder_sha256": actual, "build_result": result,
                          "official_validation": official}, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, ImportError, zipfile.BadZipFile) as error:
        print(json.dumps({"status": "failed", "error": f"{type(error).__name__}: {error}"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
