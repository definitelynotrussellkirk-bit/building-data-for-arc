#!/usr/bin/env python3
"""Historical initial import recipe; never changes the predecessor checkout.

The adjacent import-manifest.json is the final inventory, including dependency
copies and original-ID aliases added during standalone verification. This script
records the initial extraction method, not a supported library refresh command.
"""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

TOOLS = """lint_generator generator_selfcheck rule_smoke generator_defect_lint
generator_distribution_gate canonical_profile_gate generator_semantic_gate
gen_diversity_probe check_generator_override_contract grammar_gate racket_linter
check_task_authority_sync generator_battery_subject generic_generator_gate
lint_generators lint_puzzles lint_base_solutions lint_descriptions lint_racket_style
canonicalize_rule generator_module_loader""".split()
SKIP = {"__pycache__", ".pytest_cache", "compiled"}


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def metadata(path: Path) -> dict:
    tree = ast.parse(path.read_text())
    result = {"docstring": ast.get_docstring(tree) or ""}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
            if isinstance(target, ast.Name):
                try:
                    result[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError, SyntaxError):
                    pass  # Only statically readable metadata; never execute source here.
    return result


def closure(source: Path, seeds: set[Path]) -> set[Path]:
    pending, found = list(seeds), set()
    while pending:
        path = pending.pop()
        if path in found:
            continue
        found.add(path)
        for parent in path.parents:
            marker = parent / "__init__.py"
            if (source / marker).is_file() and marker not in found:
                pending.append(marker)
        for node in ast.walk(ast.parse((source / path).read_text())):
            modules = []
            if isinstance(node, ast.Import):
                modules = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                base = list(path.parent.parts)
                modules = ([".".join(base[:len(base)-node.level+1] + [node.module])]
                           if node.level else [node.module])
                modules += [modules[0] + "." + item.name for item in node.names]
            for module in modules:
                rel = Path(*module.split("."))
                choices = [rel.with_suffix(".py"), rel / "__init__.py"]
                if len(rel.parts) == 1:
                    choices += [path.parent / rel.with_suffix(".py"), Path("scripts") / rel.with_suffix(".py")]
                match = next((p for p in choices if (source / p).is_file()), None)
                if match is not None:
                    pending.append(match)
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    source, dest = args.source.resolve(), args.destination.resolve()
    if source == dest or source in dest.parents or dest in source.parents:
        raise SystemExit("Source and destination must be separate checkouts")
    if any((dest / p).exists() for p in ("catalog", "generators", "shared")):
        raise SystemExit("Refusing to overwrite an imported library")
    copied, derived, mappings = [], [], []

    def copy(original: Path, target: Path, runtime: Path | None = None) -> None:
        src, dst = source / original, dest / target
        if src.is_symlink() or not src.is_file():
            raise ValueError(f"Not a regular source file: {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        content = src.read_bytes()
        with dst.open("xb") as handle:
            handle.write(content)
        shutil.copymode(src, dst)
        copied.append({"source": str(original), "path": str(target),
                       "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)})
        if runtime is not None:
            mappings.append({"path": str(target), "target": str(runtime)})

    def write(relative: Path, content: str) -> None:
        path = dest / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as handle:
            handle.write(content)
        derived.append(str(relative))

    canon, db, notes = defaultdict(list), defaultdict(list), defaultdict(list)
    for name, target in [("canonical/puzzles.jsonl", canon), ("canonical/puzzle_db.jsonl", db),
                         ("derived/generator_associated_notes.jsonl", notes)]:
        for row in read_rows(source / "data" / name):
            target[row["task_id"]].append(row)
    assignments = {r["task_id"]: r for r in read_rows(source / "data/derived/kimi_generator_assignment.jsonl")}
    generators = {p.parent.name: p.relative_to(source)
                  for p in (source / "puzzle_generators/per_puzzle").glob("*/generator.py")}
    for p in (source / "puzzle_generators/generic/concepts").glob("*/gen[0-9]*.py"):
        generators[f"generic_{p.parent.name}_{p.stem}"] = p.relative_to(source)
    records = []
    for tid in sorted(set(canon) | set(generators) | set(assignments)):
        original, task_rows, assignment = generators.get(tid), canon[tid], assignments.get(tid, {})
        meta = metadata(source / original) if original else {}
        summary = str(meta.get("SUMMARY") or (task_rows[0].get("written_solution") if task_rows else "")
                      or meta.get("docstring") or tid)
        home, kind = Path("generators") / tid, "generic" if tid.startswith("generic_") else "per_puzzle"
        if original:
            if kind == "per_puzzle":
                for src in sorted((source / original.parent).rglob("*")):
                    if src.is_file() and not set(src.parts) & SKIP:
                        copy(src.relative_to(source), home / src.relative_to(source / original.parent), src.relative_to(source))
            else:
                copy(original, home / "generator.py", original)
            write(home / "SUMMARY.md", f"# {tid}\n\n{summary}\n\nKind: `{kind}`. Imported version: `{meta.get('VERSION', '?')}`.\n"
                  "Approval is derived by the catalog from current code and retained evidence.\n")
            write(home / "notes.md", f"# Working notes: {tid}\n\nRecord design decisions, hypotheses, review findings, and unresolved questions here.\n"
                  "Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.\n")
            write(home / "workspace/README.md", "# Workspace\n\nKeep alternate drafts, reproducers, and unfinished experiments here.\n"
                  "The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.\n")
            write(home / "evidence/associated_notes.jsonl", "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in notes[tid]))
        def values(key):
            return sorted({str(v) for r in task_rows for v in
                           (r.get(key, []) if isinstance(r.get(key), list) else [r.get(key)]) if v})
        records.append({"id": tid, "kind": kind, "summary": summary,
                        "sources": values("source"), "skills": values("skills"),
                        "difficulties": sorted({v.lower() for v in values("difficulty")}),
                        "primitives": sorted({p for r in db[tid] for p in r.get("racket_primitives", [])}),
                        "aliases": sorted({str(r[k]) for r in db[tid] for k in ("legacy_task_id", "original_id") if r.get(k) and r[k] != tid}),
                        "canonical_rows": len(task_rows), "generator": str(home / "generator.py") if original else None,
                        "runtime_generator": str(original) if original else None,
                        "version": str(meta.get("VERSION", "")), "rule_task_id": meta.get("RULE_TASK_ID", tid),
                        "family": assignment.get("root_rule_family_id") or None,
                        "split": assignment.get("split_assignment") or None,
                        "parent_ids": sorted({r["parent_hash"] for r in task_rows if r.get("parent_hash")}),
                        "train_safety": assignment.get("train_safety", "unreviewed"),
                        "mix_weight": float(assignment.get("recommended_mix_weight") or 0),
                        "semantic_veto": bool(assignment.get("active_semantic_veto")),
                        "veto_reason": assignment.get("active_semantic_veto_reason", ""),
                        "reviewed_generator_sha256": assignment.get("generator_sha256"),
                        "reviewed_rule_hash": assignment.get("rule_hash_expected"),
                        "review_status": assignment.get("latest_review_status", ""),
                        "health": assignment.get("health_list", "unknown"), "notes_count": len(notes[tid])})

    seeds = {Path("scripts") / (name + ".py") for name in TOOLS}
    seeds.update(p.relative_to(source) for p in (source / "arc_repl").rglob("*.py") if not set(p.parts) & SKIP)
    for p in (source / "puzzle_generators").rglob("*.py"):
        if ("per_puzzle" not in p.parts and p.name not in {"catalog.py", "llm_author.py"}
                and not set(p.parts) & SKIP and p.relative_to(source) not in generators.values()):
            seeds.add(p.relative_to(source))
    common = closure(source, seeds)
    common.update(p.relative_to(source) for p in (source / "arc_repl").rglob("*.rkt") if not set(p.parts) & SKIP)
    for rel in list(common):
        for parent in rel.parents:
            if (source / parent / "__init__.py").is_file():
                common.add(parent / "__init__.py")
    common.add(Path("scripts/run_generator_battery.sh"))
    for rel in sorted(common - set(generators.values())):
        target = Path("shared/tools") / rel.relative_to("scripts") if rel.parts[0] == "scripts" else Path("shared/runtime") / rel
        copy(rel, target, rel)

    data = {Path("data/canonical/puzzles.jsonl"), Path("data/canonical/puzzle_db.jsonl")}
    data.update(p.relative_to(source) for p in (source / "data/base/solutions").rglob("*.json"))
    data.update(p.relative_to(source) for p in (source / "data/raw").glob("*.json"))
    for name in ("kimi_generator_assignment.jsonl", "kimi_generator_reviews.jsonl", "generator_associated_notes.jsonl",
                 "head_frequency.jsonl", "dsl_vocab.json", "generator_difficulty.jsonl", "generator_blacklist.json", "generator_graylist.json"):
        rel = Path("data/derived") / name
        if (source / rel).is_file():
            data.add(rel)
    for rel in sorted(data):
        copy(rel, Path("shared") / rel, rel)
    for p in sorted((source / "GUIDE").rglob("*")):
        if p.is_file() and not set(p.parts) & SKIP:
            copy(p.relative_to(source), p.relative_to(source), p.relative_to(source))
    for p in sorted((source / "tests").glob("test_*.py")):
        match = re.match(r"test_generator_([0-9a-f]{8,12})\.py$", p.name)
        if match and match[1] in generators:
            copy(p.relative_to(source), Path("generators") / match[1] / "tests" / p.name, p.relative_to(source))
        elif any(term in p.name for term in ("generator", "canonical_profile", "authority_sync", "grammar_gate", "rule_smoke")):
            copy(p.relative_to(source), Path("shared/tests") / p.name, p.relative_to(source))
    for name in ("PUZZLE_GENERATOR_SPEC.md", "ARC_GENERATOR_CONTRACT.md", "RACKET_DSL.md", "CONVENTIONS.md"):
        rel = Path("docs") / name
        if (source / rel).is_file():
            copy(rel, Path("docs/reference") / name)
    write(Path("catalog/puzzles.jsonl"), "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))
    write(Path("catalog/runtime_files.json"), json.dumps(mappings, indent=2) + "\n")
    authority_index = {}
    for item in mappings:
        if item["target"].startswith("data/base/solutions/"):
            row = json.loads((dest / item["path"]).read_text())
            if row.get("task_id"):
                authority_index[item["target"]] = row["task_id"]
    write(Path("catalog/authority_files.json"), json.dumps(authority_index, indent=2) + "\n")
    def git(*argv):
        return subprocess.run(["git", "-C", str(source), *argv], check=True, capture_output=True, text=True).stdout.strip()
    report = {"schema": "arcpuzzles-import-v1", "source_repository": str(source),
              "source_commit": git("rev-parse", "HEAD"), "source_status": git("status", "--porcelain=v1"),
              "copied_files": copied, "derived_files": derived,
              "generator_count": len(generators), "catalog_count": len(records),
              "exclusions": ["caches", "live databases", "training runs/weights", "bulk review archives",
                             "LLM authoring client", "legacy SQLite catalog"], "status": "copied; runtime verification separate"}
    (dest / "docs/migration/import-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"generators": len(generators), "records": len(records), "copied_files": len(copied),
                      "copied_bytes": sum(r["bytes"] for r in copied), "derived_files": len(derived)}, indent=2))


if __name__ == "__main__":
    main()
