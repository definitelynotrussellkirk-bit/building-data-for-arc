"""Project source-bound qualified episodes into independent single-query views.

Run from the packet through ``review.py run python3 <this-file> export
--qualification PATH --out NEW_DIRECTORY``; use ``verify --bundle DIRECTORY``
to check a saved projection. Only one ``public/<sha256>.json`` is a model turn.
The bundle, its directory listing, and all of ``private/`` belong to the caller;
they contain future queries, order, labels, and source metadata. This module
does not implement a controller, replay Racket, accept source, or admit training.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[4]
TASK_ID = "699479899861"
SCHEMA = "arcpuzzles-qualified-sequential-projection-v1"
LIMITS = (
    "Source-bound receipt and serialized projection checks only; no new Racket "
    "replay, independent authentication of rewritten receipts, owner acceptance, "
    "or training admission. Reveal one selected public file at a time."
)

if __name__ == "__main__":
    # Direct invocation uses this checkout, never an ambient sibling environment.
    sys.path.insert(0, str(ROOT / "src"))

from arcpuzzles.parametric_worker import _grid
from arcpuzzles.review_witness import _qualified


def _load_public_helper():
    path = ROOT / "shared/runtime/reviewer_support.py"
    spec = importlib.util.spec_from_file_location("_arc699479899861_public_helper", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module.public_challenge_bytes


_public_bytes = _load_public_helper()


def _raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def public_view_bytes(episode, query_index=0):
    """Return visible bytes, independent of every hidden label and future query."""
    queries = episode.get("test")
    if (type(queries) is not list or type(query_index) is not int
            or not 0 <= query_index < len(queries)):
        raise ValueError("query_index must select one query with an exact integer")
    return _public_bytes({"train": episode.get("train"),
                          "test": [{"input": queries[query_index]["input"]}]})


def _projection(qualification, execution, qualification_bytes, execution_bytes):
    if qualification.get("task_id") != TASK_ID:
        raise ValueError("This task-local exporter requires qualification for " + TASK_ID)
    views, episodes = {}, []
    for episode_index, episode in enumerate(execution["episodes"]):
        if not 2 <= len(episode["train"]) <= 6 or len(episode["test"]) != 4:
            raise ValueError("This native qualification requires 2..6 demos and four private queries")
        inputs = []
        for split in ("train", "test"):
            for pair in episode[split]:
                # The native receipt checker checks provenance/certificates;
                # strict grids and distinct inputs are checked here as well.
                inputs.append(_raw(_grid(pair["input"])))
                _grid(pair["output"])
        if len(set(inputs)) != len(inputs):
            raise ValueError("Demonstration and query inputs must be distinct")
        identifiers = []
        for query_index in range(len(episode["test"])):
            payload = public_view_bytes(episode, query_index)
            identifier = _sha(payload)
            if identifier in views:
                raise ValueError("Duplicate visible query view; no bundle was published")
            views[identifier] = payload
            identifiers.append(identifier)
        episodes.append({"episode_index": episode_index, "view_ids": identifiers})
    manifest = {
        "schema": SCHEMA, "task_id": TASK_ID, "status": "qualified_projection",
        "qualification": {"path": "qualification.json", "sha256": _sha(qualification_bytes)},
        "execution": {"path": "execution.json", "sha256": _sha(execution_bytes)},
        "source_binding": qualification["source_binding"],
        "episodes": episodes,
        "public_files": [{"path": f"public/{identifier}.json", "sha256": identifier}
                         for identifier in sorted(views)],
        "racket_replayed": False, "owner_acceptance": "not_performed",
        "training_admitted": False, "limits": LIMITS,
    }
    return views, manifest


def _read_qualification(library, qualification):
    path = Path(qualification).resolve()
    execution_path = path.with_name("execution.json")
    qbytes, ebytes = path.read_bytes(), execution_path.read_bytes()
    q, execution = _qualified(library, path)
    if path.read_bytes() != qbytes or execution_path.read_bytes() != ebytes:
        raise ValueError("Qualification or execution changed during validation")
    return q, execution, qbytes, ebytes


def _check_files(bundle, views, manifest):
    expected = {"private/qualification.json", "private/execution.json", "private/manifest.json"}
    expected.update(row["path"] for row in manifest["public_files"])
    actual, directories = set(), set()
    for path in bundle.rglob("*"):
        if path.is_symlink():
            raise ValueError("Projection bundle must contain no symlinks")
        if path.is_file():
            actual.add(path.relative_to(bundle).as_posix())
        elif path.is_dir():
            directories.add(path.relative_to(bundle).as_posix())
    if actual != expected or directories != {"public", "private"}:
        raise ValueError("Projection file inventory differs; unexpected or missing file")
    if (bundle / "private/manifest.json").read_bytes() != _raw(manifest):
        raise ValueError("Private manifest differs from source-bound projection")
    for identifier, payload in views.items():
        if (bundle / "public" / f"{identifier}.json").read_bytes() != payload:
            raise ValueError("Public view differs from its exact visible bytes/hash")


def verify_export(bundle, *, library=ROOT):
    """Validate saved bytes and current source binding without another replay."""
    bundle = Path(bundle)
    if bundle.is_symlink():
        raise ValueError("Projection bundle must be a real directory")
    values = _read_qualification(library, bundle / "private/qualification.json")
    views, manifest = _projection(*values)
    _check_files(bundle, views, manifest)
    return {"status": "verified_projection", "task_id": TASK_ID,
            "episodes": len(manifest["episodes"]), "views": len(views),
            "training_admitted": False, "racket_replayed": False}


def export_qualified(qualification, output, *, library=ROOT):
    """Save strict single-query views and a private order/source/answer mapping."""
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Choose a new output directory: {output}")
    qualification = Path(qualification).resolve()
    values = _read_qualification(library, qualification)
    views, manifest = _projection(*values)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".arc-single-query-", dir=output.parent) as directory:
        stage = Path(directory)
        (stage / "public").mkdir()
        (stage / "private").mkdir(mode=0o700)
        for identifier in sorted(views):
            (stage / "public" / f"{identifier}.json").write_bytes(views[identifier])
        (stage / "private/qualification.json").write_bytes(values[2])
        (stage / "private/execution.json").write_bytes(values[3])
        (stage / "private/manifest.json").write_bytes(_raw(manifest))
        # A source or receipt edit while serializing must block publication.
        if _read_qualification(library, qualification) != values:
            raise ValueError("Qualified source or receipt changed during projection")
        verify_export(stage, library=library)
        output.mkdir(exist_ok=False)
        (stage / "public").rename(output / "public")
        # The completion manifest is published last, together with private data.
        (stage / "private").rename(output / "private")
    return {"status": "qualified_projection", "task_id": TASK_ID,
            "episodes": len(manifest["episodes"]), "views": len(views),
            "manifest": str((output / "private/manifest.json").resolve()),
            "training_admitted": False, "racket_replayed": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export")
    export.add_argument("--qualification", type=Path, required=True)
    export.add_argument("--out", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = (export_qualified(args.qualification, args.out) if args.command == "export"
                  else verify_export(args.bundle))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"export_qualified: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
