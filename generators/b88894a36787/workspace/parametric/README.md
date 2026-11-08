# Native missing-extension prototype

`adapter.py` reuses the inherited `missing_extension.py` programs for `bottom`
and `penultimate`, and adds `first_hit`. The canonical default is preserved
byte-for-byte. Production v3.1.0 and its approval state are unchanged.

| Setting | Unmatched header behavior |
| --- | --- |
| `bottom` | Canonical vertical extension through the bottom row. |
| `penultimate` | The inherited alternate extension stops one row earlier. |
| `first_hit` | Render matched L-routes first, then extend each unmatched column only through empty cells before its first rendered obstacle; extend to the bottom when no obstacle exists. |

Matched routes use leftmost-header overlap priority. `first_hit` examines an
immutable matched-route stage, preserving blockers and treating multiple
unmatched columns independently. An original input edge dot cannot substitute
for that stage: the crossing that determines the stop is created by routing.

## Native API and grammar

`generate(seed, settings=None, demos=3, queries=4)` returns private `train`,
`test` and `program_solution`. `program(settings)` returns a standalone Racket
rule. Seeds are exact integers in `0..2**63-1`; settings contain exactly
`missing_extension`. An omitted setting uses the declared mode at `seed % 3`.
Requests support 3–6 demonstrations and 1–4 queries, independently. Separate
local random streams construct the complete six-demo/four-query banks before
slicing; changing counts or settings preserves shared input prefixes. No
module-global random state is changed, and requests return fresh lists.

The separate native grammar supports rectangular 8–30 grids, 2–8 distinct
contiguous interior headers (also bounded by width minus two), zero to two
missing matches with at least one matched header, and at most two ignored
nonheader-color edge dots. Each header has at most one matching edge dot.
Ignored dots may share a color. Colors are exact integers 0–9. Crossing routes
are lawful in this prototype; production's smaller noncrossing domain is not
expanded by this work.

The minimum lesson has missing counts 2, 1 and 0. It shows a deep first hit,
a later hit, no-hit fallback, a row-1 hit, opposite strict canvas halves,
interior and boundary omissions, priority intersections and ignored colors.
The four independently ordered queries include an 8×8 case, a complete case,
larger interacting routes, and a 30×30 case with deep routes reaching both
side edges and the bottom. Geometry, colors, offsets and lawful reflections
vary by seed; horizontal reflection is an input variation, not a claim that
left-priority labels commute with reflection.

## Evidence and reuse

`audit.py` is a reusable task-local finite protected-Racket auditor. It loads
only adjacent adapter/family/contract files, fits declared settings and authored
shortcuts to demonstrations, checks survivors against private queries, caches
exact program/input executions, and rejects runtime errors or source drift.
It never treats an execution error as a teaching success. The retained audit
checks all three settings at seeds 0 and 17: 82 comparisons, all demo-refuted.
The focused final suite passes 82 tests, including the inherited five tests.
A maximum-seed request checks all ten pairs per setting with protected Racket.

Independent self-review found right-half and lower-half stop shortcuts in the
initial lesson. The existing three demonstrations were repaired; query banks
were preserved. Original findings and source snapshots remain in
`checks/b88894a36787/`; a 56-execution protected replay refutes all four retained
finding rows after repair. These are bounded checks, not universal uniqueness
or measured learning-benefit claims.

From the outer packet directory, the current native workflow is:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify b88894a36787 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/b88894a36787/qualification --summary
python3 review.py preview-public export --qualification ../checks/b88894a36787/qualification/qualification.json --out ../checks/b88894a36787/public-preview
python3 review.py preview-public verify --bundle ../checks/b88894a36787/public-preview
```

Use a new output directory for a new run. The native manifest binds current
sources and declared evidence; qualification and causal replay are retained
separately. Reviewer readiness requires the resulting receipts. Owner
qualification and fresh acceptance of the integrated bytes remain separate;
training admission is false.

Only one selected `public/<sha256>.json` is a model prompt. Each file has the
same demonstrations and one unanswered query, with IDs derived from exact
visible bytes. The controller retains the bundle, directory listing, future
queries, ordering, settings, programs and answers. Export verification checks
source bindings and bytes; it neither replays Racket nor authenticates an
adversarially rewritten private receipt.

The inherited `evidence/retained` files and legacy CLI are historical
provenance. Its setting-named filenames are not the current public interface;
use native opaque one-query export for new model-facing challenges.
