"""Exercise the delivered replay helper on small original-source copies.

Requires the original packet ZIP; does not import or modify the active repo.
The cases verify receipt/source collision refusal, wrong-root refusal,
wrong-patch refusal, successful subdirectory application, and repeat refusal.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-zip", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    helper = here / "apply_verified_delta.py"
    expected_path = here / "expected-source-files.json"
    expected = json.loads(expected_path.read_text())
    patch = here / "source-tested.patch"
    args.out.mkdir(parents=True, exist_ok=False)
    cases = []
    with tempfile.TemporaryDirectory(prefix="delta-prefix-regression-") as td:
        root = Path(td)
        workspace = root / "WORK"
        workspace.mkdir()
        with zipfile.ZipFile(args.original_zip) as archive:
            for row in expected["files"]:
                if row["before_sha256"] is not None:
                    path = workspace / row["path"]
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(archive.read("WORK/" + row["path"]))
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        altered = root / "altered.patch"
        altered.write_bytes(patch.read_bytes() + b"\n")

        def snapshot():
            return {row["path"]: hashlib.sha256((workspace / row["path"]).read_bytes()).hexdigest()
                    if (workspace / row["path"]).is_file() else None
                    for row in expected["files"]}

        for name, git_root, patch_path, wanted in (
            ("receipt-source-collision", root, patch, 2),
            ("wrong-root", workspace, patch, 1),
            ("wrong-patch", root, altered, 1),
            ("nested-workspace", root, patch, 0),
            ("repeat-apply", root, patch, 1),
        ):
            before = snapshot()
            receipt = args.out / (name + ".json")
            if name == "receipt-source-collision":
                receipt = workspace / next(row["path"] for row in expected["files"]
                                           if row["before_sha256"] is None)
            argv = [sys.executable, str(helper), "--workspace", str(workspace),
                    "--git-root", str(git_root), "--patch", str(patch_path),
                    "--expected-files", str(expected_path), "--receipt", str(receipt)]
            result = subprocess.run(argv, text=True, capture_output=True, timeout=30)
            after = snapshot()
            if result.returncode != wanted or (wanted and before != after):
                failure = {"status": "failed", "name": name, "argv": argv,
                           "cwd": str(Path.cwd()), "exit_code": result.returncode,
                           "expected_exit_code": wanted, "stdout": result.stdout,
                           "stderr": result.stderr, "before": before, "after": after,
                           "helper_source_sha256": hashlib.sha256(helper.read_bytes()).hexdigest()}
                (args.out / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")
                if receipt.is_file():
                    (args.out / "unexpected-receipt.json").write_bytes(receipt.read_bytes())
            assert result.returncode == wanted, (name, result.stdout, result.stderr)
            if wanted:
                assert before == after, (name, "refusal mutated source")
            else:
                assert all(after[row["path"]] == row["after_sha256"]
                           for row in expected["files"])
            cases.append({"name": name, "argv": argv, "cwd": str(Path.cwd()),
                          "exit_code": result.returncode, "expected_exit_code": wanted,
                          "source_unchanged_on_refusal": before == after if wanted else None,
                          "all_after_hashes_match": True if not wanted else None,
                          "stdout": result.stdout, "stderr": result.stderr,
                          "receipt": str(receipt), "status": "passed"})
    summary = {"status": "passed", "cases_passed": len(cases), "cases": cases,
               "helper_source_sha256": hashlib.sha256(helper.read_bytes()).hexdigest(),
               "scope": "Small original-source copies in a Git root above WORK; no full runtime or suite"}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"status": "passed", "cases": len(cases)}))


if __name__ == "__main__":
    main()
