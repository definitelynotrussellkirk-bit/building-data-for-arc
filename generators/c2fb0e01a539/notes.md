# Working notes: c2fb0e01a539

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `8f0cc0ed324b7947445743158f85b3cfb01e615513bb29f715eb790921562ede`.

# Decisions for c2fb0e01a539

## D1 — Preserve the canonical authority

**Choice.** Keep the selected Racket rule and canonical examples byte-for-byte unchanged; pin `RULE_HASH = "8efc6e86f888"` in the generator.

**Why.** The canonical rule already implements the intended transformation: preserve the grid and fill each 4-connected zero component that does not touch the border with 7. Baseline rule smoke and authority sync were green, so the defect was the sampler and its contracts, not the authority.

**Alternatives rejected.** Rewriting the Racket rule to match the old frame sampler would narrow the task and break authority. Adding special cases for rectangles or wall colors would encode shortcuts rather than the topology.

**Probe.** Final authority sync is green; authority-set SHA-256 stayed `82ef7876208bb0a01d86413c39dec9c495032297dc58f243154c012fc6ea4420`. The independent probe matched real Racket on 37/37 retained inputs.

**Limit.** A normalized rule hash binds the selected source, but does not itself certify every future sampler input.

## D2 — Replace random frames with a constructive topology curriculum

**Choice.** Use four deterministic profiles: `unit_plus_tall2`, `wide2_plus_bent3`, `unit_plus_bent4`, and `bent4_plus_tall2`.

**Why.** The old rectangles labelled data correctly but supported multiple wrong explanations. Every new profile constructs two true holes plus an open-bbox decoy. Across the schedule, examples teach multiple holes, multi-cell filling, nonrectangular holes, mixed-component enclosure, fixed output color 7, border preservation, and 4-neighbor rather than 8-neighbor zero connectivity.

**Alternatives rejected.** Pure random wall growth made it hard to guarantee witnesses and exact axes. More rectangle variants still left rectangle-only and bounding-box rules viable. Rejection sampling was avoided because a small constructive grammar gives deterministic coverage and cheap replay.

**Probe.** The semantic gate passed all declared witness/rival requirements on 600 draws. The 300-lesson census found zero ambiguities in production or 1,500 held-out rotations.

**Failure mode / limit.** The fixed four-profile schedule is finite and ordinary draws always have exactly two holes. It does not prove identifiability against undeclared rules or broader count extrapolation.

## D3 — Keep only observable exact axes

**Choice.** Expose `grid_h` and `grid_w` in 9..14, four `scene_profile` values, and two `palette_kind` values. Reject unknown keys. Declare no incompatible combinations because every cross-product boundary is constructive.

**Why.** The baseline advertised singleton, alias, dead, and negative-overlapping controls. A training or debugging control is useful only when its requested value is recoverable from returned pixels.

**Alternatives rejected.** Retaining `texture`, `density`, `position_bias`, `n_frames`, or palette-count aliases would preserve inert metadata. Marking them diagnostic would still enlarge the public surface without helping lesson construction.

**Probe.** `observe_overrides()` reconstructs all four axes. The final matrix accepted 12,150/12,150 draws over 135 cases and three bands with zero findings/warnings; unknown keys were rejected.

**Failure mode / limit.** Dihedral orientation and embedding offset remain stochastic implementation details, not exact public controls.

## D4 — Reserve color 7 and use two three-color palettes

**Choice.** Input palettes are `canonical=(2,4,6)` and `broad=(1,8,9)`, permuted per draw; 7 never appears in input.

**Why.** Reserving 7 makes the fixed fill color directly learnable and prevents “preserve an existing 7 object” ambiguity. Three input colors match the canonical palette-size envelope and permit a main wall plus two accent components for cooperative enclosure.

**Alternatives rejected.** A single wall color cannot refute same-component enclosure. Arbitrary colors including 7 blur input preservation versus output creation. Larger palettes moved the sampler away from canonical profiles.

**Probe.** Exact palette overrides are pixel-observable and pass the full override matrix. Final profile-floor input palette sizes match canonical 3–4 total colors including background.

**Failure mode / limit.** Only two palette sets are represented; hue-specific generalization outside them is untested.

## D5 — Anchor each lesson cycle to a canonical profile

**Choice.** Slot 0 is always 9x11 with three nonzero colors; other slots vary dimensions by difficulty within 9..14.

**Why.** The baseline had zero exact canonical-profile support in medium and hard. A deterministic anchor guarantees every four-example schedule includes one exact profile without making all examples identical.

**Alternatives rejected.** Pure band ranges made exact support probabilistic. Restricting every draw to canonical dimensions reduced diversity and made profile an unnecessary shortcut.

**Probe.** Final profile floor: 16/60 exact, 36/60 envelope, with exact support in easy 4/20, medium 7/20, and hard 5/20.

**Failure mode / limit.** Hard examples can be larger than the canonical envelope by design; strict-canonical-like coverage is therefore 46.67%, not 100%.

## D6 — Make rivals executable and source-bound

**Choice.** Declare thirteen `SEMANTIC_RIVALS`/`LESSON_COMPETITORS`, six `CANONICAL_SHORTCUTS`, eight witness predicates, and a `lesson_identifiable()` hook.

**Why.** Comments saying “this teaches topology” are not testable. The selected canonical pairs are simultaneously fit by rectangle-only, bounding-box, same-component, and 8-neighbor alternatives, so each generated lesson must contain counterevidence.

**Alternatives rejected.** Manual spot inspection is not reproducible. Model inference as the gate would be expensive and confound data quality with model capability.

**Probe.** Task tests verify every declared canonical shortcut actually fits all usable canonical pairs before requiring the generated schedule to refute it. The reusable probe checks all cyclic starts; the shared census checks production assembly and every query rotation.

**Failure mode / limit.** Rival enumeration is finite. A plausible undeclared rule can still survive.

## D7 — Join walls after the intermediate morphology failure

**Choice.** Connect main-color wall pieces and the open decoy through one exterior backbone, keeping two accent cells as separate color components.

**Why.** The first topology-correct implementation fragmented walls into a median of about seven objects, outside the canonical median of two, and its largest pieces were too small. The connected backbone restores canonical-scale morphology without altering the holes.

**Alternatives rejected.** Suppressing the distribution warning would hide real drift. Merging every color into one component would destroy the mixed-component enclosure witness. Enlarging isolated fragments would worsen object-count drift.

**Probe.** The retained intermediate battery failed `defect_lint` and `dist_gate`; the final rerun passed both. Final morphology diagnostic reports generated object-count median 2, component-size median 12.25, palette 3, area 90.

**Failure mode / limit.** Marginal morphology matching does not certify semantic similarity; that is why the semantic and lesson checks remain separate.

## D8 — Separate lawful grammar from strict canonical resemblance

**Choice.** `self_check()` accepts any rectangular ARC grid with nonzero walls, border-connected zero background, and at least one enclosed 4-connected zero region. `strict_canonical_like()` adds canonical dimension, palette, hole-count, and hole-area checks.

**Why.** A validator should enforce the rule domain, not just the current sampler. The strict hook is the appropriate place for distribution resemblance.

**Alternatives rejected.** Encoding the four sampler profiles in `self_check()` would reject lawful unseen topology. Keeping the baseline count-only check accepted singleton, short-line, and solid-block impostors.

**Probe.** Canonical inputs pass; final self-check, defect lint, grammar, strict semantic rate, and task-local mutation tests all pass.

**Failure mode / limit.** `self_check()` intentionally does not require every teaching witness; schedule-level tests do.

## D9 — Add portable tests and a reusable probe

**Choice.** Add `tests/test_generator.py` and `workspace/topology_probe.py` using source-relative/public helpers and the packet Racket wrapper.

**Why.** The general battery does not discover task-local tests automatically, and future agents need a one-command audit that preserves source hashes and checks cyclic schedules.

**Alternatives rejected.** Private `scripts` imports and fixed `parents[...]` path guesses would fail in copied runtimes. A Python oracle alone would not bind the Racket authority.

**Probe.** Final task-test snapshot: 110 passed, no skips. Probe: 400 generated inputs, 393 distinct, zero self-check/determinism/mirror failures, all profiles in each band, and 37/37 Racket parity.

**Failure mode / limit.** The probe schedule is deterministic and diagnostic, not a statistical guarantee.

## D10 — Preserve failures and honest solve boundaries

**Choice.** Keep the before battery, the intermediate 10/12 failure, TDD red logs, and both solve episodes. Do not claim private-query correctness.

**Why.** The intermediate morphology defect materially changed the final design. The exposed solve necessarily had earlier rule exposure from generator work.

**Alternatives rejected.** Deleting failed runs would make the repair path unverifiable. Manufacturing a failed solve would create false training evidence.

**Probe.** Blind solve: 3/3 visible, one revision, exposure no. Exposed solve: 4/4 visible, one revision, exposure yes, bound to the final generator hash. Both summaries report `last_reported_label: unknown`.
