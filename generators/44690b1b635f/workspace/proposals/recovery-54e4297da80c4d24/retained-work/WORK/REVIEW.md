Task `44690b1b635f`, generator version `3.1.0`; recovery overlay for assignment `review-efb25880f190b5c1`.
Defect: v3.0.0 had correct labels but only 42 color-normalized role masks across all bands, enabling a finite template shortcut.
Repair: retained all public/fixed profiles and added a deterministic, structurally validated `procedural_maze` profile.
Reference rule: unchanged; canonical `RULE_HASH` remains `72a0e00e932b`.
Local checks: 29 full-suite tests passed (21 unique behavior checks plus the overlay-copy duplicate); Python compilation passed; independent BFS oracle covered all sampled procedural/fixed cases.
Diversity: every band produced 64/64 unique forced procedural wall topologies; default 800 draws produced 59 topologies and 548 exact inputs per band.
Parametric prototype: two 3-demo/4-query episodes, fixed settings, all three rivals distinguished, public/private export split verified.
Blind solve: previously frozen visible-only attempt passed 3/3 examples; recovered solver and notes are included for official replay.
Remaining blockers: official after battery, Racket execution, post-repair solve, allocation sample, two audits, and packet builder need the original extracted packet.
Acceptance: **needs attention** until `tools/replay_in_full_packet.py` completes the hash-bound full-packet replay and official checks.

## Implemented repair

The prior audit did not find incorrect Racket labels. It demonstrated that the
source selected one of 16 fixed role masks per band and then varied only two
marker colors. The replacement does not weaken validation or discard canonical
anchors. It adds a single profile whose wall layout is a perfect maze generated
from a keyed DFS spanning tree. Recognition is structural rather than
provenance-based:

- perimeter cells must remain walls;
- every odd/odd interior room must be open;
- every even/even interior cell must remain a wall;
- traversable cells must be connected;
- the traversable graph must have exactly `vertices - 1` edges;
- the role mask must contain one singleton marker and exactly three arm markers.

Opening a closed connector creates a cycle and is rejected. Opening an
even/even wall is rejected. Closing a required connector disconnects the graph
and is rejected. The canonical BFS mirror still determines all outputs.

## Findings and status

| ID | Affected path | Evidence | Patch status | Result |
| --- | --- | --- | --- | --- |
| R1 | `generators/44690b1b635f/generator.py` | `checks/recovery/diversity-census.json` | repaired | 64/64 unique forced topologies per band |
| R2 | procedural recognizer | `tests/test_procedural_maze_diversity.py` | repaired | cycle/even-even mutations rejected |
| R3 | rule mirror | same focused test | unchanged | independent BFS oracle matched |
| P1 | `workspace/parametric/` | `evidence/private/manifest.json` | proposed only | 2 settings × 4 distinct queries; Python labels pass |
| T1 | large-packet recovery | `tools/replay_in_full_packet.py` tests | tooling supplied | wrong preimage refused; valid overlay backed up and applied atomically |
| B1 | official packet-only gates | `AUDIT.md`, `RESULTS.json` | open | no unsupported pass claimed |

## Checks actually run

From the recovery repository root:

```bash
PYTHONPATH=. pytest -q tests/test_role_topology_diversity.py
# 8 passed
PYTHONPATH=. pytest -q tests/test_parametric_prototype.py tests/test_replay_tool.py
# 11 passed
PYTHONPATH=. pytest -q tests/test_allocation_sampler.py
# 2 passed
PYTHONPATH=. pytest -q
# 29 passed (the task-local overlay test duplicates the 8 focused generator cases)
python -m py_compile <changed Python files>
# pass
```

The final combined run and its complete log are retained under
`checks/recovery/`. Source hashes and command records are in `RESULTS.json`.

## Parametric assessment

The prototype exposes two small bounded axes. `neighbor_mode=cardinal` versus
`king` changes the graph traversed; `phase=0` versus `1` swaps which role color
fills each distance parity. The canonical setting is `cardinal,0`, whose
normalized Racket hash is exactly `72a0e00e932b`. Each retained episode fixes
one setting across three demonstrations and four queries. Demonstrations reject
all three competing settings, every query is distinct and differs from at least
one rival, and public exports omit settings, programs, and query answers.

The alternate Racket programs have been materialized and hashed but not run in
this recovery environment. They remain **proposed** and must not be admitted or
approved until the full packet executes each program against its retained
private labels.

## Blind-solve recovery

The mandatory blind task was completed before the repair source was opened. The
visible-only hypothesis marks a candidate panel when its occupied coordinates
form a nonempty subset of the cells added from the first reference panel to the
second. It passed all three visible examples and predicted hidden outputs
`[[0,0,8,8]]` and `[[8,8,0,0]]`. The official frozen record was lost with the
extracted workspace; `recovery/blind-solve/` contains the exact solver, notes,
and known hashes for replay without pretending the packet journal still exists.
