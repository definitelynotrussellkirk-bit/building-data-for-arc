# Working notes: 498af9326ab9

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current parametric family: any/every shortest path

`workspace/parametric/adapter.py` supplies episode-fixed `path_mode=any|every`.
`any.rkt` exactly preserves the selected canonical program. `every.rkt` marks
zero vertices in singleton layers of the obstacle-aware shortest-path graph:
these are precisely the vertices every shortest route must visit. The Python
adapter's labels are checked by actual protected Racket; a path-count oracle
and vertex-deletion tests independently check the intersection criterion.

The input grammar includes winding room chains, cyclic mazes, asymmetric
obstacles and multi-gate barriers, with 2–6 demonstrations and 1–4 distinct
queries. Four-query requests include substantive 30×30 room networks. Matched
inputs across settings prevent a setting-dependent sampler shortcut. The first
demo forces backward major-axis travel and reverses at least one marker
coordinate. These address the retained sampling findings **within this new
family**; the selected production generator is unchanged, so its prior audit
resolutions remain unchanged.

Current evidence: native `workspace/parametric/evidence/manifest.json`, the
task-local `evidence/current/` execution/teaching/boundary files, and returned
`checks/498af9326ab9/qualification/{qualification,execution}.json`.
Qualification passed both settings at seeds 0 and 17, with three demos and four
queries. The bounded audit has 96 Racket evaluations; qualification has 40.
All 48 staged task tests pass, including 192 bounded sampler requests and
eight-seed teaching checks against seven specified rival rules. No universal
identifiability or training-gain claim is made.

The required protected causal witness is returned at
`checks/498af9326ab9/causal/witness.json`: its actual optimal distance is 52,
whereas the wrong Manhattan intermediate is 22. Both programs execute and
produce different outputs; construction and independent replay are retained.

The existing test suite had a fixed-depth canonical-data lookup that failed
in the staged runtime. It now uses `reviewer_support.find_root` and
`canonical_path`. The initial failure and successful relocated run are both
retained under `checks/498af9326ab9/`.

Status: reviewer **ready/qualified**, owner exact-source acceptance pending.
Next action: integrate this task-local delta and run the normal native
qualification/acceptance handoff on live bytes. No training admission or
canonical source/rule hash update is included. See the parametric README for
the exact commands, finite coverage and one-query public projection.
