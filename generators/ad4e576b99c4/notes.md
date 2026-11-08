# Working notes: ad4e576b99c4

## Current parametric extension — review-e622a7eb1a6fbedc

The task-local prototype adds shear_start_rows in {2,3,4}, with exact canonical
default 3. It preserves the mask, semantic colors, opposite-side move, split,
and border endpoint convention. Every existing dimension combination fits even
setting 2's maximum shift (8 + 7 <= 16). Inputs are independent of the setting,
which stays fixed per episode. Canonical generator and ledger are unchanged;
variants remain proposed/unapproved with training disabled.

Separate demo/query controls support 1–8 / 1–32 distinct inputs, with at most 64
attempts per input. The first demo has a noncanonical mask against fixed-comb
copying. Four default queries cover both sides and heights 4,10,6,8. All accepted
labels come from real Racket. The certificate fits 14 explicit candidates using
demos only, then checks survivors on query inputs. This is finite candidate
evidence, not universal identifiability.

The writer regenerates whole episodes before exporting separate public/private
data; exact visible-byte hashes define public filenames. The retained batch has
three settings, two demos and four queries each, on six paired inputs. See
workspace/parametric/evidence/manifest.json and the adjacent README.

Final checks: 36 focused tests pass; 24 independent boundary comparisons agree
with Racket, and the oracle matches three retained canonical pairs. Adversarial
review found boolean/float demo outputs accepted through Python equality.
Both regression cases failed before the fix and pass now; exact cell types and
matching shape are checked before source loading. The return retains the red
tests, repair, and independent re-review. Unchanged production batteries and
peer suites were not run.

Next useful action: maintainer review of the parameter semantics and finite
rival set before a production adapter or variant/training admission. No blocker
remains in this prototype scope.

## Current rule and domain

The lawful input is a rectangular 16–22 by 16–22 split field using exactly colors 1, 5, and 6. The lower 3–6 rows are solid 6. A 4-connected color-5 mask with a full top row is flush left or right, occupies every row of its bounding box, and ends immediately above the split. The Racket authority moves that exact mask to the opposite edge, shifts mask rows after the first three one cell inward per row, and paints the exposed part of the first 6 row color 9.

`RULE_HASH = 6de9bdaa4c45`; Racket remains the label authority. `rule_mirror` is supplementary geometry for tests and probes only.

## Reversed baseline decision

**Prior choice:** version 2.0.1 generated a zero background with a single color-6 marker and a fixed P-pentomino, then described a different stratification/slide rule. That source did not inhabit the canonical split-field domain, omitted the rule pin, advertised controls that were not trustworthy, and produced objects far smaller than the canonical masks.

**New choice:** version 3.0.0 is a constructive split-field sampler with exact observable controls for `grid_h`, `grid_w`, `bottom_rows`, `patch_width`, `patch_height`, and `side`. Every advertised Cartesian combination is feasible, unknown/coerced overrides are rejected, and `self_check` validates the actual task geometry.

**Reason and evidence:** the before battery retained lint and defect-lint failures under `checks/before/`; the final source hash `724983291a9a40a55a057de4ea299e8cb3d54effb74e949b44f4d5e508d22cfc` is all-green on the 12-stage after battery and passes 55 portable task tests (`checks/after-v1/`, `checks/task-tests-v1/`).

## Teaching decision

All three canonical pairs reuse one five-column comb, so the strongest plausible canonical-fitting rival is `fixed_public_comb`: infer placement and shear but always stamp the public comb instead of copying the source mask. The retained exact witness is `counterexamples/fixed-public-comb.json`; the independent Python oracle and real Racket authority agree, while the rival differs at 15 cells.

The sampler cycles three profiles with period 3: `canonical_comb`, `odd_teeth`, and `alternating_bands`. Two demonstrations plus one query therefore contain all three profiles, and every query rotation leaves at least one noncanonical demonstration. Keyed spines vary the noncanonical masks without changing that teaching guarantee. The final 300-lesson census materialized 900 pairs and 900 query rotations with zero ambiguity or scoring errors; 723 inputs were unique (`checks/lesson-census-final.json`).

## Independent evidence

`workspace/reference_probe.py` checks replay, strictness, determinism, an independent geometry oracle, the retained rival, and optional real-Racket parity. On the final source it checked 1,000 generated inputs with zero self-check, strictness, determinism, or oracle mismatches; 668 inputs refuted the rival, 897 inputs were distinct, and all 52 selected Racket comparisons agreed (`checks/reference-final.json`).

## Limits and open findings

The masks come from three connected families rather than every lawful connected mask. The semantic claims cover declared executable rivals, not universal induction. Canonical demonstrations alone remain compatible with the fixed-comb shortcut; generated teaching examples supply the disambiguation. Approval is source-bound: this packet marks the unchanged generator approved; proposed parameter variants remain unapproved and are not admitted for training. No unresolved task-local blocker remains in this return.
## Current reviewer considerations

Source SHA-256: `724983291a9a40a55a057de4ea299e8cb3d54effb74e949b44f4d5e508d22cfc`.

# Decisions: ad4e576b99c4

## D1 — Replace rather than patch the baseline sampler

**Original choice:** a background-0 scene with one color-6 marker and a fixed P-pentomino, apparently intended as a generic slide/stratify task. The original rationale is not retained; `notes.md` contained no design history.

**Alternatives considered:** preserve that scene and revise only metadata; minimally recolor it; or build from the canonical geometry. The first two would leave the generator outside the authority's actual input manifold and make passing labels accidental.

**Decision:** replace the sampler with a constructive implementation of the canonical split-field domain. The before lint/defect-lint failures and direct canonical comparison made this a root-cause correction, not a cosmetic refactor.

**Failure mode / limit:** this is a broad task-local rewrite, so regressions were controlled with test-first canonical/override expectations, a separate geometry oracle, and Racket parity rather than trusting the new implementation itself.

## D2 — Advertise only exact, pixel-observable axes

**Choice:** expose height, width, lower-band depth, patch width, patch height, and side. Every advertised value is exact and `observe_overrides` recovers it from the grid.

**Rejected alternatives:** expose mask profile as a public exact axis or keep vague texture/palette axes. The schedule profile is curriculum structure rather than a user-facing independent geometry control, while fixed colors are semantic roles under the selected authority.

**Probe:** the public override gate passed, and focused tests exercise joint low/high corners across `None`, easy, medium, and hard. Invalid/coerced inputs are rejected rather than silently normalized.

**Limit:** mask topology remains sampled rather than directly overrideable. That keeps the contract small but means callers cannot request every lawful connected mask.

## D3 — Use a fully constructive legal product

**Choice:** 16–22 grids, 3–6 lower rows, 3–7 mask width, and 4–10 mask height. These bounds make all advertised combinations feasible: at least 10 upper rows fit the tallest patch, and at least 9 horizontal cells remain when width is 16 and patch width is 7, exceeding the maximum seven-cell shear.

**Rejected alternative:** declare many incompatible combinations and resample. Constructive totality gives clearer exact-control semantics and avoids hidden rejection bias.

**Probe:** public override gate, 55 task tests, and 1,000-sample reference probe.

## D4 — Preserve canonical support while broadening defaults

**Choice:** strongly weight 16–18 square grids and width 5, but retain all rectangular dimensions and patch widths. Difficulty changes lower-band depth and patch height, not the rule.

**Rejected alternatives:** reproduce only the three public sizes; sample all values uniformly. Canonical-only shapes encourage dimension shortcuts, while fully uniform defaults made the 20-draw canonical-profile floor unnecessarily fragile.

**Failure mode / limit:** the square bias is deliberate and measured, not uniform. Exact overrides and occasional broad rectangles preserve support; downstream users should not infer a uniform prior.

## D5 — Teach against the fixed-public-comb rival

**Original public ambiguity:** all canonical demonstrations reuse the same comb mask, so “always stamp that comb” fits them exactly.

**Choice:** retain one canonical profile and add `odd_teeth` and `alternating_bands`, cycled with period 3. With two demonstrations and one query, every cyclic lesson contains all profiles; every held-out position leaves a noncanonical demonstration.

**Rejected alternatives:** random profile choice with rejection; make every sample noncanonical; use only one alternate mask. A fixed cycle makes the lesson guarantee exhaustive and replayable, while retaining canonical examples prevents distribution drift.

**Probe:** exhaustive cyclic-start/query-position unit test; 300-lesson census with 900 rotations; exact authority-backed witness in `counterexamples/fixed-public-comb.json`.

**Limit:** finite declared-rival evidence does not prove unique human interpretation. Other undeclared rivals may exist.

## D6 — Add keyed topology variation inside schedule families

**Choice:** vary spines in `odd_teeth` and sparse rows in `alternating_bands` using the generator context RNG. This preserves each profile's semantic distinction while avoiding repeated default grids.

**Rejected alternative:** fixed masks for all three profiles. The diversity gate exposed repeated inputs under that first implementation.

**Probe:** the failing diversity result was retained during development; the final gate is green and the final probe reports 486 distinct masks / 897 distinct inputs out of 1,000.

## D7 — Keep Python rule logic supplementary

**Choice:** implement `rule_mirror` and `workspace/reference_probe.py` independently for fast diagnostics, but continue to identify Racket as authority and verify a selected subset through the real runtime.

**Rejected alternative:** derive expected outputs only from the generator module. That would let a shared bug make tests self-confirming.

**Probe:** all three canonical pairs, explicit shortcut witness, and 48 generated inputs were compared with Racket in the final probe (52 total); focused tests also invoke the real authority when available.

**Limit:** the 52 Racket checks are a sample, not every generated grid. The independent Python oracle covered all 1,000 probe grids.

## D8 — Synchronize stale selected rule text, not canonical behavior

**Prior choice:** the selected base solution JSON contained a different text copy from the canonical `program_solution`.

**Choice:** copy the existing canonical source into both selected fields and mark it synchronized. No canonical ledger or transformation behavior changed.

**Rejected alternative:** waive the defect-lint warning. Source identity is part of the task authority contract, so leaving two divergent copies would make future maintenance ambiguous.

**Probe:** rule smoke, Racket lint, and authority sync all green in the final battery.

## D9 — Honest solve and audit boundaries

The blind task was solved before exposure. The later repair-task solve records earlier exposure `yes`, despite using only visible examples during that episode. Audit targets were inspected and reproduced but not edited. Private query labels were never opened.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/ad4e576b99c4/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
