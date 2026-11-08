# Current native review: abe8a3c35e86

## 2026-10-25 — successive canonical reflections

The current task-local native prototype is reviewer-ready with finite verified
evidence; exact-source owner acceptance is pending and training is not admitted.
Production version 2.0.0 remains unchanged at SHA-256
`7b0070d31baf4909cd9a87423f3fb5fb26f118a4062f6436c7ac1fd6d8318493`.
The supplied review index contains no existing audit rows. Its historical
approval record and every byte of the prior notes remain preserved below.

### Current rule, dependency, and teaching decision

`workspace/parametric/native_family.py` and its adjacent adapter expose
`{"passes":1}` and `{"passes":2}`. The default returns the exact 767-byte
canonical program, SHA-256
`eb5d6fb489a018776ff8676567076341973fa390ea38d12b5199abb7ab143f74`.
The alternative, SHA-256
`bb15706d94c8c28222a23149091c19a32885e29478e933120cc7661a168f5e60`,
executes that exact body, binds its resulting grid as the next input, and
executes the body again. Each pass considers all nonzero, non9 cells together,
prefers a strict column-side reflection, otherwise uses a strict row-side
reflection, and otherwise preserves the grid. Source cells remain; individual
out-of-bounds copies are ignored.

The intermediate grid changes the next branch. Successful quadrant column
copies make the motif straddle the pivot column, enabling a second row
reflection. If every column copy clips, the intermediate remains unchanged and
the next pass must again select the column branch. This distinguishes actual
state-dependent execution from forcing a second axis or drawing fourfold
symmetry directly. Empty motifs and neither-side states remain unchanged.

The native grammar accepts every exact built-in rectangular list of built-in
lists with axes 1..30, exact integer colors 0..9, and exactly one 9 pivot. It
includes the original examples, thin and singleton grids, multicolor and
disconnected motifs, and partial or total clipping. Generated episodes are a
constructive subset of that grammar. Seeds, settings, and counts reject wrong
types and unsupported values; labels and intermediates remain controller-side.

Four demonstrations are the supported minimum and ordinary default, with four
queries independently selectable; the API supports demos 4..6 and queries 1..4.
The four required cores cover a partially clipped quadrant, a fully
column-clipped quadrant with otherwise legal row copies, joint multicolor
row-only geometry, and an asymmetric neither-side state. A measured three-demo
counterexample explains the minimum: an erroneous else-row fallback fits the
first three but adds incorrect cells on a column-only two-pass query. The fourth
demo refutes it before query scoring. This is a finite teaching result, not a
universal lower bound. Optional demos are the singleton pivot and a substantive
30x30 column-only scene. The four query shapes are 7x9, 14x19, 23x27, and 30x30;
the full query bank is seed-shuffled before prefix selection. Independent input
streams and fixed episode settings preserve matched inputs across both modes.
Large scenes contain hundreds of colored cells and functional mirror space;
the fully column-clipped 30x30 query correctly remains unchanged.

### Current evidence and limits

All paths here are under `checks/abe8a3c35e86/` in the review packet.

- `native-and-audit.xml` records 124 passing tests, zero failures or errors
  (53 native-family tests and 71 independent audit tests).
- `sampler-v1.json` records 96/96 successful Python sampler requests across
  both settings, supported count combinations, and 16 seeds: 144 distinct
  inputs, 63 distinct query inputs, and 32 distinct 30x30 inputs. This probe
  checks structure and sampling; it does not independently certify labels.
- `teaching-v1/private/audit.json` freezes fits using the four demonstrations
  before scoring queries. Across four episodes, 40 reference labels and 120
  hypothesis fits produced 116 refutations and four intended-only survivor
  sets, with all 16 query scores correct. Its protected ledger records 478
  Racket executions, 536 requests, and 58 cache hits; candidate and runtime
  source hashes were unchanged. Equivalent hypotheses are disclosed as aliases.
- `three-demo-hole-v1/report.json` retains the actual frozen native bank's
  three-demo else-row counterexample and fourth-demo repair, verified by ten
  protected evaluations. `design_reflection_probe.json` separately records
  twenty protected evaluations on independent literal design scenes.
- `qualification/qualification.json` records four qualified jobs at the minimum
  four demos and four queries, with 48 protected evaluations. Its execution
  SHA-256 is
  `0caee45b33f99780f69a503331206dc8a05d39c9e1c901ea668de990b06627ee`.
- `causal/witness.json` and `causal/replay.json` retain two cases with explicit
  intermediate grids and disagreeing counterfactual labels. Construction and
  replay each executed four protected labels; status is `reviewer_replayed`.
  `preview-verify-v2-command.json` records successful verification of four
  preview episodes and sixteen single-query views. The initial incorrect CLI
  invocation and earlier failed test iteration remain available as history.

The read-only implementation review found no concrete semantic or contract
issues in native source SHA-256
`cb06eb859f0740ac9b079e4a2c76be4e1a848069ca4bed35bfc265bd82d3533f`.
The canonical Racket remains label authority; independent Python implementations
serve as diagnostic checks. Finite seeds, rivals, labels, and replay do not prove
universal identifiability, full coverage of the validator's grammar, universal
algorithmic depth, measured learning gains, or owner acceptance. Intermediate
interpretations remain reviewer arguments. These current prototype claims do
not revise the narrower production grammar described in the retained history.

## Preserved prior notes

# Working notes: abe8a3c35e86

## 2026-10-07 review repair

The selected 1.2.0 baseline sampled only motifs above or below the pivot and therefore exercised only horizontal reflection. It rejected some canonical inputs, advertised dead or overlapping texture controls, did not pin the canonical rule hash, lacked useful 7×7 support, and could not teach the canonical branch order. The canonical rule itself was not changed.

The 2.0.0 sampler is constructive. It generates connected 3–5-cell motifs in eight exact layouts: left, right, above, below, and four strict quadrants. Quadrant layouts satisfy both side predicates and are labelled by the canonical column-first branch, so they directly refute the strongest canonical-fitting shortcut: checking above/below before left/right. All exact override combinations in the declared domains are feasible and observable.

The production schedule repeats category pattern `Q,R,C,Q,R` over ten concrete layout roles (`Q` = both-predicates priority witness, `R` = row-only, `C` = column-only). A lesson uses four demonstrations and one query from five consecutive roles. Exhaustive task-local tests hold out each position from every cyclic start checked and compare against four declared rivals. Half the scheduled roles are forced to the canonical 7×7 scale to stay above the profile warning floor.

`workspace/reference_probe.py` is an independent Python geometry oracle. It does not import implementation helpers and supplies portable canonical-pair loading plus outputs for the intended rule and principal rivals. The Racket canonical rule remains label authority; the Python oracle is only a regression and diagnostic aid.

Limitations: identifiability is measured only against the declared finite rival set, not proved against every conceivable rule. The generator intentionally models the connected monochrome motif manifold of the canonical demonstrations; disconnected, multicolor, overlapping, or out-of-bounds cases are rejected rather than treated as training data.
## Current reviewer considerations

Source SHA-256: `7b0070d31baf4909cd9a87423f3fb5fb26f118a4062f6436c7ac1fd6d8318493`.

# Decisions for `abe8a3c35e86`

## D1 — Preserve the canonical authority

**Choice.** Keep the canonical Racket rule unchanged and pin `RULE_HASH = "eb5d6fb489a0"` in the generator.

**Rationale.** The baseline defect was distributional and contractual, not a wrong authority. Canonical examples and direct Racket execution agree on a two-branch conditional: left/right geometry reflects across the pivot column; only otherwise does above/below geometry reflect across the pivot row.

**Alternatives rejected.** Reordering the Racket branches to match the old vertical-only sampler would change the task and erase the priority distinction. Adding special cases in Racket would mask malformed generator inputs rather than repair them.

**Probe.** Rule smoke, Racket lint, and authority synchronization all pass in `checks/final-verification/`; the exact witness in `checks/shortcut-witness/racket.json` executed rule hash `eb5d6fb489a0`.

**Failure mode / limit.** The Python oracle is not authority. It is compared to canonical pairs and a selected Racket output, but a future rule change must update the pin and rerun those checks.

## D2 — Use constructive connected motifs, not rejection sampling

**Choice.** Generate one monochrome 4-connected motif of 3–5 cells from enumerated feasible offset sets, then choose a pivot from positions where both the source and selected reflection fit and remain disjoint.

**Rationale.** Every documented joint override becomes feasible and deterministic. Construction eliminates silent placement exhaustion, clipping, overlap, and accidental malformed returns.

**Alternatives rejected.** Randomly painting cells then retrying makes rare combinations brittle and can silently bias shapes. Keeping the old handcrafted vertical forms preserves the central coverage defect.

**Probe.** Exact overrides are exercised for all eight layouts in all four difficulty values by `test_every_exact_control_is_realized_in_every_band`; the final override gate is green.

**Failure mode / limit.** The declared domain intentionally excludes disconnected, multicolor, overlapping, and out-of-bounds motifs. Those are rejected by `self_check`, not interpreted as additional rule branches.

## D3 — Advertise only observable exact axes

**Choice.** Expose `grid_h`, `grid_w`, `motif_size`, `motif_color`, and `layout`; reject unknown axes, booleans masquerading as integers, wrong types, and out-of-range values. Recover all five values through `observe_overrides`.

**Rationale.** The baseline's `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` controls were singleton, aliases, or semantically dead. Honest axes are easier to test and safer for downstream dataset assembly.

**Alternatives rejected.** Retaining dead controls for compatibility would continue to misrepresent what a caller can request. Mapping several names to the same random source obscures which control is effective.

**Probe.** Final lint reports no warnings, final override contract passes, and invalid controls have explicit task tests.

**Failure mode / limit.** Exact overrides may reduce default randomness by design. No incompatible combinations are declared because all values in the Cartesian product are constructively feasible.

## D4 — Cover all branch classes and the priority case

**Choice.** Support `left`, `right`, `above`, `below`, `upper_left`, `upper_right`, `lower_left`, and `lower_right`. Treat quadrants as both-predicate cases and apply the canonical column branch first.

**Rationale.** The three canonical demonstrations establish both single branches but do not include a both-predicate input. Therefore the strongest plausible rival—row priority when both hold—fits all canonical pairs.

**Alternatives rejected.** Sampling only single-branch layouts leaves branch priority unteachable. Sampling quadrants but not declaring them semantically would produce correct labels without a check that lessons actually distinguish the rival.

**Probe.** `checks/shortcut-witness/oracle.json` contains an exact 7×7 upper-left input and both disagreeing outputs; `checks/shortcut-witness/racket.json` selects the column-priority output.

**Failure mode / limit.** Priority is established only on lawful connected motifs. No claim is made for malformed geometry in which neither branch predicate is true.

## D5 — Four demonstrations and a ten-role teaching schedule

**Choice.** Set `EXAMPLES_NEEDED = 4`. Repeat the ten concrete roles whose branch-category pattern is `Q,R,C,Q,R,Q,R,C,Q,R`. A lesson consists of four demos plus one query from five consecutive roles.

**Rationale.** Every five-role window contains two priority witnesses, two row-only cases, and one column-only case. After holding out any single pair, at least one of each decisive class remains. This distinguishes row-priority, column-only, row-only, and identity competitors under arbitrary query position.

**Alternatives rejected.** Independent random layouts can occasionally produce a lesson whose demonstrations all miss one branch. Three demonstrations are insufficient for this schedule to preserve all three decisive classes after every holdout. Hard-coding a single fixed lesson would sacrifice diversity.

**Probe.** Task tests exhaust held-out positions over repeated cyclic starts. The strict semantic gate checks 60 rotations with zero ambiguity; the larger census checks 1,500 with zero ambiguity.

**Failure mode / limit.** The census evaluates a finite named rival set. An undeclared adversarial rule may still fit finite demonstrations. The schedule is deterministic by `sample_index`, so downstream code should preserve consecutive assembly or rely on the verified rotation-safe five-pair window rather than arbitrary subsampling.

## D6 — Anchor canonical 7×7 support at half the roles

**Choice.** Force both dimensions to 7 on schedule roles 0, 2, 4, 6, and 8; allow caller overrides to take final precedence.

**Rationale.** The first repair had lawful canonical support in every band but only 8/60 exact 7×7 draws, a 13.3% rate below the gate's 25% warning floor. Anchoring every even role is deterministic, easy to audit, and leaves the other half available for broader size diversity.

**Alternatives rejected.** Increasing random weight alone left medium at 8/40 in the regression test and made the rate seed-sensitive. Forcing all roles to 7×7 would unnecessarily collapse dimension diversity.

**Probe.** The failed gate is retained at `checks/profile-floor-first/`; the test-first failure is retained at `checks/task-tests-profile-red/result.json`. The final profile stage is green.

**Failure mode / limit.** Dimension frequency is deliberately nonuniform. Exact dimension overrides remain honored for every role.

## D7 — Keep a separate independent oracle

**Choice.** Put `reference_probe.py` under the task workspace and prohibit it from importing generator implementation helpers.

**Rationale.** Tests should detect a shared implementation error rather than reproduce it. The helper also gives future agents a portable way to load canonical pairs and compare the intended and rival transformations.

**Alternatives rejected.** Testing private helper functions would validate implementation details instead of behavior. Reimplementing the oracle separately in every test would invite drift.

**Probe.** Canonical pairs are loaded through `reviewer_support.find_root` and `canonical_pairs`, so the same tests passed in the fresh extracted packet.

**Failure mode / limit.** The independent Python oracle can still share a conceptual misunderstanding; Racket comparison and canonical examples provide the external check.

## D8 — Preserve failed iterations and verify the handoff patch

**Choice.** Retain the original 54-test RED run, the profile-floor RED run, and the first failed fresh replay. Regenerate the final patch from the staged Git index so new files are included, then apply it to a clean isolated packet and rerun focused tests.

**Rationale.** The first manual `git diff` omitted untracked tests and the workspace oracle, proving that a green working tree is not sufficient handoff evidence.

**Alternatives rejected.** Deleting the failed replay would hide a packaging risk. Trusting filename lists or copying the whole repository would not test the actual delta contract.

**Probe.** `checks/fresh-replay/replay.json` records the first exit 5, final `git apply --check`, final apply, matching generator hash, six changed paths, and 63/63 passing tests.

**Failure mode / limit.** The fresh replay verifies source application and focused tests, not every full-battery stage a second time. The complete battery already ran against the same generator bytes.
