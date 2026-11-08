"""Exhaustively select compact slots for the existing 16-slot code/gray cycle.

There are only 12 meaningful position pairs: the locations of code 1 and code 3.
Codes 2 and 4 are interchangeable for these schedule constraints. This searches
compact counts 8..10; fewer than eight cannot show both gray states for four
codes. No generator source or literal solution table is imported.
"""
from itertools import combinations, permutations
import json
from pathlib import Path

WINDOWS = [{(start + k) % 16 for k in range(8)} for start in range(16)]
rows = []
for position1 in range(4):
    for position3 in range(4):
        if position1 == position3:
            continue
        anchors = {5*position for position in range(4) if position != position1}
        # Gray/non-3 slots refute the new rival exactly when made compact.
        refutable = {slot for slot in range(16) if slot % 4 != position3
                     and bool((slot // 4) % 2 ^ (slot % 4) % 2)}
        eligible = [slot for slot in range(16) if slot not in anchors]
        populations = []
        for compact_count in (8, 9, 10):
            solutions = []
            for expanded in combinations(eligible, 16-compact_count):
                ex = set(expanded)
                # Same code and gray state recur eight slots later. Both must
                # not be expanded if compact scenes are to show that state.
                if any((slot+8) % 16 in ex for slot in ex):
                    continue
                if any(len(window & ex) < 2
                       or len((window & refutable)-ex) < 2 for window in WINDOWS):
                    continue
                solutions.append(expanded)
            populations.append({"compact_count": compact_count, "solution_count": len(solutions)})
            if solutions:
                rows.append({"code_1_position": position1, "code_3_position": position3,
                             "compact_count": compact_count, "expanded_slots": solutions[0],
                             "solution_count": len(solutions), "searched_populations": populations})
                break

assert len(rows) == 12 and all(row["compact_count"] == 10 for row in rows)
table = {(row["code_1_position"], row["code_3_position"]): set(row["expanded_slots"])
         for row in rows}
order_checks = []
for order in permutations((1, 2, 3, 4)):
    expanded = table[(order.index(1), order.index(3))]
    states = {code: set() for code in order}
    anchors = []
    compact_refutations = set()
    for slot in range(16):
        block, position = divmod(slot, 4)
        code = order[position]
        gray = bool((block % 2) ^ (position % 2) ^ (code == 3))
        if block == position and code != 1:
            anchors.append(slot)
            assert slot not in expanded
        if slot not in expanded:
            states[code].add(gray)
            if gray and code != 3:
                compact_refutations.add(slot)
    assert len(anchors) == 3
    assert all(state == {False, True} for state in states.values())
    minimum_expanded = min(len(window & expanded) for window in WINDOWS)
    minimum_compact_refutations = min(len(window & compact_refutations) for window in WINDOWS)
    assert minimum_expanded >= 2 and minimum_compact_refutations >= 2
    order_checks.append({"order": order, "canonical_slots": anchors,
                         "minimum_expanded_per_eight": minimum_expanded,
                         "minimum_compact_gray_non3_per_eight": minimum_compact_refutations})

report = {
    "constraints": ["3 canonical anchors retained", "both compact gray states per code",
                    "at least 2 expanded in every cyclic 8", "at least 2 compact-gray/non3 in every cyclic 8"],
    "minimal_compact_count_in_this_schedule_class": 10,
    "rows": rows,
    "code_orders_checked": 24,
    "order_checks": order_checks,
    "limits": "This finite combinatorial proof concerns the existing code/gray cycle. Actual generated patterns and reference outputs are checked separately.",
}
out = Path.cwd().parent / "checks/final-code-review/schedule-search.json"
out.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"position_pairs": len(rows), "code_orders_checked": len(order_checks),
                  "minimal_compact_count": 10,
                  "minimum_expanded_per_eight": min(row["minimum_expanded_per_eight"] for row in order_checks),
                  "minimum_compact_gray_non3_per_eight": min(row["minimum_compact_gray_non3_per_eight"] for row in order_checks)}, indent=2))
