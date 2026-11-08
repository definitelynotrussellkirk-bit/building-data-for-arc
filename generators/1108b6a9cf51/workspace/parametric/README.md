# Native transform-transfer prototype

Infer the unique D4 operation taking the first panel A to the second panel B,
then use that input-dependent operation on panel C. This preserves the original
two-step reasoning. Production v3.0.0 and selected canonical authority remain
unchanged; the `forward` program is the exact selected canonical text.

| `transfer` setting | Operation on C |
| --- | --- |
| `forward` | Apply the inferred A→B operation once. |
| `inverse` | Apply its inverse; CW and CCW exchange, while other D4 operations are self-inverse. |
| `twice` | Apply the inferred operation twice. |

The parameter is fixed for an episode; the inferred operation varies between
examples. All settings share the same inputs. Reviewed selected-generator
transform, orbit and connected-panel helpers are loaded through the
same-checkout loader. Alternate Racket rules use guarded substitution of the
canonical final application, retaining the same inference mechanism.

## Native API and grammar

`generate(seed, settings=None, demos=3, queries=4)` returns private `train`,
`test` and `program_solution`; `program(settings)` returns a complete Racket
rule. Seeds are exact integers in `0..2**63-1`. An explicit setting contains
exactly `transfer`; omission selects the declared mode at `seed % 3`. Supported
counts are independently 3–6 demonstrations and 1–4 queries. Full six/four
banks are built before slicing, using distinct local streams for demo content,
query content, query ordering and the shared relation coin. Requests are fresh
and do not alter process-global random state.

Inputs contain three equal n×n panels, separated by two complete color-9
columns, with n in 3–9. Panels use exact integer colors 0–8 and jointly 2–8
nonzero colors across A/C. A and C must contain both background and content and
have full eight-element D4 orbits. A→B must identify exactly one operation.
The sampler additionally keeps each color connected; connectivity is a
sampler guarantee, not a requirement imposed by the native parser. After at
most 32 unsuccessful symmetry checks, its constructive connected fallback
guarantees an asymmetric panel. The production grammar remains n=3–6.

The three mandatory demonstrations show a quarter-turn, an axis reflection
and a diagonal reflection. The repaired quarter-turn example has a 5×5 cross:
four distinct two-cell arms surround a uniquely rare, lowest-color center.
The center and occupancy remain fixed under rotation, while the full colored
pattern identifies the operation. The axis-reflection example requires
minority colors despite a symmetric dominant-color mask. An off-center C with
zero margins distinguishes transforming the whole panel from cropping first.

Four independently ordered queries use panel sizes 3, 7, 8 and 9, with an
opposite quarter-turn, identity, 180° rotation and a reflection. Their palettes,
density and clustered shapes vary by seed. The 9×29 maximum input has 237
occupied cells; each panel has 73 occupied cells spanning all four boundaries.
Its output is 9×9. A 30×30 input cannot fit the unchanged horizontal layout:
3n+2≤30 forces n≤9. No padding or alternative panel layout is claimed.

## Verification and tools

The focused repaired suite passes 112 tests, including independent coordinate
oracles for every operation/setting, protected Racket execution, all five
canonical pairs, strict domains, request isolation and forced fallback.
The maximum-seed six-demo/four-query request has 30 protected label checks.

`audit.py` is a task-local reusable protected-Racket auditor. It loads only
adjacent sources, compares declared settings and authored shortcuts using
demonstrations, checks survivors against private queries, and rejects execution
errors or source drift. It also handles canonical dictionary-form tests and
string-row grids. The final seeds 0/17 audit has 144 comparisons: 136
demo-refuted and eight finite-consistent, with no query conflict or error.
Six consistent rows are algebraically equivalent reflection omissions under
`twice`; two dominant-color rows only agree on the finite checked queries.
They are not claimed to prove general equivalence.

Independent review confirmed two initial lesson gaps: rarest-color-only
inference at seed 17 and lowest-color-only inference at the maximum seed.
The existing D1 was strengthened to the cross without adding demonstrations.
All four query banks at seeds 0, 17, 19 and the maximum seed remain unchanged.
Original findings and source snapshots are preserved in
`checks/1108b6a9cf51/`. A 28-execution protected replay refutes both saved cases
by the repaired first demonstration. The two exact rival programs are retained
in `native_family.py` for future auditing. All evidence is bounded.

From the outer packet directory, use the native workflow with new output paths:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify 1108b6a9cf51 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/1108b6a9cf51/qualification --summary
python3 review.py preview-public export --qualification ../checks/1108b6a9cf51/qualification/qualification.json --out ../checks/1108b6a9cf51/public-preview
python3 review.py preview-public verify --bundle ../checks/1108b6a9cf51/public-preview
```

The current manifest binds the adapter, resources, test sources and scoped
evidence. Native qualification and causal replay are separate receipts.
Reviewer readiness is followed by owner qualification and fresh acceptance of
the integrated bytes; training admission remains false.

Give a model only one selected `public/<sha256>.json` at a time. Its identifier
depends on exact visible bytes, and it contains the demonstrations plus one
unanswered query. The controller retains private settings, programs, answers,
ordering, other files and future queries. Native export verification checks
bytes and current source binding; it does not replay Racket or authenticate
adversarially rewritten private receipts.
