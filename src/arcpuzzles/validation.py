"""Structural migration checks; does not confer generator quality approval."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys
import tempfile

from .catalog import Catalog, local_path, sha256


def validate_library(catalog: Catalog, *, verify_import: bool = False, import_generators: bool = False) -> dict:
    errors = []
    mappings = json.loads((catalog.root / "catalog/runtime_files.json").read_text())
    destinations = set()
    for row in mappings:
        try:
            path = local_path(catalog.root, row["path"])
            local_path(Path("/arcpuzzles-validation-root"), row["target"])
            if not path.is_file() or path.is_symlink():
                errors.append(f"Missing regular runtime source: {row['path']}")
            if row["target"] in destinations:
                errors.append(f"Duplicate runtime target: {row['target']}")
            destinations.add(row["target"])
        except ValueError as exc:
            errors.append(str(exc))
    generators = 0
    for row in catalog._records.values():
        if not row.get("generator"):
            continue
        generators += 1
        home = catalog.root / "generators" / row["id"]
        for name in ("generator.py", "SUMMARY.md", "notes.md", "workspace/README.md", "evidence/associated_notes.jsonl"):
            if not (home / name).is_file():
                errors.append(f"{row['id']}: missing {name}")
        try:
            ast.parse((home / "generator.py").read_text())
        except (SyntaxError, OSError) as exc:
            errors.append(f"{row['id']}: {exc}")
        if row["runtime_generator"] not in destinations:
            errors.append(f"{row['id']}: generator missing from runtime mapping")
    checked = 0
    if verify_import:
        manifest = json.loads((catalog.root / "docs/migration/import-manifest.json").read_text())
        for row in manifest["copied_files"]:
            path = local_path(catalog.root, row["path"])
            checked += 1
            if not path.is_file() or sha256(path) != row["sha256"]:
                errors.append(f"Changed/missing imported original: {row['path']}")
    imported = 0
    if import_generators and not errors:
        from .runtime import prepare_runtime, run_process
        with tempfile.TemporaryDirectory(prefix="arcpuzzles-imports-") as directory:
            stage = Path(directory)
            prepare_runtime(catalog, stage)
            modules = [row["runtime_generator"].replace("/", ".")[:-3]
                       for row in catalog._records.values() if row.get("generator")]
            (stage / "request.json").write_text(json.dumps({"mode": "imports", "modules": modules}))
            result = run_process([sys.executable, "-E", "-s", str(stage / "arcpuzzles_worker.py")], stage, timeout=180)
            if result["exit_code"] or result["timed_out"]:
                errors.append(f"Import worker failed: {result['stderr']} (timeout={result['timed_out']})")
            else:
                report = json.loads((stage / "imports.json").read_text())
                imported = report["imported"]
                errors.extend(report["errors"])
    return {"passed": not errors, "generators": generators, "runtime_mappings": len(mappings),
            "generator_imports_checked": imported,
            "original_hashes_checked": checked, "errors": errors,
            "scope": "library structure/source integrity; not a semantic quality review"}
