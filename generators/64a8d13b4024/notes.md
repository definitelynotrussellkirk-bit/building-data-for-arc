# Working notes: 64a8d13b4024

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-24 review repair

### D1. Canonical rule and authority

The unchanged rule counts colors 1, 2, and 3 globally, then emits a fixed 6×3 grid with bottom-aligned colored columns. The independent oracle in `workspace/reference_probe.py` matches all five labeled canonical pairs. No Racket or canonical-data edit was needed.

### D2. Remove non-observable and degenerate axes

The prior metadata advertised palette aliases, constants, position aliases, density, and three degenerate textures. Those controls were either inert or bypassed the advertised dimensions/counts. The reviewed contract exposes only five pixel-observable integer axes: `grid_h`, `grid_w`, `n1`, `n2`, and `n3`.

Rejected alternative: retain old names as compatibility aliases. Silent aliases are precisely the failure the override audit is meant to expose; callers now receive an explicit unknown-axis error.

### D3. Full-domain exact overrides

Every legal value is accepted in every difficulty band. Sampling bands weight defaults but never narrow the override domain. Literal integers are required; bools, strings, floats, unknown keys, and out-of-range values are rejected before `GenCtx` construction.

Baseline evidence: endpoints 8/14 failed under branch-local bounds, unknown keys were ignored, and values such as string counts were coerced. Repaired focused tests force both dimension endpoints and count endpoints in all four bands.

### D4. Equal counts are lawful

The old generator rewrote `n3` whenever `n1 == n2 == n3`, even though the canonical set contains a lawful 2/2/2 example and the rule is unambiguous. The rewrite was removed. Exact requests such as 3/3/3 now remain 3/3/3 in returned pixels and labels.

### D5. Period-three semantic curriculum

`SCHEDULE_PROFILES = (count_six, adjacent_pair, border_scatter)` and `EXAMPLES_NEEDED = 3`. The first two profiles force one unpinned count to six, rotating the selected color deterministically; the third varies border geometry without forcing six. Thus every sliding window of three default demonstrations includes the sixth output row, and every four-pair episode contains at least two such witnesses, so holding out any one pair still leaves evidence.

The canonical-fitting rival `cap_bars_at_five` matches all five published pairs because none has a count above five. Every scheduled lesson and every held-out query rotation refutes it. This is declared consistently through `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `WITNESS_RIVALS`.

### D6. Pixel-derived validation and observation

`self_check` and `strict_canonical_like` accept rectangular 8–14 grids containing only literal colors 0–3 with each counted color present 1–6 times. `observe_overrides` recovers all five exact axes from pixels. Validators do not depend on generation metadata and do not mutate their input.

### D7. Independent reusable probe

`workspace/reference_probe.py` deliberately does not reuse generator parsing or rule helpers. It loads labeled canonical pairs, independently counts colors, constructs labels, implements the cap-five rival, audits determinism and diversity, and can target an alternate `generator.py`.

Evidence retained under `WORK/checks/64a8d13b4024-*`:

- RED: 27 failed / 22 passed, including branch-limited endpoints, equal-count rewriting, ignored unknown axes, and missing semantic contracts.
- GREEN: 49/49 focused tests passed.
- Independent audit: 180 samples per band (720 total), zero validation errors, zero nondeterminism, 720 distinct inputs; all five canonical pairs matched the independent oracle and the shortcut.

### Known limits

The sampler intentionally restricts normal counts to six because the authoritative output has six rows. It does not generate missing-color or overflow cases: those are outside the reviewed training grammar, not hidden texture modes. Difficulty changes default weighting only; it is not an advertised exact axis.


### D8. Query-rotation closure

The first repair guaranteed one count-six example in each ordered three-demo window, but exhaustive schedule enumeration found four ambiguous held-out rotations: when that sole witness became the query, `cap_bars_at_five` fit all remaining demonstrations. A new regression reproduced the failure before the schedule changed.

Version 2.1.0 forces count six in both the `count_six` and `adjacent_pair` residues. Any four consecutive labelled pairs now contain at least two witnesses, so every three-demo holdout retains one while `border_scatter` still supplies a non-forced geometry branch. The focused suite is 50/50 green; the source-bound period receipt passes all bands and query positions; the independent probe checks 48/48 rotations; and 32/32 fresh generated inputs match the unchanged Racket authority.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-149abe63a1c3c16f:rejected`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `c814a464d558cc1d3df388a88a67850ab4adfd553eeb95c5af027d599e4b4f71`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted sourceeb3733d87d38d5f01950108e2eed143e6e2016fbc54cf99094fe82a6480ec6f9 removes inert aliases, honors five observable axes and preserves equal counts.50task tests and exact-axis/reference evidence are reviewer-reported. This adjudicates the retained standalone source-bound finding; it does not retroactively validate the rejected assignment identity.

### Assessment or prior finding

Main assignment identifier rejected; standalone source-bound report only.

## 64a8d13b4024

**Reproduced override-contract defect; source left unchanged.** The advertised
exact controls are not reliable:

- `grid_h=8`, `grid_h=14`, `grid_w=8`, and `grid_w=14` are declared valid but
  raise `ValueError` because generation internally requests only 9..12.
- `n1=n2=n3=2` silently returns counts `2,2,3` by rewriting `n3`.
- an unknown `typo=1` key is accepted;
- `palette_kind=default` and `palette_kind=warm` produce byte-identical grids;
- `texture=missing_color` bypasses requested 14x14 dimensions and 6/6/6 counts,
  returning a fixed 10x10 scene with counts 0/2/3.

The exact calls and deterministic output hashes are in
`checks/audit/64a8d13b4024/override-contract-evidence.json`. The isolated official
override stage failed after 83,160 draws with 4,586 findings: 3,240 override
mismatches, 1,320 generation errors, 22 axis-effect findings, 2 metadata findings,
1 provenance finding, and 1 accepted unknown key. Concise official evidence is
`checks/audit/64a8d13b4024-override/checks/64a8d13b4024_audit_battery_summary.json`
and its override log.

Audited generator SHA-256:
`c814a464d558cc1d3df388a88a67850ab4adfd553eeb95c5af027d599e4b4f71`.
No files under `generators/64a8d13b4024/` were edited.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-149abe63a1c3c16f-assignment-rejected/audit_assets.json), manifest SHA-256 `55a61686dace52a36ba8235a7b172f26c672a54bf2c48734aa0a7af0ce0d9955`.
<!-- arcpuzzles-current-audit-assessment:end -->

## 2026-10-25 native parametric family

### D10. Count-derived column ordering

The production generator and canonical ledger remain unchanged. The native
adapter in `workspace/parametric/` adds one episode-fixed parameter,
`column_order`:

- `color_order` is the byte-exact canonical program;
- `count_descending` counts colors 1, 2, and 3, ranks the complete
  `(color, count)` bars by descending count with low-color tie-breaking, then
  assigns those ranked bars to output columns.

This preserves the source puzzle's global-count/bar-chart reasoning while
adding a genuine sequential dependency: **A** counts the three colors; the
**intermediate** is the ranked `(color, count)` sequence; **B** uses that
sequence to choose each output column before rendering. The protected-Racket
witness at `checks/64a8d13b4024/causal/witness.json` replaces the ranked
intermediate with fixed color order on the same qualified input and changes the
second and third output columns.

### D11. Matched lessons and public boundary

Inputs are independent of the private setting. The first two demonstrations
separate both declared settings and teach the low-color tie break. The adapter
supports 2–6 demonstrations and 1–4 prefix-stable queries, with four distinct
query profiles ending in a substantive 30×30 case. Distractor colors 4–9 cover
all four boundaries but are ignored by both programs. `public_turn` writes one
masked query at a time and excludes settings, programs, seeds, answers, and
future queries.

The reusable `workspace/parametric/audit_lessons.py` checks the supported
count surface, matched inputs, prefix stability, nine executable shortcut
families, exact 30×30 coverage, and visible-byte public IDs.

### D12. Qualification and limits

- focused staged suite: 81 passed;
- finite audit: 64 seeds, 1,536 episodes, 768 matched-input checks, 384 exact
  30×30 pairs, 3,968 setting-dependent answer differences, zero declared
  shortcut survivors;
- public projection check: 8/8 passed;
- native qualification: both settings at seeds 0 and 17, 4 jobs, 28 retained
  labels, 40 protected-Racket evaluations, execution SHA-256
  `ee084813d80aa81c9d0fcb473c18efa15737bba585a47cdcdca591482ebfd45c`;
- causal witness SHA-256
  `f96849762fa0146e42ed1e8c9d029af8268ec2ce3e84dc49d6634358d067ef4a`.

The finite rival bank is not a universal uniqueness proof. The family is
reviewer-ready only: exact-source owner intake, native requalification,
acceptance replay, and explicit training admission remain required.
