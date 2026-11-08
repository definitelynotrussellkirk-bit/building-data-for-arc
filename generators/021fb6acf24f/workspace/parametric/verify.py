"""Verify a materialized color-order evidence tree."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prototype import verify_tree


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = verify_tree(args.out)
    print(json.dumps(result, sort_keys=True))
    return int(result["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
