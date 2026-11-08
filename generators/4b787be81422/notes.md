# Working notes: 4b787be81422

## Current native parametric status (2026-10-24)

Frozen assignment: `review-be9f00f6431caa5a`. The native candidate is **ready for
owner exact-source acceptance**. Source SHA-256: `6aea60d3927c6cc6a7ef7ac2ef29b5f5b51406cb2f23f2a28d1d3ccdb5df9354`.
The canonical `generator.py` and selected Racket authority are unchanged.

`workspace/parametric/adapter.py` and `promotion.json` expose left-right,
top-bottom, half-turn, and `bbox_major_axis` settings with independent 3–6 demos
and 1–4 queries. The added setting measures occupied height/width, chooses LR
for tall content and TB otherwise (including square ties), then classifies the
whole canvas. This is input-dependent contextual gating, not iterative simulation.
The new orbit sampler replaces the prototype's inherited corner-coded schedule.

Current evidence: `workspace/parametric/evidence/native-v2/checks.json` reports
8 protected-Racket episodes across all settings at seeds 0/17, 1,338 program/input
evaluations including 8 official pairs, exact public-byte hashes, and first-turn
prefix parity. `boundaries.json` adds 16/16 successful direct-adapter lessons,
48/48 prefix comparisons, all settings on minimum 3×3 inputs, and substantive
30×30 queries. The task test receipt reports 58 passed, 0 failed/errors/skipped.
The native source inventory is `workspace/parametric/evidence/manifest.json`.
The return contains `checks/4b787be81422/qualification/{qualification,execution}.json`
(8/8 jobs, 128 protected executions) and `checks/4b787be81422/causal/`
(3 changed-output wrong-intermediate cases, constructed and replayed).

Teaching limit: three demonstrations identify the four declared settings but
can leave extra rivals viable. Every emitted query is screened against all
viable tested rivals. In particular, three-demo bbox-major lessons retain the
bbox-alignment rival; a fourth centered asymmetric demo eliminates it. This
conditional support is explicit; no universal identification or training gain
is claimed. The reusable writer and `checks/4b787be81422/edge_probe.py` reproduce
the focused checks.

The **unchanged canonical sampler** still has a top-right-corner shortcut.
The bounded audit confirms it on 8 ordinary draws and gives two lawful 3×3
Racket counterexamples. This finding remains open for canonical sampler repair;
the new native sampler refutes the corner rival in its demonstrations. Existing
canonical approval is not refreshed, and no owner acceptance or training
admission is claimed by this return.

Approach decisions: retain the three useful axis rules and exact default; add
bbox-to-axis selection rather than introducing component tie/connectivity rules;
use the existing native API, public-byte helpers and witness builder. The
ordinary count is three as required by owner intake; fourth/fifth/sixth demos
strengthen the finite curriculum without expanding the maximum beyond six.

## Intended rule and authority

Return `[[1]]` exactly when every input row equals its reversal (left-right / vertical-axis reflection symmetry); otherwise return `[[7]]`. The selected Racket authority was not changed and remains pinned by `RULE_HASH = "4a60caa6e208"`.

The canonical demonstrations are intrinsically axis-ambiguous: top-bottom symmetry and 180-degree rotational symmetry fit all canonical pairs. I used imported note `GNOTE-003159` as a lead and independently retained the existing four-residue schedule that puts top-bottom-only and rotation-only negative witnesses into ordinary four-demonstration windows. Imported notes `GNOTE-003160` and `GNOTE-003161` also guided preservation of matched foreground counts and the canonical-compatible `self_check` boundary.

## Repair in this review

Baseline defect lint found that `generate` silently coerced invalid `sample_index` scalars (`True`, `False`, `1.0`, `"1"`, and `-1`). Root cause was explicit `int(...)` conversion at the public call boundary. The repair adds strict validation before any generation work: `seed` must have literal type `int`, and `sample_index` must have literal type `int` and be nonnegative. The schedule and all valid generation paths now use those already-validated values without coercion.

`VERSION` remains `2.0.0` deliberately. A version bump participates in RNG seeding and would change every valid generated sample even though the repair only narrows invalid API inputs. `checks/output-stability.json` compares 990 valid calls with the frozen packet baseline and finds zero mismatches.

Focused tests now cover invalid `seed` and `sample_index` scalars. They also use the portable `reviewer_support.canonical_pairs(..., root=find_root(__file__))` helper rather than the deprecated fixed-layout import.

## Shortcut witness

`counterexamples/top_bottom_shortcut.json` records an ordinary generated input (`seed=0`, `sample_index=3`, medium):

```text
2 0 0
0 0 0
2 0 0
```

It is top-bottom symmetric but not left-right symmetric. The top-bottom rival predicts `[[1]]`; the Python mirror and the authoritative Racket rule both return `[[7]]`. The focused test binds the JSON witness to the current generator, and the Racket application is retained at `checks/question-shortcut/racket.json`.

## Verification and limits

- Before battery: 11/12 green; only strict-scalar defect lint failed.
- After battery: 12/12 green at generator SHA-256 `740547e89806c6dd8c279f20a0fdd958e4b413e58a3ee9596516e5ae663fb5b7`.
- Prior focused task tests: 19/19 passed after adding the source-bound shortcut witness.
- Current portable task-test snapshot: 22/22 passed (19 retained canonical-generator tests plus 3 isolated parametric-prototype tests).
- A 300-lesson census (100 per difficulty band, four demonstrations plus one query) found zero ambiguities across 1,500 production pair checks and zero across 1,500 query rotations, against the declared rivals.
- Post-repair visible-only solve: 4/4 demonstrations pass on the first revision; earlier rule exposure is disclosed.

The finite census only refutes declared/search-tested rivals on sampled lessons; it is not a proof against every imaginable hypothesis or every seed. The selected canonical generator was already catalog-approved at this packet baseline. The new parametric extension is explicitly proposed-only and does not inherit that approval.

## 2026-10-20 original-family parametric extension

The canonical generator and selected Racket authority remain unchanged. The isolated
`workspace/parametric/prototype.py` varies one meaningful episode-level parameter,
`symmetry_axis`, over `left_right` (canonical/default), `top_bottom`, and
`rotation_180`. A seed selects one setting for an entire four-demonstration/one-query
episode. The demonstrations eliminate both alternative axes, and the query is
positive only under the selected setting.

The exact Racket program SHA-256 values are:

- left-right: `4a60caa6e20884d9da9f502911f0d9f7f8610c537e2d348cb88b68f050c40997`;
- top-bottom: `a09981aa82ae2ebca81e0bdabb6e6af1dcfa50d9a27decd180b716052de4855e`;
- 180-degree rotation: `629cae4e51721d4e08bdaffa35e155f6cadf6ffee5902a433b66200f4ce3edc6`.

`checks/parametric/symmetry-axis-v1/manifest.json` records live-Racket labels,
Python-mirror parity, canonical-default parity on all eight official pairs,
redacted public episodes, private setting receipts, and one axis-specific query
witness for each setting. The bounded evidence covers seeds 0, 1, and 2 at medium
difficulty; it is not a production API, universal identifiability proof, or approval
of the two variant rules.
## Current reviewer considerations

Source SHA-256: `740547e89806c6dd8c279f20a0fdd958e4b413e58a3ee9596516e5ae663fb5b7`.

# Decisions for 4b787be81422

## D1 — Preserve the intended rule and Racket authority

**Choice:** Keep the left-right symmetry classifier and `RULE_HASH = 4a60caa6e208` unchanged.

**Rationale:** Rule smoke, authority synchronization, all canonical pairs, and the existing Python mirror already agree. The blocking defect was an input API contract issue, not a semantic error.

**Rejected alternative:** Editing the Racket program or canonical row. That would add authority churn without addressing the reproduced bug.

**Evidence:** `checks/after/checks/4b787be81422_after_rule_smoke.json`, `checks/after/checks/4b787be81422_after_authority_sync.json`.

## D2 — Preserve the four-residue adversarial curriculum

**Choice:** Retain the paired schedule and its ordinary four-demonstration windows.

**Rationale:** Imported notes `GNOTE-003159`, `GNOTE-003160`, and `GNOTE-003161` identified the canonical axis ambiguity, count-shortcut risk, and grammar boundary. Current measurements confirm the schedule supplies both labels, matched-count opposite-label pairs, top-bottom-only negatives, and rotation-only negatives.

**Rejected alternatives:** Random independent examples could omit a rival-killing witness in a short lesson; narrowing the grammar to generated shapes would reject lawful canonical inputs; broad distribution refactoring would be unrelated to the sole failing gate.

**Evidence:** `checks/after/checks/4b787be81422_after_semantic_gate.json`, `checks/lesson-census-final.json`.

## D3 — Validate rather than coerce scalar call arguments

**Choice:** Require `type(seed) is int`; require `type(sample_index) is int` and `sample_index >= 0`; validate before generation.

**Rationale:** `int(...)` collapses distinct invalid values (`True`, `1.0`, `"1"`) and makes a negative index participate in the cyclic schedule. Strict rejection gives one unambiguous public contract and prevents hidden aliasing.

**Rejected alternatives:** Retaining coercion for convenience; accepting arbitrary `numbers.Integral` values; clamping negatives; validating only `sample_index`. These either preserve ambiguity or leave the seed boundary inconsistent.

**Evidence:** `checks/before/checks/4b787be81422_before_defect_lint.log`, `checks/task-tests-red2/result.json`, `checks/counterexample-green/result.json`.

## D4 — Do not bump `VERSION`

**Choice:** Keep `VERSION = "2.0.0"`.

**Rationale:** Version is part of the stable RNG context. Bumping it would remap all valid `(seed, sample_index, difficulty)` outputs even though no lawful generation behavior needed to change. The new rejection contract applies only to inputs that were already outside the intended domain.

**Failure mode considered:** A maintainer might expect every source change to bump version. Here that would unnecessarily invalidate the carefully measured lesson schedule. The final source hash still uniquely binds the repair.

**Evidence:** `checks/output-stability.json` reports 0 mismatches across 990 valid calls.

## D5 — Make tests portable and bind the shortcut witness

**Choice:** Use `reviewer_support.canonical_pairs(..., root=find_root(__file__))`; add a checked-in JSON counterexample and a focused test that regenerates it.

**Rationale:** Portable task-test runtimes do not preserve repository-depth assumptions. A data witness makes the strongest rival answer reusable by future agents and prevents prose from drifting away from source behavior.

**Rejected alternative:** Keep the deprecated canonical import or cite only an ad hoc review script. Both are less portable and less durable.

**Evidence:** `checks/counterexample-red/result.json`, `checks/counterexample-green/result.json`, `checks/question-shortcut/racket.json`.

## D6 — Report finite curriculum evidence honestly

**Choice:** Claim only sampled identifiability against declared/search-tested rivals: 300 lessons and all 1,500 hold-out rotations.

**Rationale:** The census is broad and source-bound but cannot rule out every possible human hypothesis, undeclared rival, seed, or cyclic lesson start.

**Rejected alternative:** Describe the finite pass as proof of unique induction. That would exceed the evidence.
