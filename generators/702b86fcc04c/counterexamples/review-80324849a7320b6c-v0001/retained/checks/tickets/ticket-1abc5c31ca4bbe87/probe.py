#!/usr/bin/env python3
"""One bounded horizontal-isolation shortcut probe; source and rule remain unchanged."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "702b86fcc04c"
TICKET = "ticket-1abc5c31ca4bbe87"
PINNED_SEED = "116104b011645043cd294171a25f332c419022e6df828c1ebb77696beb6c2ad4"
PINNED_SOURCE = "3c8f591a1a54b6a7f39887ca74493513291942110c44b7509e98f73dc303975e"
PINNED_RULE = "17282641828d"
OUT = Path(__file__).resolve().parent


def save(name, value):
    (OUT / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def horizontal_isolation_rival(grid):
    output = deepcopy(grid)
    width = len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2 and (c == 0 or row[c-1] != 2) and (c+1 == width or row[c+1] != 2):
                output[r][c] = 3
    return output


def documented_domain(grid):
    """Independently check the documented singleton separation and larger distractor."""
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    components = []
    while cells:
        seed = min(cells)
        cells.remove(seed)
        component = [seed]
        stack = [seed]
        while stack:
            r, c = stack.pop()
            for adjacent in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if adjacent in cells:
                    cells.remove(adjacent)
                    stack.append(adjacent)
                    component.append(adjacent)
        components.append(component)
    singletons = [component[0] for component in components if len(component) == 1]
    separated = all(
        all(grid[rr][cc] == 0
            for rr in range(max(0, r-1), min(len(grid), r+2))
            for cc in range(max(0, c-1), min(len(grid[0]), c+2))
            if (rr,cc) != (r,c))
        for r,c in singletons)
    return {"component_sizes": sorted(map(len, components)),
            "singleton_count": len(singletons),
            "larger_component_count": sum(len(c) > 1 for c in components),
            "singletons_separated_from_every_other_nonzero_cell": separated,
            "documented_invariants_hold": bool(singletons) and any(len(c) > 1 for c in components) and separated}


def main():
    started = time.monotonic()
    root = find_root(__file__)
    generator, source_path, source_sha = load_selected_generator(TASK, root=root)
    assert source_sha == PINNED_SOURCE, (source_sha, PINNED_SOURCE)
    seed = int(PINNED_SEED[:16], 16)
    demos = [generator.generate(seed, i) for i in range(4)]
    query = generator.generate(seed, 4, grid_h=8, grid_w=8)
    # Change only the orientation and placement of the larger red distractor.
    # Both existing red singletons and the nonred distractor remain.
    query[1][4] = query[1][5] = 0
    query[3][1] = query[4][1] = 2
    inputs = demos + [query]
    canonical = canonical_pairs(TASK, root=root)
    for grid in inputs:
        assert generator.self_check(grid) == []
        assert documented_domain(grid)["documented_invariants_hold"]
    receipt = Catalog(root).apply(TASK, inputs + [p["input"] for p in canonical],
                                  timeout=90, check_generator_domain=True)
    save("racket.json", receipt)
    assert receipt["generator_sha256"] == PINNED_SOURCE
    assert receipt["executed_rule_hash"] == PINNED_RULE
    assert receipt["rule_hash_matches_catalog"]
    labels = [item["output"] for item in receipt["results"]]
    assert all(label is not None for label in labels)
    reference = labels[4]
    rival = horizontal_isolation_rival(query)
    differences = [{"row":r, "column":c, "reference":reference[r][c], "rival":rival[r][c]}
                   for r in range(len(query)) for c in range(len(query[0]))
                   if reference[r][c] != rival[r][c]]
    demo_agreements = [horizontal_isolation_rival(g) == y for g,y in zip(demos,labels)]
    assert all(demo_agreements)
    assert differences == [{"row":3,"column":1,"reference":2,"rival":3},
                           {"row":4,"column":1,"reference":2,"rival":3}]
    canonical_reference_matches = [p["output"] == y for p,y in zip(canonical,labels[5:])]
    assert all(canonical_reference_matches)
    canonical_rival_matches = [horizontal_isolation_rival(p["input"]) == y
                               for p,y in zip(canonical,labels[5:])]
    witness = {"task_id":TASK, "source_sha256":source_sha,
               "executed_rule_hash":PINNED_RULE, "ticket_seed":PINNED_SEED,
               "generation_seed":seed, "demonstration_indices":[0,1,2,3],
               "query_construction":"generate(seed,4,grid_h=8,grid_w=8); clear (1,4),(1,5); set (3,1),(4,1) to2",
               "rival":"Recolor red cells with no horizontal red neighbor, ignoring vertical neighbors.",
               "train":[{"input":g,"output":y} for g,y in zip(demos,labels[:4])],
               "query":{"input":query,"output":reference,"rival_output":rival},
               "query_domain":documented_domain(query),
               "query_self_check":generator.self_check(query),
               "differences":differences}
    save("witness.json", witness)
    result = {"schema":"arcpuzzles-bounded-adversarial-witness-v1",
              "ticket_id":TICKET, "task_id":TASK, "status":"finding",
              "source_sha256":source_sha, "rule_hash":PINNED_RULE,
              "probe_seconds":round(time.monotonic()-started,4),
              "targeted_probes":1, "executed_labels":len(labels),
              "demo_agreements":demo_agreements,
              "query_domain":documented_domain(query),
              "query_differing_cells":differences,
              "canonical_label_matches":sum(canonical_reference_matches),
              "canonical_pairs":len(canonical),
              "canonical_rival_matches":sum(canonical_rival_matches),
              "scope":"Generated-demonstration shortcut, not a canonical-fitting rival or a label error.",
              "limits":["One constructed lawful query, four ordinary demonstrations; no prevalence estimate.",
                        "The current sampler cannot emit a vertical red distractor; this is a distribution coverage gap.",
                        "No target edits, audit clearance, approval change or training admission."]}
    save("result.json", result)
    save("outcome.json", {"ticket_id":TICKET,"type":"adversarial_witness","status":"finding",
          "summary":"A horizontal-isolation shortcut matches four ordinary generated demonstrations but fails on a lawful vertical two-cell red distractor. Actual Racket preserves both red cells; rival recolors both. The query satisfies both documented invariants and self_check. Rival fits 4/5 canonical pairs, so this is a generated-distribution coverage finding, not a canonical-fitting ambiguity.",
          "evidence_paths":[f"checks/tickets/{TICKET}/result.json",f"checks/tickets/{TICKET}/witness.json",
                            f"checks/tickets/{TICKET}/racket.json",f"checks/tickets/{TICKET}/probe.py",
                            f"checks/tickets/{TICKET}/command.json"],
          "elapsed_minutes":None})
    print(json.dumps(result,sort_keys=True))


if __name__ == "__main__":
    main()
