"""Run the supplied full-return builder against a sparse packet extraction."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import re
import stat
import sys

from archive_overlay import ArchiveOverlay, ArchiveOverlayError


def sha256_arg(value):
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise argparse.ArgumentTypeError("expected a lowercase 64-character SHA-256 digest")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, required=True, help="sparse extracted WORK directory")
    parser.add_argument("--source-zip", type=Path, required=True, help="original immutable packet ZIP")
    parser.add_argument("--zip-sha256", type=sha256_arg, required=True, help="independently recorded original ZIP digest")
    parser.add_argument("--omissions", type=Path, required=True, help="JSON path list recorded at sparse extraction")
    parser.add_argument("--out", type=Path, required=True, help="new return ZIP; must not exist")
    parser.add_argument("--receipt", type=Path, help="optional new JSON receipt including all verified virtual paths")
    args = parser.parse_args(argv)
    try:
        work = args.work.resolve(strict=True)
        omitted = json.loads(args.omissions.read_text())
        if not isinstance(omitted, list) or not all(isinstance(p, str) for p in omitted):
            raise ArchiveOverlayError("Omissions must be a JSON list of path strings")
        if args.receipt is not None:
            receipt = args.receipt.resolve()
            if receipt == args.out.resolve() or receipt.is_relative_to(work / "repo"):
                raise ValueError("Receipt must differ from output and be outside WORK/repo")
            if args.receipt.exists() or args.receipt.is_symlink():
                raise FileExistsError(f"Receipt already exists: {args.receipt}")
            if not args.receipt.parent.is_dir():
                raise FileNotFoundError(f"Receipt parent directory does not exist: {args.receipt.parent}")
        with ArchiveOverlay(work, args.source_zip, expected_zip_sha256=args.zip_sha256,
                            omitted_paths=omitted) as overlay:
            # Require the real supplied builder before importing it. The original
            # builder subsequently checks every other immutable repository file.
            source = work / "repo/src/arcpuzzles/review_full_return.py"
            manifest = json.loads((work / "PACKET-MANIFEST.json").read_text())
            if (source.is_symlink() or not stat.S_ISREG(source.stat().st_mode)
                    or hashlib.sha256(source.read_bytes()).hexdigest()
                    != manifest["files"].get("repo/src/arcpuzzles/review_full_return.py")):
                raise ArchiveOverlayError("The supplied full-return builder must be present and unmodified")
            sys.path.insert(0, str(work / "repo/src"))
            try:
                module = importlib.import_module("arcpuzzles.review_full_return")
                if Path(module.__file__).resolve() != source.resolve():
                    raise ArchiveOverlayError("A different arcpuzzles installation was imported")
                result = module.build_full_return(work, args.out)
            finally:
                sys.path.pop(0)
        summary = {"build": result, "overlay": overlay.report()}
        if args.receipt is not None:
            with args.receipt.open("x", encoding="utf-8") as f:
                json.dump({"build": result, "overlay": overlay.report(include_paths=True)}, f,
                          sort_keys=True, indent=2)
                f.write("\n")
        print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        parser.exit(1, f"package_sparse: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
