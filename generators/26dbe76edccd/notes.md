# Current account: 26dbe76edccd

## Intended rule and authority

On a rectangular color-0 background, every cell whose color is neither 0 nor gray 5 is a seed. Its color extends rightward through the row and stops immediately before the first gray 5; without a right-side gray, it extends to the border. The Racket authority was not changed. The generator pins canonical `RULE_HASH = "ff55fa477cae"`.

## Current generator domain

Version 2.0.0 emits 5–14 by 7–18 grids with 2–5 active seed rows and 1–3 non-terminating gray distractors. The exact advertised controls are `grid_h`, `grid_w`, `rays`, and `extra_blockers`; every control is observable, legal endpoints are constructive, unknown names and invalid scalar types fail loudly. Defaults use an eight-profile cycle: six canonical-scale anchors and two endpoint probes.

Each generated input includes four task-domain witnesses: a one-cell ray before a blocker, trailing background after a blocker, a later second blocker, and an open ray to the border. These refute the declared rivals `skip_unit_gap`, `ignore_blocker`, `last_blocker`, and `require_blocker` on every grid. The first and third rivals also fit all canonical pairs, so their counterexamples are required teaching support rather than cosmetic diversity.

## Reversed decisions

The prior 1.1.0 source advertised many legacy controls (`palette_kind`, `palette_size`, `n_distinct_colors`, textures, and wider size/count ranges) that were ignored, silently swallowed, or rejected at stated boundaries; `texture=no_seeds` also contradicted `self_check`. The new choice is to remove that false surface instead of pretending to support it. Evidence began with unresolved audit `review-bb6472c904793673:v0001`, was reproduced by the before battery, and is retained in `counterexamples/review-e892df8ea5d378da/control_and_semantic_regression.json`.

## Assumptions and known limits

The sampled domain is deliberately sparse: at most one seed per active row, seed colors are distinct within an input, and semantic colors 0 and 5 are fixed. Overlapping rays, multiple seeds in one row, duplicate seed colors, alternate directions, and color-role permutations are not claimed. The four executable rivals are finite probes, not a proof of unique induction against every possible hypothesis. A 300-lesson census (100 per band, three demonstrations plus one query) found no declared-rival ambiguity in production order or any of 1,200 query rotations; it does not enumerate all seeds or undeclared rules.

## Verification

Final generator SHA-256: `f4b6226be045518d17b247f41c21acdf8de5c6091554d5658962fe64b1a33a81`. The final 12-stage after battery is all green; portable task tests pass 47/47; the post-repair visible-only solve passes 3/3 examples on its first genuine hypothesis. No open blocker is known.
## Current reviewer considerations

Source SHA-256: `f4b6226be045518d17b247f41c21acdf8de5c6091554d5658962fe64b1a33a81`.

# Decisions: 26dbe76edccd

## D1 — Replace the false legacy surface with exact behavioral controls

**Prior choice.** Version 1.1.0 exposed palette, count, position, density, and texture controls in addition to grid/seed controls. The original rationale is unknown. In practice, several were ignored, unknown names were accepted, stated endpoints were rejected by narrower internal draws, and `no_seeds` failed the generator's own validator.

**New choice.** Advertise only `grid_h` (5–14), `grid_w` (7–18), `rays` (2–5), and `extra_blockers` (1–3). Validate every request before constructing `GenCtx`; reject bools, floats, strings, explicit `None`, negative sample indices, unknown difficulty values, and unknown axes. Provide `observe_overrides` so exactness is independently measurable.

**Alternatives rejected.** Implementing all inherited generic axes would add color and texture variation with little connection to this rule and would preserve misleading concepts such as `no_seeds` in the ordinary domain. Keeping ignored aliases for compatibility would continue silent data-stratum collapse. Exact, smaller controls are safer for dataset assembly.

**Probe/failure mode.** Endpoint and invalid-scalar parametrized tests plus the official override and defect-lint gates cover this decision. A future axis must be both constructive and observable or be explicitly declared incompatible.

## D2 — Keep semantic colors fixed

Background 0 and blocker 5 are roles in the canonical authority, not freely permutable decoration. I retained them rather than add a palette axis that might change rule meaning. Seed colors vary over the remaining ARC colors and are distinct within an input. A future color-role expansion would need Racket-checked counterfactuals and a role extractor; legal color values alone are insufficient.

## D3 — Force all four witnesses into every grid

The canonical examples admit at least two plausible shortcuts: skip a ray when only one cell lies before the blocker, and stop at the last rather than first gray blocker. I added two more common rivals—ignore blockers and require a blocker—and made every generated grid refute all four through four concrete witnesses.

I chose per-grid coverage rather than a lesson schedule because dataset assembly may shift start positions or query order. A schedule-only witness can disappear from demonstrations even when overall frequencies look healthy. Per-grid witnesses make every three-example lesson robust to those four rivals and made all query rotations pass. The cost is a more structured sparse domain; that limitation is explicit.

## D4 — Preserve a sparse, one-seed-per-row manifold

The generator emits 2–5 active rows, one colored seed per active row, with distinct seed colors. This isolates the rightward casting law and matches the canonical structure. I did not add multiple seeds in one row, repeated colors, crossings, or altered directions because the selected authority's behavior on interactions is not pedagogically established by the canonical pairs. Such expansions could be lawful but should be separate, Racket-labeled experiments with new rivals and validators.

## D5 — Canonical-centered defaults plus exact endpoint probes

Defaults follow an eight-profile cycle: six 6×8/7×9 canonical-scale profiles and two 5×7 / 14×18 endpoint profiles. This keeps 75% of default samples close to native scale while preventing declared size ranges from becoming dead metadata. Difficulty changes nuisance geometry probabilities rather than rule semantics.

An earlier iteration declared a three-step lesson schedule. The semantic gate correctly required schedule-period enumeration, but the declaration served no necessary curriculum behavior. I removed it rather than manufacture schedule semantics; the final cycle is a sampling implementation detail, while identifiability is per grid.

## D6 — Do not change the Racket authority

Canonical outputs, rule smoke, and authority sync all agreed with the intended first-gray-or-border law. The defect was in the generator contract and teaching distribution, not label authority. I pinned `RULE_HASH = "ff55fa477cae"` and left the Racket rule untouched.

## D7 — Build reusable task-local diagnostics

`workspace/reference_probe.py` independently implements the authority mirror, four rivals, override observation, malformed examples, and teaching checks without importing generator internals. Tests compare generator declarations against that independent probe. This gives future agents a small executable specification and catches self-consistent bugs that generator-only tests could miss.

## D8 — Treat finite rival checks honestly

The semantic gate and census establish no ambiguity only against four named deterministic rivals over sampled lessons. They do not prove unique induction against arbitrary programs. Reports and notes therefore state exact denominators, ordering, rotation policy, and domain restrictions instead of claiming universal identifiability.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-bb6472c904793673:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `6b4900d80aec81dbcbc78d8072ce2d83dac83a5e44860d49415245a237833af3`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Current sourcef4b6226be045518d17b247f41c21acdf8de5c6091554d5658962fe64b1a33a81 explicitly replaces the inert legacy palette/texture/count surface with four exact positive axes, constructive endpoints and unknown/scalar rejection; current notes retain the old control witness. New reviewer-bound strict audit reports12 stages green and14 selected audit tests. Resolves the named old-source6b4900d80aec81dbcbc78d8072ce2d83dac83a5e44860d49415245a237833af3 public-contract finding only; no fresh maintainer run or claim of universal coverage.

### Assessment or prior finding

## 26dbe76edccd

**Classification: reproduced defect — the advertised override domain is mostly false, unknown keys are swallowed, and one advertised texture violates the generator's own validator.**

The current audited generator SHA-256 is `6b4900d80aec81dbcbc78d8072ce2d83dac83a5e44860d49415245a237833af3` (version 1.1.0). The official compact override gate failed. Its log reports more than 17,306 additional primary findings and 95,430 legacy multi-axis rejections with no declared incompatibility; it also confirms that the unknown key `__override_contract_unknown_axis__` is accepted.

A smaller replay at seed 17/sample 0 is easier to inspect. The base grid is 6x10 with four non-marker colors `[1, 6, 7, 9]`. Each of these lawful declared requests returns byte-identical output: `palette_kind="warm"`, `palette_kind="cool"`, `n_distinct_colors=1`, and `palette_size=1`. An unknown `bogus_axis=1` also returns those same bytes. Meanwhile declared boundaries such as `grid_h=4`, `grid_h=14`, `grid_w=5`, `grid_w=18`, and `seeds=10` raise `ValueError` because the implementation narrows them to its default draw ranges. Finally, advertised `texture="no_seeds"` returns a 7x10 grid that `self_check` rejects with `expected at least 2 seed rows`.

**Impact.** Dataset assembly cannot rely on the declared control surface: requested strata may silently collapse to one distribution, lawful boundary jobs may fail, typos may look successful, and a named degenerate can emit data outside the generator's own accepted domain.

**Evidence and replay.** `checks/audit/26dbe76edccd/finding.json` and `checks/audit/26dbe76edccd/reproduce.py`; run from the return root with:

```text
PYTHONPATH=repo/shared/runtime python3 checks/audit/26dbe76edccd/reproduce.py
```

The official gate receipt is `checks/audit/26dbe76edccd/override-current/result.json`; its large detailed case file is compressed and hash-mapped in `checks/COMPRESSED-EVIDENCE.json`.

**Suggested repair.** Either implement every advertised axis over its full valid range and reject unknown keys, or shrink `AXES` to exact observable controls. Degenerate textures should be removed from the normal contract or made valid under `self_check`. The audit target was not modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-bb6472c904793673-v0001/audit_assets.json), manifest SHA-256 `f449b3c4534369fd81a7e60917d05be7977b434dfae3976be0f5207d88bc9857`.
<!-- arcpuzzles-current-audit-assessment:end -->
