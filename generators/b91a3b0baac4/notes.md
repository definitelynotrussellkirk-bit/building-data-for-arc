# Working notes: b91a3b0baac4

## Current intended rule

A unique corner marker selects a common beam direction: 1=up, 2=right, 3=down, 4=left. Every other nonzero, non-5 cell emits its own color in that direction. The beam passes through ordinary colored cells, stops immediately before the first color-5 cell, and otherwise reaches the edge. The marker and blockers are preserved. The selected Racket authority is unchanged and pinned by `RULE_HASH = "46ed28101b5f"`.

## Repair decision (version 4.0.0)

The previous 3.0.2 sampler placed emitters and blockers independently. Retained audit `review-e60aa433587d30e8:v0001` showed the blocker-ignoring rival matched 1,305/1,800 draws and all five demonstrations in one consecutive lesson (`evidence/review_index.json`; retained probe under `counterexamples/review-e60aa433587d30e8-v0001/`). I used that prior return only as a lead and remeasured the pinned baseline with the packet's before battery.

I replaced random blocker placement with a constructive beam-coordinate layout. Every normal draw now reserves one emitter/blocker line with downstream space, guaranteeing an active blocker, and places every remaining blocker upstream of all emitters on its line, guaranteeing at least one irrelevant blocker. This reverses the prior “random blockers may or may not matter” choice because it produced lesson-level ambiguity. The minimal repaired witness is `counterexamples/blocker_schedule_repair.json`; focused tests exhaust bounded cyclic five-demo windows and compare the executable `ignore_blockers` rival.

The old `palette_kind` and `texture` controls were removed rather than relabeled: they were inert or admitted unlawful negative fixtures. The replacement exact axes are grid height/width, emitter and blocker counts, emitter-palette size, marker corner, and marker direction. Every advertised boundary is constructive and observable through `observe_overrides`; unknown keys and non-strict scalar controls are rejected.

A deterministic five-residue profile schedule supplies 6x9/palette-6 and 7x9/palette-5 canonical profiles in four residues and a difficulty-weighted broad profile in the fifth. This preserves broad layout/color variation while making profile-floor support explicit in every band. `strict_canonical_like`, one named semantic witness, one named rival, and the lesson competitor contract are executable.

## Parametric assessment

`workspace/parametric/` contains a separate **prototype** for one bounded rule parameter, `blocker_mode ∈ {stop, pass}`. `stop` is the canonical default; `pass` continues through and repaints color-5 cells. The setting is selected once per episode. Retained Racket programs and seed-17 evidence show every demonstration distinguishes the two settings. The prototype does not alter or approve the production rule.

## Assumptions and limits

- The generator samples only canonical fixed-rule inputs; outputs remain the selected Racket rule's responsibility.
- Production draws deliberately require at least two blockers and four emitters, while `self_check` accepts the sparser canonical pairs (one blocker, two emitters).
- The declared rival set is finite. Passing `ignore_blockers` checks does not prove universal identifiability against every conceivable rule.
- `strict_canonical_like` validates the fixed beam grammar, not an exhaustive characterization of all aesthetically useful ARC instances.
- The profile schedule is keyed by `sample_index % 5`; the source-bound lesson census and task-local cyclic probe cover the retained sampling policy, not arbitrary downstream reordering policies.
- Independent maintainer replay and masked-query scoring remain outside this return.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-e60aa433587d30e8:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `eea96d81a3687aabf92ae2a0ac01609f0656727a07e7a977c83bef86f3d51350`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit focused closure against current 92e1c956e8d2bbd05b396c1c853871a5d39bfc20114d875e31a65c599b08b9c8. Owner static inspection confirms constructiveexclusive activebeamline emittert1/blockert3 plusupstreamirrelevantblockers,declaredignore_blockers rival andactive/inactivewitness. Focusedtestsasserteverydefaultdraw changes outputwhenblockersignored andeveryfive-demo cyclicwindowhaswitness. ReviewerRacket600/600witnessdraws,60/60rivalclaims,62portabletests and300lessons/1800rotations directlyclosepriorseed1/index1..5all-noninformative-blocker lessondefect. Retainedcounterexamples/blocker_schedule_repair.json;productionvscanonicalcountsremainexplicit;finiteevidence notuniversalproof.

### Assessment or prior finding

## b91a3b0baac4

**Suspected training shortcut, reproduced at lesson level: blockers are usually
non-informative.**  The generator places color-5 blockers uniformly among free
cells rather than ensuring they intercept a beam.  An executable rival that
casts every beam to the border and ignores blockers produced exactly the same
output as the canonical rule on 1,305/1,800 draws (72.5%): easy 516/600, medium
437/600, hard 352/600.

The weakness is not only per-example.  With seed 1 and medium difficulty, the
ignore-blockers rival fits all five consecutive demonstrations at sample indices
1–5, then changes the answer at query index 6.  The query was run through Racket;
the Python authority mirror matches the Racket output and the blocker-ignoring
rival differs.  Evidence: `checks/audit/b91a3b0baac4/probe.json`,
`checks/audit/b91a3b0baac4/racket_query_input.json`,
`checks/audit/b91a3b0baac4/racket_query_output.json`, and
`checks/audit/b91a3b0baac4/crosscheck.json`.

This is a curriculum-quality finding, not a claim that every downstream lesson
is ambiguous.  A repair should schedule at least one guaranteed active-blocker
witness per lesson window while retaining some irrelevant blockers to prevent a
shortcut that treats every 5 as active.  No audit-target patch was made.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-e60aa433587d30e8-v0001/audit_assets.json), manifest SHA-256 `06fc691c879d6a4a2123a4e9d9d081742958dea5fd7e95e1315805c93f19adf2`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `92e1c956e8d2bbd05b396c1c853871a5d39bfc20114d875e31a65c599b08b9c8`.

# Decision ledger for `b91a3b0baac4`

## D1 — Keep the canonical Racket authority unchanged

**Original choice:** The selected fixed rule already expresses the intended beam
transformation and solves the canonical pairs. The reason for the old sampler's
input distribution was not documented beyond historical notes.

**Decision:** Pin `RULE_HASH = "46ed28101b5f"` and repair only input sampling,
validation, teaching contracts, tests, and task-local prototype files.

**Alternatives considered:** Rewrite the Racket program; switch to the divergent
archival raw program; encode labels in Python. All were rejected because the
failure was lesson construction, not canonical output correctness. Python is
used only for independent mirrors/rivals.

**Probe/evidence:** Rule smoke, grammar, Racket lint, and authority synchronization
all pass in `checks/after/`; the authority report shows the selected canonical
source synchronized while a divergent archival source remains explicitly
archival.

**Failure mode/limit:** A latent rule bug shared by every canonical example would
not be repaired here. No such bug was found in this assignment.

## D2 — Replace random blocker placement with constructive mixed blockers

**Original choice:** Version 3.0.2 placed emitters and blockers independently,
apparently to maximize visual diversity. The precise original rationale is
unknown.

**Decision:** Reserve one line with an emitter at beam coordinate `t=1` and a
blocker at `t=3`; put all remaining blockers at upstream coordinates `t∈{0,1}`
on other lines, and all other emitters downstream at `t>=2`.

**Why:** The prior audit lead found the blocker-ignoring rival matched 1,305 of
1,800 draws and every demonstration in one lesson. A teaching sampler must make
the rule-defining interaction visible, not merely produce correct labels.

**Alternatives considered:**

1. rejection-sample random layouts until one active blocker appears;
2. make every blocker active;
3. add only a lesson-level resampler while leaving individual draws weak.

Constructive placement was selected because it terminates deterministically,
supports exact counts, and also preserves at least one irrelevant blocker. “All
active” was rejected as a new shortcut. Lesson-only rejection was rejected
because it hides weak examples and complicates exact replay.

**Probe/evidence:** `counterexamples/blocker_schedule_repair.json`, focused cyclic
window tests, 600/600 semantic witnesses, and the 300-lesson census.

**Failure mode/limit:** The distribution intentionally overrepresents explicit
blocker evidence relative to natural random placement. That is appropriate for
training-rule identification but should not be mistaken for a natural-frequency
benchmark.

## D3 — Advertise only exact, observable axes

**Original choice:** The old generator exposed `texture`, `palette_kind`, and
other controls that were inert, clamped, or could create invalid fixtures. The
reason for retaining them is unknown.

**Decision:** Use seven exact axes:

| Axis | Range | Rationale |
|---|---:|---|
| `grid_h` | 6..14 | Fits constructive vertical/horizontal geometry and broad ARC sizes. |
| `grid_w` | 7..16 | Leaves enough beam length at every direction and minimum size. |
| `n_emitters` | 4..8 | Stronger production lessons while remaining visually sparse. |
| `n_blockers` | 2..6 | Guarantees one active plus at least one irrelevant blocker. |
| `emitter_palette_size` | 2..4 | Avoids monochrome shortcuts while preserving repeats. |
| `marker_corner` | four corners | Tests that corner location is an anchor, not direction. |
| `marker_direction` | 1..4 | Covers every canonical direction exactly. |

Unknown keys, invalid difficulty, booleans passed as integers, and out-of-range
values are rejected. `observe_overrides` reconstructs each value.

**Alternatives considered:** Keep aliases for compatibility; clamp values; mark
large sets of combinations incompatible. Rejected because hidden coercion makes
training data and audits irreproducible. No explicit incompatibility is needed
for the constructive ranges.

**Probe/evidence:** 707 cases × 3 bands × 30 seeds = 63,630 accepted draws with
zero findings in the official override report.

**Failure mode/limit:** Removing old axes is an intentional interface break for
callers that relied on undocumented coercion. The strict failure is preferable
to silently producing a different requested instance.

## D4 — Use a deterministic canonical-profile schedule plus a broad residue

**Original choice:** The baseline mostly missed canonical height/width/color-count
profiles. The historical intended profile weighting is unknown.

**Decision:** Schedule five residues:
`6x9/palette-6`, `7x9/palette-5`, `6x9/palette-6`,
`7x9/palette-5`, and one difficulty-weighted broad draw. Here “palette-6” and
“palette-5” refer to total distinct input colors after marker/blocker inclusion;
the corresponding emitter palette sizes are 3 and 2.

**Alternatives considered:** Sample only canonical dimensions; independently
weight each dimension; rejection-sample to a target fraction. The retained
schedule gives deterministic coverage, exact override behavior, and one broad
residue without rejection loops.

**Probe/evidence:** Final profile floor 50/60 exact and 51/60 envelope; exact hits
per band 15/20 easy, 17/20 medium, 18/20 hard.

**Failure mode/limit:** `sample_index % 5` is visible periodic structure. It is a
sampling schedule, not part of the puzzle rule. Downstream systems that select
only one residue could skew the profile mix; the retained lesson census samples
consecutive starts and records residues.

## D5 — Keep marker direction independent of marker corner

**Original choice:** Marker colors 1–4 encode direction; corner placement is an
anchor. The baseline did not clearly document whether they were independent.

**Decision:** Sample all four corners and all four direction colors independently.
Exclude the marker direction color from emitter palette selection so the unique
corner marker is not confused with a same-colored emitter during structural
inspection.

**Alternatives considered:** Bind each corner to a conventional inward direction;
allow marker-color emitters. Binding was rejected as a direct shortcut. Same-color
emitters are lawful under the rule but were excluded in production for clearer
role parsing; canonical validation remains broad enough for the fixed rule.

**Probe/evidence:** Exact override tests cover all corner/direction values and
joint combinations; the post-repair visible solve inferred the mapping from five
examples.

**Failure mode/limit:** Excluding marker-color emitters narrows color-role support.
A future extension could add carefully tested role-permutation counterexamples,
but that was not needed to fix the retained blocker shortcut.

## D6 — Separate production invariants from canonical acceptance

**Original choice:** The old self-check was weak and did not encode the teaching
requirements.

**Decision:** `self_check` accepts lawful fixed-rule grids with one valid corner
marker, at least two emitters, and at least one blocker, so all canonical inputs
remain accepted. Production generation is stricter: four to eight emitters, two
to six blockers, and mixed active/inactive evidence.

**Alternatives considered:** Make self-check require the production witness or
exact production ranges. Rejected because it would incorrectly reject sparse
canonical examples and conflate rule validity with curriculum policy.

**Probe/evidence:** 3/3 canonical inputs accepted; 600/600 sampled strict checks;
no profile-floor crash.

**Failure mode/limit:** A self-check pass does not assert lesson identifiability.
That is deliberately handled by semantic witnesses/rivals and lesson tests.

## D7 — Declare one executable plausible rival

**Original choice:** The baseline had no executable semantic contract.

**Decision:** Declare `ignore_blockers`, map it to the
`active_and_inactive_blockers` witness, and reuse it as the lesson competitor.
This is the smallest rival directly supported by the reproduced failure.

**Alternatives considered:** Add many speculative rivals (wrong direction,
marker-as-emitter, stop-after-blocker) immediately. Rejected to avoid unvalidated
or redundant contracts. The test utility `workspace/reference_probe.py` makes it
cheap to add a rival when a concrete failure is found.

**Probe/evidence:** Rival claim 60/60 verified; every one of 300 production lessons
and every one of 1,800 query rotations refuted it.

**Failure mode/limit:** Passing a finite rival set is not universal
identifiability. The reports state that limitation explicitly.

## D8 — Five demonstrations per lesson

**Original choice:** The retained failure involved a five-demonstration lesson.
The canonical task has three labeled pairs but production curriculum policy is a
separate concern.

**Decision:** Set `EXAMPLES_NEEDED = 5`. Because every draw is itself a blocker
witness, every five-demo window refutes the declared rival even when a sixth pair
is held out as query.

**Alternatives considered:** Three examples; adaptive count; six examples.
Five matches the assignment's retained curriculum shape and keeps token cost
bounded. The constructive per-draw witness makes more examples unnecessary for
this particular rival.

**Probe/evidence:** 12 official smoke lessons, 300 larger-census lessons, 1,800
query rotations, and task-local bounded cyclic tests.

**Failure mode/limit:** Five examples do not guarantee that Qwen3.5-9B will infer
the intended rule, only that the declared rival is not observationally equivalent.

## D9 — Add one parametric rule prototype, isolated from production

**Original choice:** Production uses the canonical “stop at blocker” rule. There
was no parametric API.

**Decision:** Prototype `blocker_mode ∈ {stop, pass}` under
`workspace/parametric/`, selected once from the episode seed. `stop` remains the
canonical default; `pass` continues through and repaints blockers. Each episode
contains two demonstrations and one query, and each demonstration distinguishes
the alternative.

**Alternatives considered:** Vary direction mapping, blocker color, beam length,
or output color. Those either weaken the recognizable core family, require a
larger input grammar, or risk color-role leakage. Blocker mode changes the actual
transformation at the repaired interaction and requires no shared API change for
a standalone prototype.

**Probe/evidence:** `checks/parametric/blocker-mode-seed17.json`, two retained
Racket programs, independent Python cross-checks, public examples, and five
prototype tests.

**Failure mode/limit:** One seed and two settings are bounded evidence. The
prototype is proposed, not production-approved; the selected generator and rule
hash are unchanged.

## D10 — Preserve failed iterations and separate audit-only findings

The initial repair test failure, prototype test failure, and interrupted override
attempt remain under `checks/`. The interrupted attempt is not counted as a pass;
the completed official after battery is the aggregate evidence. Audit targets
`da776131ac9a` and `92953d9974a2` were not edited. Their reproductions are
source-bound under `checks/audit/` and reported separately in `AUDIT.md`.

## D11 — Current native admission candidate: beam completion then longest-delta highlight

**Choice.** Keep the production generator and canonical rule unchanged. Add a
native two-setting family under `workspace/parametric/`: `beam_only` is exact
canonical source, while `beam_then_highlight_longest` first completes every
blocker-aware beam, measures each emitter's newly painted delta, and recolors the
unique longest derived segment to color 8.

**Why this supersedes the older proposal.** The retained blocker pass/stop
prototype varies one local rule decision but does not supply the current round's
required causal depth. The new family makes Stage B depend on a completed-grid
intermediate while preserving the recognizable beam task and exact canonical
default.

**Teaching and adversarial design.** Inputs are setting-neutral. The minimum two
demonstrations separate the selected rules from identity, shortest/first/last
highlighting, full-beam highlighting, blocker-ignoring, and canonical-only
shortcuts. Profiles support 2–6 demonstrations and 1–4 prefix-stable queries;
the fourth query is 30×30 with both active and irrelevant blockers.

**Evidence.** 82 task tests and 20 focused tests pass. A finite audit covers 48
episodes and 184 wrong-intermediate pair checks. Four native qualification jobs
(two settings × seeds 0 and 17) execute 32 protected-Racket labels. Qualification
and execution replay byte-identically. The protected causal witness replaces the
maximum-length intermediate with the shortest segment and changes 11 final cells.

**Limits / next action.** The rival audit is finite and does not prove uniqueness
against arbitrary rules. Owner exact-source integration, fresh qualification,
acceptance replay, and any training-admission decision remain pending. Keep the
older blocker-mode prototype as provenance, not as the current candidate.
