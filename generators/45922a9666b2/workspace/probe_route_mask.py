"""Exhaust the fixed profiles' alternative decompositions of published route masks.

This proves a narrowly scoped structural fact, not general lesson identifiability.
Run through the packet's standard review.py run wrapper; no Racket or labels are
needed because this checks finite monotone path geometry on the selected source.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys


# Locate only an ancestor's runtime; neither cwd nor another checkout is used.
for ancestor in Path(__file__).resolve().parents:
    candidates = (ancestor / "shared/runtime", ancestor)
    dependency = next((p for p in candidates if (p / "reviewer_support.py").is_file()), None)
    if dependency is not None:
        sys.path.insert(0, str(dependency))
        break
else:
    raise ImportError("No local reviewer_support runtime in this source tree")

from reviewer_support import find_root, load_selected_generator


TASK_ID = "45922a9666b2"


def enumerate_role_paths(height, width, role, route_union):
    """Every up/right path within the mask with this role's exact invariants."""
    count, stop, terminal_row = role
    found = []

    def walk(cells, turns):
        row, col = cells[-1]
        if row == terminal_row and turns == count:
            found.append((tuple(cells), stop))
            return
        if row > terminal_row and (row - 1, col) in route_union:
            walk(cells + [(row - 1, col)], turns)
        # The rule stops on reaching row zero; no horizontal top-row move.
        if row > 0 and turns < count and (row, col + 1) in route_union:
            walk(cells + [(row, col + 1)], turns + 1)

    for col in range(width):
        if (height - 1, col) in route_union:
            walk([(height - 1, col)], 0)
    return found


def probe_profile(generator, profile):
    height, width, roles, gray_count = generator._profile_role_signature(profile)
    canonical = generator._profile_signature(profile)[4]
    route_union = {cell for cells, _stop in canonical for cell in cells}
    role_options = [enumerate_role_paths(height, width, role, route_union) for role in roles]
    valid = []
    for paths in itertools.product(*role_options):
        starts = tuple(cells[0][1] for cells, _stop in paths)
        if not all(left < right for left, right in zip(starts, starts[1:])):
            continue
        if not generator._starts_fit(starts, roles, width):
            continue
        constraints = generator._constraints_for_paths(paths)
        if constraints is None:
            continue
        open_cells, critical_gray = constraints
        # The renderer must be able to meet the profile's total gray count.
        if not len(critical_gray) <= gray_count <= height * width - len(open_cells):
            continue
        if set(open_cells) != route_union:
            continue
        valid.append(paths)
    noncanonical = sum(paths != canonical for paths in valid)
    if len(valid) != 1 or noncanonical != 0:
        raise AssertionError(f"{profile}: published mask has an alternative legal decomposition")
    expected_size = sum(height - terminal_row + turns for turns, _stop, terminal_row in roles)
    if expected_size != len(route_union):
        raise AssertionError(f"{profile}: disjoint fixed-role cardinality invariant failed")
    return {"profile": profile, "dimensions": [height, width],
            "roles": roles, "route_union_size": len(route_union),
            "role_path_option_counts": [len(options) for options in role_options],
            "candidate_decomposition_count": len(list(itertools.product(*role_options))),
            "valid_same_mask_decomposition_count": len(valid),
            "noncanonical_same_mask_decomposition_count": noncanonical}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = find_root(__file__)
    generator, source, source_hash = load_selected_generator(TASK_ID, root=root)
    results = [probe_profile(generator, profile) for profile in generator.SCENE_PROFILES]
    output = args.output.resolve()
    argv = [sys.executable, str(Path(__file__).resolve()), "--output", str(output)]
    packet = root.parents[1]
    receipt = {"schema": "walker-template-structure-v1", "status": "passed",
               "task_id": TASK_ID, "generator_version": generator.VERSION,
               "generator_rule_hash": generator.RULE_HASH,
               "generator_source": str(source), "generator_sha256": source_hash,
               "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "command_argv": argv, "cwd": str(Path.cwd()),
               "wrapper_command_argv": [str(packet / "WORK/.venv/bin/python"),
                    str(packet / "review.py"), "run", *argv],
               "wrapper_cwd": str(packet), "profiles": results,
               "reasoning": [
                   "Every role fixes its path cardinality to height - terminal_row + turn_count.",
                   "Routes are disjoint, so their union cardinality equals the sum of those fixed cardinalities.",
                   "Equality with the published-mask rival requires every published-mask cell to be in the actual path union; initial red starts already belong to that union.",
                   "Equal cardinality then forces equal unions; exhaustive mask-confined enumeration finds only the canonical decomposition for each profile.",
                   "Consequently every valid procedural layout disagrees with the published-mask rival, independently of nuisance gray placement.",
                   "The default period-six schedule contains at most one canonical layout in four consecutive draws; holding out any one draw leaves at least two procedural demonstrations."],
               "limits": [
                   "Bound to the exact selected generator source hash and its four fixed published role profiles.",
                   "Uses the selected generator's role, start-fit, and blocker-constraint definitions; does not independently establish their intended domain.",
                   "Checks every relevant same-mask path decomposition, not all gray textures or all possible alternative rules.",
                   "Schedule reasoning requires default layout selection and consecutive indices; explicit overrides and arbitrary nonconsecutive lessons are excluded.",
                   "No Racket execution, broad identifiability, training admission, or private/blind puzzle claim."]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "profiles": len(results), "output": str(output)}))


if __name__ == "__main__":
    main()
