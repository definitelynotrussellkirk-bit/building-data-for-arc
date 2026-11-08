"""Read-only puzzle queries and evidence-based approval filters."""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
from typing import Any


def library_root(root: str | Path | None = None) -> Path:
    """Locate this checkout or its installed, bundled library."""
    if root is not None or os.environ.get("ARCPUZZLES_HOME"):
        candidate = Path(root or os.environ["ARCPUZZLES_HOME"]).resolve()
    else:
        installed = Path(__file__).resolve().parent / "library"
        checkout = Path(__file__).resolve().parents[2]
        candidate = installed if (installed / "catalog/puzzles.jsonl").is_file() else checkout
    if not (candidate / "catalog/puzzles.jsonl").is_file():
        raise FileNotFoundError(f"No ARCpuzzles catalog at {candidate}; pass --library or ARCPUZZLES_HOME")
    return candidate


def local_path(root: Path, relative: str) -> Path:
    """Resolve a manifest path without allowing traversal or external symlinks."""
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"Invalid library-relative path: {relative!r}")
    result = root / rel
    if not result.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes library: {relative!r}")
    return result


def jsonl(path: Path) -> list[dict[str, Any]]:
    result = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{number}: expected an object")
            result.append(row)
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Catalog:
    """An independent local library. Querying never imports generator code."""

    def __init__(self, root: str | Path | None = None):
        self.root = library_root(root)
        self._records: dict[str, dict] = {}
        self._aliases: dict[str, set[str]] = defaultdict(set)
        for row in jsonl(self.root / "catalog/puzzles.jsonl"):
            tid = row["id"]
            if not isinstance(tid, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", tid):
                raise ValueError(f"Invalid catalog ID: {tid!r}")
            if tid in self._records:
                raise ValueError(f"Duplicate catalog ID: {tid}")
            self._records[tid] = row
            for alias in row.get("aliases", []):
                self._aliases[alias].add(tid)
        aliases_file = self.root / "catalog/aliases.json"
        if aliases_file.is_file():
            for alias, targets in json.loads(aliases_file.read_text()).items():
                for tid in targets:
                    if tid not in self._records:
                        raise ValueError(f"Alias {alias!r} targets an unknown puzzle: {tid}")
                    self._aliases[alias].add(tid)
                    if alias not in self._records[tid].setdefault("aliases", []):
                        self._records[tid]["aliases"].append(alias)
        self._canonical: dict[str, list[dict]] | None = None
        self._canonical_stamp: tuple[int, int] | None = None

    def _variants(self) -> dict[str, list[dict]]:
        path = self.root / "shared/data/canonical/puzzles.jsonl"
        stat = path.stat()
        stamp = (stat.st_mtime_ns, stat.st_size)
        if self._canonical is None or self._canonical_stamp != stamp:
            index: dict[str, list[dict]] = defaultdict(list)
            for row in jsonl(path):
                index[row["task_id"]].append(row)
            self._canonical = dict(index)
            self._canonical_stamp = stamp
        return self._canonical

    def resolve(self, task_id: str) -> str:
        """Resolve an exact ID or an unambiguous recorded alias."""
        if task_id in self._records:
            return task_id
        matches = self._aliases.get(task_id, set())
        if len(matches) == 1:
            return next(iter(matches))
        if matches:
            raise ValueError(f"Ambiguous alias {task_id!r}: {', '.join(sorted(matches))}")
        raise KeyError(f"Unknown puzzle: {task_id}")

    def describe(self, task_id: str) -> dict[str, Any]:
        """Metadata plus approval derived from current implementation bytes."""
        row = deepcopy(self._records[self.resolve(task_id)])
        path = local_path(self.root, row["generator"]) if row.get("generator") else None
        row["has_generator"] = bool(path and path.is_file())
        row["notes_path"] = f"generators/{row['id']}/notes.md"
        row["review_notes_path"] = f"generators/{row['id']}/evidence/review_index.json"
        row["counterexamples_path"] = f"generators/{row['id']}/counterexamples"
        from .review_notes import audit_state
        state = audit_state(self.root, row["id"])
        for field in ("audit_unresolved", "audit_unresolved_count", "audit_pending_triage_count"):
            row[field] = state[field]
        row["generator_sha256"] = sha256(path) if row["has_generator"] else None
        reasons = []
        if row.get("train_safety") != "reviewed_safe":
            reasons.append("not_reviewed_safe")
        if row.get("semantic_veto"):
            reasons.append("active_semantic_veto")
        weight = row.get("mix_weight", 0)
        if not isinstance(weight, (int, float)) or not math.isfinite(weight) or weight <= 0:
            reasons.append("nonpositive_mix_weight")
        if not row["has_generator"]:
            reasons.append("missing_generator")
        elif not row.get("reviewed_generator_sha256"):
            reasons.append("missing_reviewed_generator_hash")
        elif row["generator_sha256"] != row["reviewed_generator_sha256"]:
            reasons.append("generator_changed_since_review")
        rules = [r.get("program_solution") for r in self._variants().get(row.get("rule_task_id", row["id"]), [])
                 if isinstance(r.get("program_solution"), str) and r["program_solution"].strip()]
        if not rules:
            reasons.append("no_canonical_rule")
            row["rule_hash"] = None
        else:
            hashes = {hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12] for rule in rules}
            row["rule_hash"] = hashlib.sha256(" ".join(rules[0].split()).encode()).hexdigest()[:12]
            if len(hashes) > 1:
                reasons.append("ambiguous_canonical_rule")
            if not row.get("reviewed_rule_hash"):
                reasons.append("missing_reviewed_rule_hash")
            elif row["rule_hash"] != row["reviewed_rule_hash"]:
                reasons.append("rule_changed_since_review")
        row["approved"] = not reasons
        row["approval_reasons"] = reasons
        return row

    def query(self, *, approved: bool | None = None, source: str | None = None,
              skill: str | None = None, primitive: str | None = None,
              difficulty: str | None = None, kind: str | None = None,
              train_safety: str | None = None, search: str | None = None,
              has_generator: bool | None = None, family: str | None = None,
              audit_unresolved: bool | None = None,
              split: str | None = None, limit: int | None = None, offset: int = 0,
              sample: int | None = None, seed: int = 0) -> list[dict[str, Any]]:
        """Combine filters with AND; sort by ID, then sample/page deterministically."""
        for name, value in (("limit", limit), ("offset", offset), ("sample", sample)):
            if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
                raise ValueError(f"{name} must be a nonnegative integer")
        if kind is not None and kind not in {"per_puzzle", "generic"}:
            raise ValueError("kind must be per_puzzle or generic")
        result = []
        for tid, raw in sorted(self._records.items()):
            if source and not any(v == source or v.startswith(source + ":") for v in raw.get("sources", [])):
                continue
            if skill and skill.casefold() not in {v.casefold() for v in raw.get("skills", [])}:
                continue
            if primitive and primitive not in raw.get("primitives", []):
                continue
            if difficulty and difficulty.lower() not in raw.get("difficulties", []):
                continue
            if any(value is not None and raw.get(name) != value for name, value in
                   (("kind", kind), ("train_safety", train_safety), ("family", family), ("split", split))):
                continue
            if search and search.casefold() not in " ".join([tid, raw.get("summary", ""), *raw.get("skills", [])]).casefold():
                continue
            row = self.describe(tid)
            if audit_unresolved is not None and row["audit_unresolved"] != audit_unresolved:
                continue
            if approved is not None and row["approved"] != approved:
                continue
            if has_generator is not None and row["has_generator"] != has_generator:
                continue
            result.append(row)
        if sample is not None:
            result = random.Random(seed).sample(result, min(sample, len(result)))
        return result[offset:] if limit is None else result[offset:offset + limit]

    def get(self, task_id: str) -> dict[str, Any]:
        """Authoring view including reference solutions and all canonical variants."""
        row = self.describe(task_id)
        row["variants"] = deepcopy(self._variants().get(row["id"], []))
        notes = self.root / "generators" / row["id"] / "evidence/associated_notes.jsonl"
        row["associated_notes"] = jsonl(notes) if notes.is_file() else []
        home = self.root / "generators" / row["id"]
        for name, field in (("SUMMARY.md", "summary_markdown"), ("notes.md", "working_notes")):
            path = local_path(self.root, (home / name).relative_to(self.root).as_posix())
            row[field] = path.read_text(encoding="utf-8") if path.is_file() else None
        # One editable source, with the old field retained for existing consumers.
        row["notes"] = row["working_notes"] or ""
        return row

    def lineage(self, task_id: str) -> dict[str, Any]:
        """Verified official family mapping, invalidated by changed source bytes."""
        row = self.describe(task_id)
        path = self.root / "shared/data/derived/official_generator_lineage.jsonl"
        matches = [r for r in jsonl(path) if r.get("generator_id") == row["id"]] if path.is_file() else []
        reasons = []
        if len(matches) != 1:
            return {"verified": False, "family_id": None, "reasons": ["missing_or_ambiguous_lineage"]}
        evidence = matches[0]
        if evidence.get("mapping_status") != "verified":
            reasons.append("mapping_not_verified")
        if evidence.get("source_hashes", {}).get("generator_sha256") != row["generator_sha256"]:
            reasons.append("lineage_generator_hash_changed")
        split, original_id = evidence.get("source_split"), evidence.get("source_task_id")
        if split not in {"training", "evaluation"} or not isinstance(original_id, str) or not re.fullmatch(r"[0-9a-f]{8}", original_id):
            reasons.append("invalid_official_identity")
        if original_id not in row.get("aliases", []) and split == "training":
            reasons.append("lineage_alias_disagrees")
        return {"verified": not reasons, "family_id": f"official:{split}:{original_id}",
                "source_split": split, "source_task_id": original_id,
                "reasons": reasons, "evidence": deepcopy(evidence)}

    def challenge(self, task_id: str, *, variant: int = 0) -> dict[str, Any]:
        """Only demonstration pairs and query inputs, with no rule/answer metadata."""
        tid = self.resolve(task_id)
        variants = self._variants().get(tid, [])
        if not isinstance(variant, int) or isinstance(variant, bool) or not 0 <= variant < len(variants):
            raise ValueError(f"variant must be between 0 and {len(variants) - 1}; this puzzle has {len(variants)} variants")
        row = variants[variant]
        def pairs(value):
            return value if isinstance(value, list) else [value] if isinstance(value, dict) else []
        def grid(value):
            if isinstance(value, list) and value and all(isinstance(r, str) for r in value):
                value = [[int(c) for c in r] for r in value]
            if (not isinstance(value, list) or not 1 <= len(value) <= 30
                    or not all(isinstance(r, list) for r in value)
                    or not 1 <= len(value[0]) <= 30
                    or any(len(r) != len(value[0]) for r in value)
                    or any(type(c) is not int or not 0 <= c <= 9 for r in value for c in r)):
                raise ValueError(f"{tid}: variant {variant} contains a malformed grid")
            return deepcopy(value)
        training, queries = pairs(row.get("train")), pairs(row.get("test"))
        if (any(not isinstance(p, dict) or not {"input", "output"} <= p.keys() for p in training)
                or any(not isinstance(p, dict) or "input" not in p for p in queries)):
            raise ValueError(f"{tid}: selected variant contains malformed pairs")
        result = {"id": tid, "variant": variant,
                "train": [{"input": grid(p["input"]), "output": grid(p["output"])}
                          for p in training],
                "test": [{"input": grid(p["input"])} for p in queries]}
        if not result["train"] or not result["test"]:
            raise ValueError(f"{tid}: selected variant has no concrete demonstration/query pairs")
        return result

    def stats(self) -> dict[str, Any]:
        """Current counts; approval labels are not fresh quality measurements."""
        records = self.query()
        return {"puzzles": len(records), "generators": sum(r["has_generator"] for r in records),
                "canonical_rows": sum(r["canonical_rows"] for r in records),
                "approved": sum(r["approved"] for r in records),
                "train_safety": dict(Counter(r["train_safety"] for r in records)),
                "kinds": dict(Counter(r["kind"] for r in records)),
                "sources": dict(Counter(s for r in records for s in {v.split(":")[0] for v in r["sources"]})),
                "not_approved_reasons": dict(Counter(reason for r in records for reason in r["approval_reasons"]))}

    def generate(self, task_id: str, **options) -> list[dict[str, Any]]:
        """Generate Racket-verified episodes; unapproved generators require opt-in."""
        from .runtime import generate
        return generate(self, task_id, **options)

    def parametric_status(self, task_id: str) -> dict[str, Any]:
        """Inspect exact-source acceptance of a parameterized rule family."""
        from .parametric_promotion import status
        return status(self, task_id)

    def generate_parametric(self, task_id: str, **options) -> list[dict[str, Any]]:
        """Use an accepted variant, checking every label through protected Racket."""
        from .parametric_promotion import generate
        return generate(self, task_id, **options)

    def export_parametric(self, task_id: str, output: str | Path, **options) -> dict[str, Any]:
        """Export accepted parameter episodes with separate public/private files."""
        from .parametric_promotion import export
        return export(self, task_id, output, **options)

    def apply(self, task_id: str, inputs: list, **options) -> dict[str, Any]:
        """Run a task's reference rule on hand-made grids for audit evidence."""
        from .runtime import apply_rule
        return apply_rule(self, task_id, inputs, **options)

    def check(self, task_id: str, **options) -> dict[str, Any]:
        """Run an inherited stage or battery, retaining its real result."""
        from .runtime import check
        return check(self, task_id, **options)

    def export(self, output: str | Path, *, count: int, **options) -> dict[str, Any]:
        """Export a bounded, hashed dataset with separate public challenges and labels."""
        from .datasets import export_dataset
        return export_dataset(self, output, count=count, **options)
