## 0d5077971eea

**Disposition: two findings; target sources unchanged.** The checked generator is
SHA-256 `a338b592c839a0ef4bec46d972da6ca06e45f2caf0353869343902badc5b3f61`,
VERSION `2.0.0`. The selected canonical Racket text is SHA-256
`071b2a298d5c565c469357c6b6662d4fe94ec5e123bbe48fa36861d8e40691df`,
with declared normalized rule hash `1130750019d1`. These match the current
review index. No prior audit is recorded there.

### A1 — A lawful zero-header row form is absent from the sampler

Every generated row whose header is zero and which contains an interior marker
also contains a nonzero, non-8 spectator. The sampler constructs its sole such
marker row with `_put_markers(..., spectator=...)`; other zero-header rows never
receive markers. Palette completion only fills zero cells with non-marker
colors, so it cannot create the missing form.

The independent counterfactual `nearest_key_for_marker_only_rows` in
`checks/audit/0d5077971eea/probe.py` applies the normal rule except that a
zero-header row containing only zeros and 8s borrows the nearest colored header.
This is a conditional variant of the declared nearest-header rival. It matched
all three canonical pairs and all 264 checked generated inputs, yet disagreed
with actual Racket on the literal `bare_zero_header_marker` witness in
`evidence.json`. That 5×7 input has four colors, medium marker density, and two
differently keyed transforming rows on opposite parities. Both `self_check`
and `strict_canonical_like` accept it. At zero-based cell `(2, 2)`, canonical
Racket preserves 8 while the rival writes 3. Adding one non-marker spectator
at `(2, 1)` makes the rival agree again; the paired control is retained.

This is a **distribution coverage finding, not an incorrect generated label**.
The existing notes already acknowledge mandatory witness rows as a distribution
limit; this audit supplies a concrete surviving conditional rival and accepted
counterexample within that limit. Consider teaching both bare and spectator
zero-header rows across the existing episode schedule, then recheck the eight
declared rivals, actual lesson assembly and minimum-canvas palette capacity.
Changing the Racket rule is unnecessary.

### A2 — Public call arguments bypass strict scalar validation

The sampler validates override types but does not validate `seed`,
`sample_index`, or `difficulty` before constructing the context. The focused
probe accepted 15 of 19 deliberately invalid argument values, including boolean,
string and floating seeds, negative/boolean sample indices, and unknown or
non-string difficulty values. Exact calls and outcomes are retained in
`evidence.json` under `scalar_argument_checks`. This is an API robustness
finding outside the valid grid-label domain. Validate an integer seed,
nonnegative integer sample index, and `None` or a known difficulty explicitly.

The public audit-phase `defect_lint` check exited **1**, reporting 39
`strict-scalar` warnings plus one coarse structural-distribution advisory
(`object_count`, `palette_roles`, `persistent_markers`). It reported zero
error-class issues. The structural advisory is a separate review lead; it does
not establish incorrect labels.

### Executed scope and limits

The source-bound probe exited **0** with status `FINDINGS`: 269 actual Racket
evaluations covered all three labeled canonical pairs, 240 default draws
(40 seeds × two schedule parities × three difficulties), 24 boundary draws,
and the two literal witnesses. The boundary calls include the previously
problematic 5×7, ten-color, high-density case at seed 6127, alongside low/medium
density and 12×16 limits. All checked generated inputs passed `self_check`;
all exact controls were realized; an independent row oracle agreed with Racket
throughout. No generated-label disagreement was found in this checked scope.

Retained reproduction and evidence: `checks/audit/0d5077971eea/probe.py`,
`evidence.json`, `probe.log`, `defect-lint/result.json`, and the stage log beneath
`defect-lint/checks/`. `command-rows.json` contains the two exact commands and
exit statuses. No full battery, model training, or universal identifiability
claim was made. The target's generator, notes, rules and tests were not edited.
