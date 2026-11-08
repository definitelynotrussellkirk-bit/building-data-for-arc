#!/usr/bin/env python3
"""Build Racket-backed evidence for the 2a5919c40197 line-axis prototype."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prototype import build_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    parser.add_argument("--seeds", type=int, default=6, help="bounded seed census (>=2)")
    args = parser.parse_args()
    report = build_evidence(args.out, seeds=args.seeds)
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "canonical_row_matches": report["canonical_row_matches"],
                "racket_labels": report["racket_execution"]["labels"],
                "identifiable_rotations": report["census"]["identifiable_rotations"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
