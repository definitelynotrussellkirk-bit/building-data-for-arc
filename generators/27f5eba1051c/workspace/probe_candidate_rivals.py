"""Audit declared shortcut solvers against canonical pairs and lesson windows.

This is a reusable authoring probe.  It reads the generator's actual
``LESSON_COMPETITORS`` / ``CANONICAL_SHORTCUTS`` declarations rather than
copying rival names, checks declared canonical shortcuts against every usable
public pair, and exercises all four cyclic lesson start residues in each band.
Run it through ``run_with_racket.py`` from the packet root.
"""
from __future__ import annotations

from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from reviewer_support import canonical_pairs, find_root


def _load_generator():
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = spec_from_file_location("candidate_generator_27f5eba1051c", path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
RIVALS = dict(gen.LESSON_COMPETITORS)
SHORTCUTS = dict(gen.CANONICAL_SHORTCUTS)


def _canonical_report():
    root = find_root(__file__)
    pairs = canonical_pairs(gen.TASK_ID, root=root)
    fits = {
        name: all(rival(pair["input"]) == pair["output"] for pair in pairs)
        for name, rival in RIVALS.items()
    }
    declared = {
        name: all(shortcut(pair["input"]) == pair["output"] for pair in pairs)
        for name, shortcut in SHORTCUTS.items()
    }
    if declared and not all(declared.values()):
        raise AssertionError(
            "CANONICAL_SHORTCUTS contains a rule that does not fit every "
            f"canonical pair: {declared}"
        )
    print(f"[canonical] pairs={len(pairs)} competitor_fit={fits}")
    print(f"[canonical] declared_shortcuts={declared}")


def main():
    _canonical_report()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = {name: Counter() for name in RIVALS}
        profiles = Counter()
        starts = Counter()
        unique_inputs = set()
        for start in range(200):
            starts[start % len(gen.SCHEDULE_PROFILES)] += 1
            pairs = []
            seed = 910_000 + band_index * 10_000 + start
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(seed, start + offset, difficulty=band)
                output = gen.rule_mirror(grid)
                profiles[gen._inspect_scene(grid)["scene_profile"]] += 1
                unique_inputs.add(tuple(tuple(row) for row in grid))
                pairs.append({"input": grid, "output": output})
            demos = pairs[: gen.EXAMPLES_NEEDED]
            query = pairs[-1]
            for name, rival in RIVALS.items():
                fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
                agrees = rival(query["input"]) == query["output"]
                outcome = "refuted" if not fits else "survived_all" if agrees else "ambiguous"
                counts[name][outcome] += 1
        print(
            f"[{band}] starts={dict(starts)} unique_inputs={len(unique_inputs)}/1000 "
            f"profiles={dict(profiles)}"
        )
        for name, counter in counts.items():
            print(f"  {name}: {dict(counter)}")
        survivors = {
            name: dict(counter)
            for name, counter in counts.items()
            if counter["survived_all"] or counter["ambiguous"]
        }
        if survivors:
            raise AssertionError(f"declared rivals survived {band} lessons: {survivors}")


if __name__ == "__main__":
    main()
