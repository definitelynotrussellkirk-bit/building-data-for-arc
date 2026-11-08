# Working notes: 8de1c257a9c7

## Current native parametric proposal

`workspace/parametric/adapter.py` now exposes the existing
`stamp_transform=identity|mirror_horizontal` meaning through native generation.
Identity is the exact selected canonical program (SHA-256
`20f6fc6440f673f07fc9f990f63986f6ba6b49909d86b3de36b735b1f5081b23`).
The production version, source, canonical records and review index remain
unchanged. Its source hash is still
`ab38bc7be7f5af70dad4fb92ba28c237b5105c3258a99ea669088c0522189a1f`.

**Decision: expand native input support while preserving rule and legacy API.**
Native inputs have side lengths 8–30, exact colors 0/2/3/8, one green anchor,
nonempty cyan geometry connected to it, at least one red destination, and complete
stamps fitting under both settings. Procedural rings, branches and walks replace
count-unique template selection in this native path. Legacy `build_input` and
`generate_episode` keep their original finite-bank schedule and defaults; the
native adapter calls the new `generate` entry point.

The first two demonstrations hold dimensions, green/red coordinates and cyan
count fixed while changing geometry and the correct output under both settings.
Thus no deterministic rule using only those matched features can fit both.
They also teach noncentral anchoring, source clearing, holes, extent beyond 3×3,
multiple destinations, and even-multiplicity overlap. A fixed six-demo/four-query
bank is built before slicing, preserving matched inputs across settings and
independent count prefixes. Limits are 2–6 demos and 1–4 queries; ordinary native
qualification defaults to three demos. Queries preserve single-destination,
separated-copy and overlapping-copy branches, including 8×8 and 30×30 cases.

**Fresh bounded evidence.** The current pass ran 99 focused tests: thirteen
native-family/legacy-compatibility, eleven independent-audit, sixty-five export,
and ten geometry-gate tests. The sampler completed 144/144 requests across
twenty-four seeds, two settings and three count combinations; it retained 240
distinct inputs, 96 distinct queries and 221 different source offset sets.
Observed attempts were at most 4/128 per profile. Large outputs contained
416–558 cyan cells and reached all four canvas boundaries. These sampler labels
are Python claims, separate from protected reference execution.

The independent audit executed 528 protected Racket evaluations across six
episodes (minimum two demos at seeds 0/17, six demos at 101; both settings and
four queries). All thirteen extra rivals and the opposite setting are refuted
by demonstrations alone. The forty-four emitted pair labels agree with the
independent interpretation and Racket. Frozen certificates are unchanged after
query evaluation. The cheap screen's missing query-claim validation was caught
by a failing regression and repaired before this final audit.

**Native readiness.** The 28-file native inventory is current. Qualification at
seeds 0/17/101, three demos and four queries passed sixty protected evaluations.
Two wrong-intermediate witnesses were built and independently replayed: swapping
the equal-count template changes seven cells on an 18×24 mirrored example;
using bbox center `(7,13)` instead of green `(5,13)` changes 286 cells on the
30×30 canonical-setting query. This establishes an input-derived geometric
dependency, not iterative state simulation. The final binding check confirms
153 qualified files, five executor files, all inventory/source hashes, exact
saved episodes, eleven export payloads and matching protected runtime identities.

Evidence is in `checks/8de1c257a9c7/`: `family-sampler-final.json`,
`native-audit-final/`, `qualification/`, `causal/`, `examples/`,
`examples-report.json`, and `final-binding.json`, with actual command receipts.
The existing full production battery was not rerun. Early implementation
failures and the legacy gate's intentional rejection are retained distinctly
from final passing checks.

### Assigned question: one extra data-quality gate

Use the opt-in `workspace/parametric/check_geometry_gate.py` gate for families
intended to teach reading source geometry. It requires a demonstration pair
with the same dimensions, anchor/destination coordinates and cyan count but
different source offsets and answers. It uses labeled demonstrations only;
queries and hidden settings cannot rescue a missing teaching contrast.

**Reproducible failure:** a fresh capture of the old seed-zero prototype has
three demos and one query under each setting. Eight protected executions verify
those intended labels; eight more show the historical count-only lookup fits
every captured pair. The old sampled query is not incorrect: this is a bypass
of geometry extraction inside a restricted bank. The new gate rejects both old
lessons and passes both current native exports. Exact old programs, grids and
outputs are retained in `legacy-baseline.json` and `legacy-count-shortcut.json`;
gate results are `geometry-gate-legacy-final.json` and `geometry-gate-native.json`.

**Possible false positive:** an intentionally finite-template family or a useful
diverse lesson with no exactly matched nuisance features can lack this contrast.
Use the gate for the intended geometry-learning contract, not as a blanket veto.
**Cheapest test:** run the pure-Python gate over already reference-verified
private episode JSON/JSONL. It groups demos by the fixed-feature signature and
compares their geometry/outputs; it performs no extra Racket calls or model run.
No Qwen learning improvement has been measured in this review.

### Open production finding and owner action

The existing production-only cardinality-lookup audit remains **unresolved** at
the unchanged production hash. The native extension fixes that shortcut for its
own broader grammar; this does not repair, resolve or approve the production
finite bank. Review and integrate the proposed source, then run qualification
and fresh owner acceptance against the exact integrated bytes. Reviewer-ready
evidence and exports grant neither acceptance nor training admission.

## Current rule and generator

Version `3.1.1` teaches one rule: locate the single green anchor, represent every
cyan cell as an exact offset from it, clear the source scene, and stamp that same
offset set at every red destination. Generated inputs use only colors 0/2/3/8,
have one green anchor, 4–14 cyan cells connected to it, and 1–5 red markers at
centers where the full template fits.

The eight-slot default schedule alternates the four complete linked 13×13
canonical profiles with asymmetric hook/stair profiles. Every four consecutive
slots include asymmetry and multiple destinations. Every five-slot cyclic lesson
now includes at least two overlap witnesses, so holding any one of its five pairs
out as the query still leaves a demonstration separating union from XOR overlap.

## Repaired defects

1. **Exact controls were not independent.** A partial override could change the
   template, red count, layout, and unrelated random draws. v3.1.1 keeps unpinned
   semantic axes on their scheduled values and retains linked canonical placement
   whenever the actual template/count still match the slot.
2. **`None` was not a no-op.** Explicit `None` entered `gen_ctx` and changed the
   sampled curriculum. It is removed before context construction.
3. **Integer controls silently coerced values.** Floats, strings, and booleans
   could become dimensions/counts through `int(...)`. `grid_h`, `grid_w`, and
   `n_reds` now require exact non-boolean integers.
4. **Task tests assumed one repository depth.** Tests now use
   `reviewer_support.find_root` and support source-tree and staged-runtime layouts.
5. **Selected Racket authorities differed by comments/formatting.** Both base
   records now preserve the comment-rich source as archival `raw_code` while the
   active `target_code` is byte-for-byte canonical. Rule semantics and declared
   rule hash `c539e2039994` did not change.
6. **One cyclic lesson window had only one overlap witness.** In v3.1.0, the
   window `[4,5,6,7,0]` became ambiguous against XOR when slot 7 was the query:
   36/1,500 rotated queries failed in the 300-lesson census. Slot 5 changed from
   `spread` to `clustered`, giving that window a second overlap witness. The final
   v3.1.1 census found 0/300 production ambiguities and 0/1,500 rotation
   ambiguities against the declared rivals.
7. **A positive branch witness was mislabeled as rival evidence.**
   `single_destination_branch` is now in `BRANCH_WITNESSES`; it is retained as
   coverage, not claimed as a rival refutation.

## Rival rule and retained witness

The strongest canonical-fitting rival is **horizontal mirror before stamping**.
All four canonical cyan templates are horizontally symmetric, so the rival fits
every canonical pair. The retained asymmetric-hook case is
`counterexamples/horizontal_mirror_seed29_slot1.json`; intended and rival outputs
differ in 16 cells. Independent selected-rule execution is retained at
`checks/mirror-counterexample/racket-final-v311.json` and matches the Python
intended output exactly.

## Reusable evidence

- `workspace/probe_controls.py` exhausts every schedule slot across fixed seeds
  for `None` no-op behavior, same-value identity, dimension-axis isolation, and
  coercion rejection; final report: `checks/control-probe-final-v311.json`.
- `tests/test_generator_8de1c257a9c7.py` covers canonical support, every cyclic
  five-pair/query rotation, controls, mutation rejection, determinism, semantic
  metadata, and the retained mirror witness.
- `tests/test_control_probe_8de1c257a9c7.py` keeps the standalone probe portable
  in both source-tree and staged-runtime layouts.

## Known limits

The morphology bank is deliberately finite: four canonical templates plus two
asymmetric templates. The final census is finite evidence against declared
rivals, not a uniqueness proof against every conceivable program. Colors retain
fixed semantic roles, and the schedule is deterministic modulo seed-driven
placement. Independent maintainer approval remains outside this review.
## 2026-10-20 public-call and parametric review

The issued v3.1.1 source passed 11/12 before-battery stages. The sole failure was
`defect_lint`: 48 probes showed that coercible or unsupported public values for
`seed`, `sample_index`, and `difficulty` were accepted. The current source adds
`_validate_public_controls` and applies it in both `generate` and
`schedule_profile`: seed/index must be exact non-boolean integers, indices must be
nonnegative, and difficulty is limited to `None|easy|medium|hard`.

The production `VERSION` intentionally remains `3.1.1`. A temporary 3.1.2 bump
changed keyed `gen_ctx` draws and broke the retained seed-29/sample-1 witness even
though the accepted distribution was not meant to change. Restoring 3.1.1 keeps
all valid calls byte-compatible while rejecting invalid calls. New portable tests
cover the public scalar contract. The final selected suite passes 45/45 and the
strict after battery passes all 12 stages. Final generator SHA-256 is
`ab38bc7be7f5af70dad4fb92ba28c237b5105c3258a99ea669088c0522189a1f`.

A proposed, isolated parametric extension now lives under
`workspace/parametric/`. It selects `stamp_transform` once per episode from
`identity` (canonical default) or `mirror_horizontal`, preserving the original
anchor/offset/stamp reasoning. Exact Racket and independent Python executions
match on 80/80 labels across 40 inputs, and all 32 measured one-pair holdouts
identify the selected setting. The extension deliberately uses asymmetric
hook/stair demonstrations because canonical symmetric templates cannot identify
this parameter. It is prototype evidence only; production generation and the
canonical Racket authority are unchanged.

The final 100-per-band lesson census materialized 300 lessons with four
demonstrations and one query each. It found 0/1,500 production ambiguities and
0/1,500 rotated-query ambiguities against declared rivals across 921 unique
inputs. This remains finite evidence, not a uniqueness proof.
## Current reviewer considerations

Source SHA-256: `ab38bc7be7f5af70dad4fb92ba28c237b5105c3258a99ea669088c0522189a1f`.

# Decisions: 8de1c257a9c7

## D1 — Fix only the demonstrated public-scalar contract

**Observed defect.** The before-phase detector accepted 48 invalid values across
`seed`, `sample_index`, and `difficulty`. These values can alias valid curriculum
coordinates (`True == 1`, `1.0 == 1`) or create undocumented difficulty lanes.

**Decision.** Add one validator used by both `generate` and `schedule_profile`:
exact non-boolean integers for seed/index, a nonnegative index, and the four
supported difficulty values. Keep advertised override validation in the existing
normalizer.

**Alternatives rejected.** Relying on `gen_ctx` leaves call-site behavior
implicit and did not satisfy the detector. Coercing strings/floats preserves the
ambiguity. Validating only `generate` would leave `schedule_profile` with a
different public contract.

**Evidence and failure mode.** The new tests first failed on all intended cases,
then passed 22/22. The completed after battery reports zero defect-lint findings.
Future public entry points should call the same validator or add equivalent
regressions.

## D2 — Do not bump the keyed generator version for a rejection-only repair

**Initial choice.** I briefly changed `VERSION` from `3.1.1` to `3.1.2`.

**Reversal.** Restore `3.1.1`. `gen_ctx` includes the version in keyed draws, so
the bump changed valid outputs even though the intended distribution was not
being revised. The frozen seed-29/sample-1 witness failed under the bump and
matched exactly after restoration.

**Reasoning.** Invalid-call rejection is an API-contract correction; valid
seed/sample/difficulty tuples should remain byte-stable. A version bump would be
appropriate only if the accepted generation distribution or semantics changed.

## D3 — Preserve the canonical production path and authority

The baseline already passed distribution, profile, semantic, grammar, Racket,
and authority gates. I therefore left templates, schedule, placement, palette,
Racket source, and rule hash untouched. Final exact-profile and envelope support
remain 28/60; declared rule hash remains `c539e2039994`.

The strongest known canonical-fitting rival—horizontal mirroring—continues to be
refuted by generated asymmetric examples. The 300-lesson census found no
ambiguity in production ordering or any one-pair rotation against all declared
rivals.

## D4 — Prototype one bounded rule parameter rather than broaden production

**Chosen parameter.** `stamp_transform ∈ {identity, mirror_horizontal}`, selected
once per deterministic episode. Identity is the canonical default; horizontal
reflection is the strongest canonical-fitting rival and preserves the same
object roles, anchor relation, transplant operation, colors, and output frame.

**Why this parameter.** It changes one compositional step without turning the
family into a different task. Existing asymmetric hook/stair templates provide
lawful, minimal teaching examples, while canonical symmetric templates expose
why parameter-specific demonstrations are necessary.

**Alternatives rejected.** Rotations add four settings and more boundary cases;
vertical reflection is not the known canonical ambiguity; palette changes alter
role coding rather than the geometric rule; changing union/XOR overlap would
modify composition semantics and require a different lesson contract.

**Integration decision.** Keep the extension under `workspace/parametric/` as a
proposed prototype. It has matching Racket, a Python mirror, public redaction,
private episode evidence, and all-holdout checks, but it is not approved for
production or training.

## D5 — Require asymmetric demonstrations for the parameterized family

All four canonical templates are horizontally symmetric, so identity and mirror
coincide on every canonical pair. Prototype episodes therefore use asymmetric
lawful inputs and three demonstrations before one query. In eight measured
episodes, all four possible held-out queries remain identifiable. Arbitrary
unfiltered episode assembly is still a known failure mode and is explicitly
outside the prototype claim.

## D6 — Retain failures and bind conclusions to final bytes

I retained the interrupted first battery attempt, the TDD red run, the
pre-prototype errors, and the intermediate version-key regression. Final claims
refer only to generator SHA-256
`ab38bc7be7f5af70dad4fb92ba28c237b5105c3258a99ea669088c0522189a1f`.
The audits are source-bound to their separate assigned hashes and do not imply
that those targets were repaired.
