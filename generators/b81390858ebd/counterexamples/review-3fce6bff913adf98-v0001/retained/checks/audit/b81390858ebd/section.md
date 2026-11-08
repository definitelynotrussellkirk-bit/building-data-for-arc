## b81390858ebd

**B813-A1 — Reproduced teaching shortcut; existing open finding reconfirmed.**
The intended rule selects the same-color 4-connected component with maximum
cardinal-contact degree, breaking ties by size and then top-left position, and
returns only that component, cropped tightly and recolored 8. The rival
**largest component, then top-left; crop and recolor 8** remains observationally
equivalent on the generator's accepted production domain.

The audited source is version `1.4.0`, SHA-256
`8ac5187e5abb962d5eb46dd402f5e4aae6a2348db7323eb30bcd4faea0708c6c`.
The selected Racket rule hash is `5fd0e8d9ff16`; raw canonical program SHA-256
is `5fd0e8d9ff1686adc1daa5048b26c11d727d1e6f88f8f5a624ee1792b37f82f3`.
The public apply receipt separately records executable callable SHA-256
`3b994a0665a790eb4f5eaf39e175bba75c2507bb5e6d6703c618cdcdcc349138`.
This is the exact source already associated with the unresolved
`review-aae0bbad2bb6c284:v0001` finding in
`repo/generators/b81390858ebd/evidence/review_index.json`; this audit supplies a
fresh bounded reproduction and does not claim a newly discovered defect.

### Evidence and scope

| Check | Result |
|---|---:|
| Generated draws: seed `20261023`, indices `0..14`, each of default/easy/medium/hard, no overrides | 60/60 generated and accepted by their difficulty-specific `self_check` |
| Distinct generated inputs | 45; default and medium overlap |
| Unique largest target, and largest-component rival equal to actual Racket output | 60/60 draws |
| All usable canonical labeled pairs, read through `canonical_pairs` | 3/3 rival matches; 3/3 canonical labels agree with Racket |
| Handmade degree-versus-size witness | 1/1 rival disagreement with actual Racket |
| Independent degree-rule mirror equal to actual Racket | 64/64 applied inputs |

The source constructs a multi-cell hub, singleton leaves, and isolated singleton
distractors. `self_check` explicitly requires the hub to have at least three
cells and every other component to be a singleton. Thus every accepted draw has
the degree target as its unique largest component. This structural restriction
explains the measured result; it contradicts the source comment claiming that
at least two demonstrations refute “pick the largest.” Neither
`CANONICAL_SHORTCUTS` nor `LESSON_COMPETITORS` is declared, so there is no executable
rival list to iterate. No task-local test files were present.

`EXAMPLES_NEEDED` is 3. Ordered production lesson execution: **unknown, 0 lessons
run**. Query-rotation execution: **unknown, 0 lessons run**. No lesson assembly,
ordering policy, or query-position policy was exercised. The separate structural
inference is that any lesson containing only accepted draws cannot refute this
rival, regardless of demonstration ordering or query position. No full battery,
selected check stage, or lesson census was run for this audit.

### Exact separating input

Input: 9 rows × 11 columns. Actual Racket output: 1 row × 3 columns.

```text
00000000000
00000007700
00000007700
00000000000
00003040000
00002220000
00000600000
09000000000
00000000000
```

The color-2 component has size 3 and degree 3. The isolated color-7 square has
size 4 and degree 0; the color-9 singleton supplies the second distractor required
by the default count range. Racket returns `[[8, 8, 8]]`. The rival returns
`[[8, 8], [8, 8]]` (2 rows × 2 columns).

This input satisfies the written/Racket contact-degree rule, but it is **outside
the documented generator domain**. Default `self_check` rejects it with exactly
`["distractor is not an isolated singleton"]`. Therefore this is evidence of an
unrefuted training shortcut and an over-restrictive teaching distribution, not
a mislabeled accepted production draw.

### Retained reproducer and suggested disposition

- `checks/audit/b81390858ebd/probe.py`: public loader/Catalog authoring probe and independent rival.
- `checks/audit/b81390858ebd/inputs.json`: exact ordered 64-input batch; witness at index 63.
- `checks/audit/b81390858ebd/racket.json`: actual public apply receipt, all inputs/outputs, hashes and execution directory.
- `checks/audit/b81390858ebd/prepared.json` and `checks/audit/b81390858ebd/report.json`: source-bound seeds, indices, overrides, validator results, rival outputs, full rule text and comparisons.
- `checks/audit/b81390858ebd/commands.json`: exact command arrays, working directories and exit codes.
- `checks/audit/b81390858ebd/probe_v1.py` and `checks/audit/b81390858ebd/probe_failure.json`: retained initial bookkeeping assertion failure. The probe initially equated raw program and callable-wrapper hashes; the final probe records them separately. This failure did not affect the Racket outputs.

Keep the existing finding open. A task-local repair should allow larger low-degree
components and include a size-versus-degree separating example in every intended
lesson, then declare the largest-component rival as an executable competitor.
The audit made no generator, notes, test, catalog, shared-code, or rule changes.
