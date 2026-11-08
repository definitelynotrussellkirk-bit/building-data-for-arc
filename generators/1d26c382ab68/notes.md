# Working notes: 1d26c382ab68

## Current parametric proposal — turn-guided reflected selection

`workspace/parametric/adapter.py` and `promotion.json` provide two episode-fixed
settings: the exact canonical `rotation_match`, and `turn_guided_reflection`.
The canonical generator, authority, version and distribution remain unchanged.
The separate six-candidate grammar uses two dihedrally distinct chiral pentomino
families. The upper template selects the family; each family contributes one
rotation candidate and two opposite reflected orientations.

For the alternative, A identifies the rotational match and relative turn; B
uses that result to choose `R^t F(T)`. After the match is known, only turn parity
is needed (`R^t F(T) = R^(2t) F(M)`). This is input-derived contextual gating,
not iterative simulation. The first two demonstrations hold the lower scene
fixed, change the upper template's family, and use opposite turn parity.
They eliminate the tested template-ignoring, position and fixed-turn shortcuts.

Counts are independently 2–6 demonstrations and 1–4 queries, normally 3/4.
Matched seeds produce identical inputs under either setting. Four queries cover
11×13, 20×22, 24×26 and 30×30; the 30×30 case has 315 object/template cells plus
the divider. `model_view` reveals one query and strips private metadata from
episode and pair levels. It does not implement a controller or trainer.

Reviewer evidence: 32 focused tests; 8 endpoint-count self-review episodes with
64 Racket-checked label claims (40 distinct protected executions), with only the
selected rule surviving 22 finite hypotheses; native qualification for both
settings and seeds 0/17 with 3 demos and 4 queries. Protected causal replay
changes the selected reflected object when operation order is reversed in
11-row and 30×30 qualified cases. Source inventory is
`workspace/parametric/evidence/manifest.json`; complete return evidence is
`checks/1d26c382ab68/{self-review,qualification,causal}/`.

Independent code review found no blocking defect. One observer limitation is
documented: hand-edited other-family chirality multiplicities are not fully
validated by `analyze`; the sampler constructs them correctly. Finite rival
checks do not prove universal identifiability or measured training gain.
Native owner acceptance on integrated live bytes remains required. No approval
or training admission is granted by this reviewer return.

## 2026-10-06 review `review-eeb8697721e28693`

The selected baseline was generator SHA-256 `93e88ca1ef2cfcda83fb883320eba8c53dcd88eb47c9a4f00d19c0859d769a95`. I used prior audit `review-f4e1e8198c66d9f9:v0001` only as a lead: it reported a portable canonical-data path failure. I reproduced that failure independently before changing the test.

The baseline generator itself already had strong geometry, exact overrides, deterministic match-slot/rotation cycling, 100% sampled input/output uniqueness, and a fully green 12-stage battery. I therefore did **not** alter generation, the Racket authority, `VERSION`, `RULE_HASH`, or the keyed draw schedule.

Two bounded defects were repaired:

1. The task test guessed a task-relative canonical path. It now uses `reviewer_support.find_root()` and `canonical_pairs()` and passes in the copied portable runtime.
2. Every semantic witness was weak because no executable rivals were declared. The four public canonical pairs also admit the wrong `always_left` rule. The generator now declares executable `always_left`, `exact_orientation_only`, `accept_reflection`, and `all_same_size` rivals; maps concrete witnesses to each; records `always_left` as a canonical shortcut; and checks rival survivorship in `lesson_identifiable`.

The rival-contract test was written red first, failed on the missing declarations, then passed after the contract was implemented. It checks all 12 cyclic starts per difficulty with three consecutive demonstrations and the next sample as query. The production census then materialized 300 lessons (100 per band), 1,200 unique inputs, and all 1,200 query rotations with zero ambiguity against the declared rivals.

Limitations: this is finite evidence against four explicit hypotheses, not a proof of unique program induction. The rival functions share the generator's structural parser, while label correctness remains independently checked by the selected Racket authority in rule-smoke and authority-sync stages.
## Current reviewer considerations

Source SHA-256: `7af83faf43c07849c2a1900002e2258846d052d4d9899a5d066658d32f538ac0`.

# Decisions: `1d26c382ab68`

## D1 — Preserve the generator distribution and selected authority

**Input choice:** keep generator version `3.0.0`, `RULE_HASH e4dd26fbc01b`, all axes, shape families, candidate colors, match-slot/rotation cycles, and Racket source unchanged.

**Rationale:** the baseline battery was already 12/12 green, exact overrides passed, the structural grammar was strong, and sampled diversity was complete. Changing sampling merely to make the review look larger would risk replay drift without addressing a demonstrated data-quality defect.

**Rejected alternative:** widen shapes, dimensions, colors, or add random schedules. These would add unneeded distribution risk and could reduce the deterministic three-demo teaching guarantee.

**Failure mode/limit:** preserving the schedule also preserves any undeclared shortcut it might contain; that is why the repair strengthens executable semantic checks rather than assuming the schedule is sufficient.

## D2 — Repair canonical access with public portable helpers

**Input choice:** replace fixed `Path(__file__).parents[...]` logic with `reviewer_support.find_root(__file__)` and `canonical_pairs(TASK_ID, root=...)`.

**Rationale:** the copied task-test runtime deliberately relocates tests beneath a task. Public helpers encode the packet layout and retain pair identity without guessing source depth.

**Rejected alternative:** copy canonical data under each task or add another parent-depth constant. Both duplicate authority or remain layout-dependent.

**Probe:** the before task-test stage failed at preflight; the same stage after the change ran pytest and passed 16/16 tests.

## D3 — Declare four executable rivals

**Input choice:** `always_left`, `exact_orientation_only`, `accept_reflection`, and `all_same_size`.

**Rationale:** each is a compact, deterministic misgeneralization directly suggested by the visible grammar. `always_left` is especially important because it fits all four public canonical pairs; the others test rotation invariance, reflection exclusion, and shape rather than cell-count matching.

**Rejected alternative:** add dozens of arbitrary transforms. A large unmotivated rival list creates noise and false confidence; rivals should be plausible, pure, executable, and tied to a generated counterexample.

**Failure mode/limit:** passing this finite family does not prove unique induction. New evidence should add a rival callable and an explicit witness mapping rather than relying on prose.

## D4 — Bind witnesses to rivals instead of counting frequency only

**Input choice:** map middle/right matches to `always_left`, nonidentity rotations to `exact_orientation_only`, the chiral distractor to `accept_reflection`, and equal candidate sizes to `all_same_size`.

**Rationale:** a witness name is weak unless its output demonstrably disagrees with a wrong program. The semantic gate now verifies seven witness→rival claims rather than merely counting nine predicates.

**Rejected alternative:** mark every witness as a generic branch witness. That would silence weak-witness reporting without proving what any example teaches.

## D5 — Keep the three-consecutive-demo policy

**Input choice:** three demonstrations at consecutive sample indices, next sample as production query; test every query rotation separately.

**Rationale:** existing modulo schedules make every three-example window cover all three candidate slots and three distinct rotations. This is minimal, deterministic, rejection-free, and leaves one query.

**Rejected alternative:** increase `EXAMPLES_NEEDED` to four. Four would show all rotations but is unnecessary once every three-demo lesson refutes the declared rivals, and it would increase context cost for Qwen3.5-9B.

**Probes:** all starts 0–11 in each band pass the task-local test; the semantic smoke passes 48/48 rotations; the larger census passes 300 production lessons and 1,200 rotations.

**Failure mode/limit:** arbitrary downstream filtering, nonconsecutive indices, or changing seeds between demonstrations invalidates this guarantee. Re-run the hook on the actual exported lesson.

## D6 — Do not bump `VERSION`

**Input choice:** retain `VERSION = "3.0.0"`.

**Rationale:** no generated grid or label changed. A version bump would intentionally perturb keyed RNG outputs and defeat replay continuity for a contract-only repair.

**Rejected alternative:** bump for every source edit. That policy is appropriate for generation changes, not pure test/diagnostic declarations.

## D7 — Post-repair solve and exposure declaration

**Input choice:** solve one fresh visible episode after source freeze and record earlier exposure as `yes`.

**Rationale:** the solve verifies that the three-demo presentation supports a direct component/rotation program, while honestly separating it from a blind inference claim. Revision 1 matched 3/3 visible examples; private query correctness remains withheld.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/1d26c382ab68/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
