#!/usr/bin/env python3
"""Run the official semantic gate on 100+ real lessons per difficulty band.

The probe stages the selected task with ``arcpuzzles.runtime.prepare_runtime``
so imports, the canonical authority, and lesson assembly are byte-bound to the
current repository snapshot.  It then runs the official semantic gate with all
strict opt-in checks and separately replays the exact lesson draw plan to count
unique inputs and schedule coverage without storing a large duplicate corpus.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

TASK_ID = "fe0dc9f32b7b"
GENERATOR_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = GENERATOR_HOME.parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arcpuzzles import Catalog  # noqa: E402
from arcpuzzles.runtime import prepare_runtime, run_process  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _census_script(total_lessons: int) -> str:
    return f'''\
import hashlib
import importlib
import json
from scripts import generator_semantic_gate as gate

TASK_ID = {TASK_ID!r}
TOTAL = {total_lessons}
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{{TASK_ID}}.generator")
plan = gate._lesson_plan(
    TASK_ID,
    TOTAL,
    bands=gate.BANDS,
    pass_difficulty=True,
    legacy=False,
)
all_hashes = set()
by_band = {{band: {{"lessons": 0, "inputs": 0, "unique": set(),
                   "demo_profile_sequences": {{}}, "start_residues_mod3": {{}}}}
           for band in gate.BANDS}}
for band, seed, sample_index, axes in plan:
    row = by_band[band]
    row["lessons"] += 1
    sequence = []
    for offset in range(4):
        grid = gen.generate(seed, sample_index + offset, **axes)
        encoded = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
        digest = hashlib.sha256(encoded).hexdigest()
        all_hashes.add(digest)
        row["unique"].add(digest)
        row["inputs"] += 1
        sequence.append(gen.schedule_profile(seed, sample_index + offset,
                                             difficulty=axes.get("difficulty")))
    demos = tuple(sequence[:3])
    key = "|".join(demos)
    row["demo_profile_sequences"][key] = row["demo_profile_sequences"].get(key, 0) + 1
    residue = str(sample_index % 3)
    row["start_residues_mod3"][residue] = row["start_residues_mod3"].get(residue, 0) + 1

for row in by_band.values():
    row["unique_inputs"] = len(row.pop("unique"))

print(json.dumps({{
    "lesson_plan_source": "scripts.generator_semantic_gate._lesson_plan",
    "lesson_sample_stride": gate.LESSON_SAMPLE_STRIDE,
    "bands": list(gate.BANDS),
    "n_demos": 3,
    "n_queries": 1,
    "total_lessons": len(plan),
    "total_inputs": len(plan) * 4,
    "unique_inputs": len(all_hashes),
    "by_band": by_band,
    "declared_schedule_profiles": list(gen.SCHEDULE_PROFILES),
    "declared_lesson_competitors": sorted(gen.LESSON_COMPETITORS),
    "declared_canonical_shortcuts": sorted(gen.CANONICAL_SHORTCUTS),
    "axes": gen.AXES,
    "invariants": gen.INVARIANTS,
}}, sort_keys=True))
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--census-per-band", type=int, default=150)
    parser.add_argument("--timeout", type=float, default=4000)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.lessons_per_band < 1 or args.census_per_band < 1:
        parser.error("lesson and census counts must be positive")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    output = args.out.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    total_lessons = args.lessons_per_band * 3

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-lesson-probe-") as raw:
        stage = Path(raw)
        manifest = prepare_runtime(Catalog(REPO_ROOT), stage, TASK_ID)
        official_json = stage / "semantic-gate.json"
        gate_argv = [
            sys.executable,
            "scripts/generator_semantic_gate.py",
            TASK_ID,
            "--per-band",
            str(args.census_per_band),
            "--lessons",
            str(total_lessons),
            "--min-strict-frac",
            "1.0",
            "--strict",
            "--require-rival-witness",
            "--require-shortcut-counterexample",
            "--require-contract",
            "--json-out",
            str(official_json),
        ]
        gate_result = run_process(gate_argv, stage, timeout=args.timeout)

        census_path = stage / "lesson_census.py"
        census_path.write_text(_census_script(total_lessons), encoding="utf-8")
        census_argv = [sys.executable, census_path.name]
        census_result = run_process(census_argv, stage, timeout=min(args.timeout, 600))

        official = (
            json.loads(official_json.read_text(encoding="utf-8"))
            if official_json.is_file()
            else None
        )
        try:
            census = json.loads(census_result["stdout"])
            census_error = None
        except Exception as exc:
            census = None
            census_error = f"{type(exc).__name__}: {exc}"

        runtime_generator = (
            stage / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
        )
        report = {
            "schema": f"{TASK_ID}-source-bound-lesson-probe-v1",
            "task_id": TASK_ID,
            "status": "passed",
            "source_binding": {
                "generator_sha256": _sha256(runtime_generator),
                "local_generator_sha256": _sha256(GENERATOR_HOME / "generator.py"),
                "probe_sha256": _sha256(Path(__file__)),
                "runtime_manifest_sha256": _sha256(stage / "RUNTIME_MANIFEST.json"),
                "runtime_manifest_task_id": manifest.get("task_id"),
            },
            "sampler": {
                "official_function": "scripts.generator_semantic_gate._lesson_plan",
                "policy": (
                    "100 lessons per band by default; band-specific pinned SHA-256 "
                    "seeds; lesson k starts at sample_index k*11; runner.run_one "
                    "uses three consecutive demos plus one consecutive query"
                ),
                "lessons_per_band": args.lessons_per_band,
                "census_per_band": args.census_per_band,
            },
            "official_gate": official,
            "input_census": census,
            "execution": {
                "cwd": "prepared source-bound runtime",
                "gate_argv": gate_argv,
                "gate_exit_code": gate_result["exit_code"],
                "gate_timed_out": gate_result["timed_out"],
                "gate_stdout": gate_result["stdout"],
                "gate_stderr": gate_result["stderr"],
                "census_argv": census_argv,
                "census_exit_code": census_result["exit_code"],
                "census_timed_out": census_result["timed_out"],
                "census_stderr": census_result["stderr"],
                "census_parse_error": census_error,
            },
        }

        audit = None
        if official and official.get("audits"):
            audit = official["audits"][0]
        expected_per_band = args.lessons_per_band
        band_rows = ((audit or {}).get("lessons") or {}).get("per_band") or {}
        failures = []
        if gate_result["exit_code"] != 0 or gate_result["timed_out"]:
            failures.append("official semantic gate did not exit cleanly")
        if not audit or audit.get("status") != "PASS":
            failures.append("official semantic audit status was not PASS")
        for band in ("easy", "medium", "hard"):
            row = band_rows.get(band) or {}
            if row.get("materialized") != expected_per_band:
                failures.append(f"{band}: expected {expected_per_band} materialized lessons")
            if row.get("identifiable") != expected_per_band:
                failures.append(f"{band}: not every lesson was identifiable")
        if census_result["exit_code"] != 0 or census_result["timed_out"] or census is None:
            failures.append("lesson input census failed")
        elif census.get("total_lessons") != total_lessons:
            failures.append("lesson input census returned the wrong lesson count")
        if report["source_binding"]["generator_sha256"] != report["source_binding"]["local_generator_sha256"]:
            failures.append("staged generator hash differs from local final source")
        if failures:
            report["status"] = "failed"
            report["failures"] = failures

        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": report["status"],
            "output": str(output),
            "generator_sha256": report["source_binding"]["generator_sha256"],
            "lessons_per_band": args.lessons_per_band,
            "unique_inputs": (census or {}).get("unique_inputs"),
            "gate_exit_code": gate_result["exit_code"],
        }, indent=2))
        return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
