# Working notes: 646eeb47599b

## Current rule and domain

Version 4.1.1 retains canonical Racket authority `610c94f513d9`. Two adjacent
green cells set the launch axis, with rays in both directions. Orange cells on
the rays become green. A cyan collision splits at the last open cell into each
open perpendicular direction; boundaries absorb. Cyan cells may touch. Traversal
reads the original input and tracks direction, so crossings and cycles are legal.

Inputs have 5..8 rows and columns, exactly two adjacent green cells, 4..14 cyan
cells, and orange field cells. At least one orange cell must change. Fixed colors
3/7/8 carry task meaning; they are not palette roles to permute. The Python optics
helper is diagnostic and selects inputs; Racket alone supplies reference labels.

## Reversed decisions and evidence

- **G1, exact controls:** 4.0.0 erased a wall to force an open initial step, so
  easy seed 11 with `n_walls=4` returned three walls. Now sample the exact wall
  count and reject nonchanging scenes without editing walls. Valid explicit pins
  use global bounds in every band; difficulty controls only default preferences.
  A pixel-derived observer exposes all four exact controls. Coerced integers,
  invalid sample indices, and unknown controls are rejected. Remove inert
  palette/texture declarations instead of promising fixed-color variation.
- **G2, lawful immediate turns:** the prior validator rejected scenes with both
  initial axial exits blocked, even though cyan can split directly from a seed.
  Now validate actual reachability. `counterexamples/reference-cases.json` retains
  19 independently Racket-labelled controls, including this case and cyan clusters.
- **G3, teachable lessons:** ordinary independent draws admitted centerward-only,
  axis-edge-only and cluster-absorption shortcuts. They each fit all six canonical
  records (three unique pairs). Unpinned indices 0 and 1 modulo 3 now refute all
  nine executable rivals; index 2 is a broad lawful draw. Explicit pins bypass
  this teaching filter and request individual lawful grids only.
- **G4, first-component gap:** 4.1.0 passed its eight-rival checks, but the broader
  search found a real lesson where applying changes only in the first input
  component fit all demonstrations. Preserve that exact intermediate lesson in
  `counterexamples/first-component-lesson.json`; 4.1.1 adds the input-only rival
  to the teaching filter. Do not treat the intermediate pass as final evidence.

## Teaching policy and limits

Production lessons use three demonstrations followed by one query. Any four
consecutive accepted, unpinned indices contain at least two teaching draws; holding
out any one pair leaves a demonstration refuting every declared rival. This
argument requires successful generation and consecutive accepted indices. It
does not cover arbitrary skips, fewer demonstrations, or pinned lesson assembly.
The 8,192-candidate cap raises visibly on exhaustion; all-seed success is unproved.

Teaching selection deliberately favors interior seeds and field connectivity
that distinguishes the rivals. The broad third retains boundary seeds, touching
walls and immediate turns, but the mixture remains biased toward these finite
teaching distinctions. No universal identifiability or training approval is claimed.

Final-source evidence in return `review-c2c0eb31e8898a11`: 38 focused tests pass,
including the portable task-test stage; the reusable
`workspace/probe_laser_contract.py` passes all 1,056 exact-control combinations
(352 unique inputs) and 96/96 Racket parity cases. The production census has
0/300 ambiguous lessons and 0/1,200 ambiguous rotations against nine rivals, with
1,200 unique inputs. Fixed seed 0 covers all three start residues in each band:
0/9 ambiguous lessons, 0/36 ambiguous rotations, 18 unique inputs. Counts are
separate and must not be added as independent coverage.

## Historical shared-gate finding

The returned final battery was 11/12 green: `semantic_gate` exited 1 with only
`declared_period_not_enumerated`. The separate final-source schedule census is
complete and passes. That edition could not ingest the receipt; its warning
remains preserved as historical evidence. Shared source was not edited in the
return. See `FEEDBACK_TO_CODEX.md` F1 and `RESULTS.json`. No source
or rule repair finding remains reproduced in the tested scope.

## Maintainer decision on returned schedule evidence

Accepted review `review-c2c0eb31e8898a11` on reviewer-reported evidence. Its supplemental `checks/schedule-census-final.json` matches the integrated generator and selected canonical rule: three starts in each band, nine lessons and 36 required rotations, with no reported ambiguity or scoring errors. The shared check now accepts it through `--schedule-census FILE --schedule-seed 0`, validating current source/rival bindings, population, completion and outcomes. Coverage is explicitly `complete_fixed_seed_reported`. The original 11/12 battery is not rewritten or reclassified. Labels were not re-executed in this maintainer check; separate target audits remain unresolved. See [the shared receipt contract](../../docs/SEMANTIC_GATE_CONTRACT.md#consuming-a-fixed-seed-schedule-census) for the exact scope and rejection policy.
## Current reviewer considerations

Source SHA-256: `aa9940392c76ce0e2006361be2bb1c4e874ea6bb0969d96106a62783941744af`.

# Decisions: 646eeb47599b, 4.0.0 → 4.1.1

The final generator SHA-256 is
`aa9940392c76ce0e2006361be2bb1c4e874ea6bb0969d96106a62783941744af`.
The pinned baseline is
`2ba23898f37c2e1db520513f83909dbb02d14cc828daf12660ba2788150b9bcf`.
No prior review supplied a substantive decision record for this selected source;
the initial `notes.md` was a template. The original rationale below is therefore
an inference from code, where stated, rather than attributed author intent.

## Domain and sampling choices

| Choice | Prior behavior / probable rationale | Final decision and reason | Evidence and limitation |
|---|---|---|---|
| Dimensions | Difficulty narrowed both defaults and valid pins, presumably to scale size. | Retain easy 5..6, medium 5..8, hard 7..8 defaults; honor explicit 5..8 dimensions in every band. | G1: 12 cross-band regression cases and the 1,056-combination probe. No unrequested expansion beyond 5..8. |
| Wall count | Sample 4..8 / 6..12 / 9..14 by band, then sometimes erase one wall to open a ray. | Sample exactly the requested count; reject a nonchanging layout without deleting walls. Exact pins span 4..14 in every band. | Baseline seeds 11/38/28 return one wall too few; final controls pass. Cyan adjacency is lawful, so no invented separation constraint. |
| Seed | Any adjacent pair, with an axial-open-step repair. | Teaching draws use interior seeds; broad and pinned draws retain arbitrary adjacent seed placement. | Interior launches expose centerward and edge-gated rivals. The broad third preserves boundary support. |
| Nonidentity | Self-check assumed blocked axial exits imply identity. | Use checked ray reachability, which includes immediate cyan turns. | G2: 19 public Racket controls; final parity samples include seven such blocked-but-changing inputs. |
| Colors | Fixed 3/7/8 semantics coexisted with inert palette and texture controls. | Keep task colors fixed and remove unsupported controls; reject their use. | A color permutation would alter task symbols. No color-role counterfactual is claimed. |
| Input types | Non-strict numeric helpers and sample-index coercion silently accepted floats, strings and bools. | Use the shared strict integer helper and explicit seed/index validation; reject unknown axes. | Focused tests establish rejection and pixel-level control effects. |
| Rule implementation | Canonical Racket gives the desired behavior. | Leave all authority bytes unchanged. A Python diagnostic evaluates candidates and executable rivals, never supplies production labels. | Six canonical records and 19 controls, then 96 new final-source samples match Racket. Finite parity is not an all-input proof. |

## Why independent random examples were insufficient

G3 is a lesson defect, separate from the exact-control defect. All six canonical
records represent three unique labeled pairs; every seed touches an axial
boundary. A centerward-only launch therefore fits them, as does a rule that
activates only at that boundary. Absorbing a cyan cell when it belongs to a
touching cyan cluster also fits every canonical record. Ordinary baseline
production confirms the gap: easy seed 30 gives three fitting demonstrations and
a disagreeing query for the first two rivals; easy seed 3 does the same for
cluster absorption. `checks/reviewer-analysis/production-*.json` retains actual
public `Catalog.generate` lessons, accepted indices, labels and comparisons.

Simply increasing the number of independent draws would reduce an observed
frequency without ensuring a distinguishing demonstration. Forcing every input
to refute every rival would remove easy and boundary cases. A period-three
teaching/teaching/broad schedule gives a concrete compromise: teaching draws
refute all nine declared rivals, while one third retains broad lawful sampling.
There is no silent fallback when the teaching search exhausts 8,192 candidates.

## The ninth rival changed the repair

Intermediate 4.1.0, hash
`d57ac6bb39490f4f0cf6b85db2d164d9b25c9d44278332a2ed90e6c128581121`,
passed 37 tests and its 300-lesson/1,200-rotation census against eight rivals.
The broader semantic search still found first-object attribution ambiguities.
That search mutates known labels; it is not itself an input-only solver. I
derived an independent rival for this task: compute the laser changes but retain
only changes in the first row-major, same-color, four-connected input component.
All changed cells were orange, so this is equivalent to the three relevant
first-object attribution mutations on this domain.

The retained easy lesson at seed 183699065748891, requested start 11, makes this
rival fit three demonstrations and fail the query. The regression failed before
the rival was added. Version 4.1.1 includes it in the executable contract and the
teaching filter; 38 tests now pass. The older failures and the intermediate
census are preserved, not relabeled as final-source evidence.

## Lesson assembly and what was actually established

The supported assembly has three demonstrations followed by one query, using
unpinned production draws. In any four consecutive indices there are at least
two teaching slots. Holding out any one of those four examples leaves at least
one teaching demonstration, which refutes each declared rival. This argument
assumes successful generation and consecutive **accepted** indices. It makes no
claim for arbitrary skipped indices, selected subsets, fewer demonstrations,
or explicit-pin lessons. Every retained final census window has four accepted
consecutive indices and no materializer rejections.

| Final-source measurement | Sampling scope | Production | Query rotations |
|---|---|---:|---:|
| Semantic smoke | 12 lessons, four per band; 600 strict-profile inputs | 12/12 identifiable | 0/48 ambiguous, required policy |
| Larger census | 100 lessons per band; requested starts 0..99; deterministic per-lesson SHA-derived seeds recorded in the report | 0/300 ambiguous | 0/1,200 ambiguous |
| Full declared-period enumeration | Seed 0; starts 0, 1, 2 in easy/medium/hard | 0/9 ambiguous | 0/36 ambiguous |

The larger census has 1,200 unique inputs. Enumeration has 36 pair occurrences
but only 18 unique inputs because windows overlap. These denominators are not
additive coverage. Nine unique input-only rivals are registered in several
namespaces; the census's 21 registry entries are **not 21 distinct hypotheses**.
The final generic search has no ambiguous lesson against its additional tested
label mutations; its first-color-only mutation is support-equivalent because
green is the only new color. Finite search cannot establish universal induction.

Final evidence: `checks/lesson-census-final.json.gz` (restore using the compression
manifest), `checks/schedule-census-final.json`, and
`checks/after-final/checks/646eeb47599b_after_semantic_gate.json`.
The unchanged shared semantic gate always warns when a schedule period is
declared, without consuming completed enumeration. Consequently the full battery
still exits 1 with 11/12 green stages. I retained truthful schedule metadata and
the complete supplemental receipt instead of suppressing the warning. F1 names
the shared-tool change needed; acceptance requires that narrow decision.

## Self-review and rejected shortcuts

Rich filtering favors interior seeds and particular orange connectivity; this
is a deliberate distribution restriction, and the ninth rival can increase
top-left/corner structure in teaching examples. The broad third preserves
unrestricted seed placement, touching walls and immediate turns, but does not
erase that bias; no all-seed search-success guarantee or absence of undeclared
shortcuts is claimed. The exact final generated witness in
`counterexamples/generator-shortcuts.json` distinguishes all three canonical-fit
rivals and is covered by the independent 96-case reference probe.

I rejected palette randomization, forbidding cyan clusters, changing canonical
examples, modifying Racket, or narrowing valid pins merely to make a checker
green. I also rejected deleting the declared schedule period to hide the shared
warning. The final independent code review found no blocking implementation
defect within the inspected scope (`checks/final-code-review.md`).

## Reusable work and separate obligations

`workspace/probe_laser_contract.py` reads the generator's current rival mappings,
checks every joint exact-control combination from pixels, and compares direct
draws against public `Catalog.apply`. It records sources, seed/index/overrides,
unique-input counts and failures, and refuses to overwrite its output. Its
successful use on both eight-rival and nine-rival versions demonstrates that
future reviewers need not edit a duplicated rival list.

The blind solve was completed before source exposure: 4/4 visible examples,
two masked queries executed. The final exposed solve is bound to 4.1.1: 3/3
visible examples, two masked queries executed, earlier exposure declared yes,
no reference consultation during solving. Both have one genuine revision;
hidden correctness is unknown. The two assigned audits are findings-only and
leave their source bytes unchanged. `AUDIT.md` and `RESULTS.json` separate their
witness-search scopes from this repair's coverage.


## 2026-10-22 review-3081544e90ba3334 — parametric branch policy evidence

- The approved canonical `generator.py` was intentionally left byte-for-byte unchanged.
- Added an isolated prototype under `workspace/parametric/` for episode-level `branch_mode`: `split_both` (canonical), `clockwise_only`, and `counterclockwise_only`.
- Input sampling is independent of the hidden setting; each retained demonstration and query makes all three settings predict distinct outputs.
- Added standalone Racket implementations, a Python reference simulator, public/private episode projections, a same-input setting witness, and a verifier.
- Added focused tests under `tests/test_parametric_branch_mode.py`; official and local receipts are under `WORK/checks/parametric/branch-mode-v1/` and `WORK/checks/after-reconstructed/`.
- A later tool-container reset removed the first extracted workspace; the implementation and receipts were reconstructed deterministically from the intact packet, with the blind-solve record explicitly noting that recovery.
