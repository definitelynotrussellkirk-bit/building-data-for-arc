# Working notes: d70726fd510f


## Current account — review-b234206ce6588830

The selected rule remains occupancy XOR across two aligned panels separated by a
full color-4 column. The canonical Racket authority and normalized rule hash
`11243a80c7ea` are unchanged. This review found one concrete API defect in the
otherwise approved selected source: `generate()` accepted boolean, floating,
and string seeds plus boolean or negative sample indices. It now requires an
exact integer seed and an exact nonnegative integer sample index before any draw.
No valid integer replay or input-distribution behavior was intentionally changed.

Final generator SHA-256 is
`5ce2c812c3ded72b7d3401a4a175a106f7f08580076d4d1184e00c5c70b17b49`.
The full after battery is 12/12 green and the portable task stage is 272/272.
The ordinary three-demonstration/one-query semantic smoke is 12/12 identifiable
in production order. Its optional rotation diagnostic is 43/48 unambiguous and
5/48 ambiguous against fixed-shape/fixed-separator rivals, so arbitrary query
rotation is not claimed. The selected ordered curriculum and existing sampler
remain unchanged by the scalar repair.

A separate proposal lives in `workspace/parametric/`. It selects one episode-level
Boolean operation (`xor`, `and`, or `or`) and one output color (1..9), then uses
that same exact Racket program for three demonstrations and one query. The
source-bound finite audit in `checks/parametric/run-02/` completed all 27 settings,
matched the canonical default on all five labeled canonical pairs, produced 27
distinct witness outputs, and retained one deliberately ambiguous diagnostic.
This is a prototype only; it does not alter or approve the canonical execution
path.

The strongest canonical-fitting shortcut remains fixed-palette XOR: treating
only left color 8 and right color 5 as occupied. The lawful one-row witness
`[0,0,9,9,4,0,7,0,7]` gives canonical output `[0,2,2,0]` but shortcut output
`[0,0,0,0]`. The current sampler emits a refuting transfer case at seed 0,
sample index 1, default difficulty. Evidence is retained under
`checks/question-shortcut/`.

No current selected-source audit finding remains unresolved in this return. The
two separately drawn audit targets were findings-only and were not edited.

---

## Current repair

Assignment `review-6c4f2053a7aa3c1b` repaired the selected baseline and retained failed iterations. Original associated notes were empty; original rationale beyond source comments is unknown. Historical unreviewed `review-7db198064734f44c:v0001` supplied leads, not current-source evidence.

Baseline could produce 19 differing cells when asked for 1, rejected lawful values through default draw domains, and ignored or distorted other controls. Correlated masks and left-biased repair also left complete lessons ambiguous between XOR and one-sided subtraction. The comparable census found 17 genuine query ambiguities in 300 independent baseline lessons.

## Choices and tradeoffs

Independent RNG streams propose panel masks. Symmetric projection realizes the final XOR count and covers both equal and both differing states whenever each class has at least two positions. Ordinary counts 2..area-2 teach all four states. Explicit tiny/zero/full-output controls remain lawful; validity does not imply teaching completeness.

Defaults cycle `sample_index % 3`: core uses canonical geometry/palette, transfer changes height, width and foreground palette, and broad mixes canonical-shaped/free geometry with full foreground choices. Broad's geometry mix was added after the first repair measured 13/60 coarse profile hits. Final support is 23/60 with every band represented. This guard is measured, not claimed to optimize model learning.

Exact controls are observable in returned grids. Foregrounds may coincide and may equal output color 2; 4 remains the divider. Invisible requested foregrounds or contradictory edges raise structured `ValueError.incompatible_axes`. Density and spatial pattern are proposal controls; projection may change final density or shape. `same_panels` means equal occupancy, while `disjoint_panels` means complementary occupancy covering the panel.

The final difficulty guard accepts `None` as medium and rejects invalid falsey objects. Validation rejects malformed grids, booleans/invalid colors, broken dividers and multiple foreground identities within a panel, while accepting lawful tiny and constant-output grids.

## Teaching contract and tools

Three `CANONICAL_SHORTCUTS` fit all canonical pairs. `LESSON_COMPETITORS` includes them and all 15 non-XOR aligned Boolean tables. `lesson_identifiable` uses visible demo labels and query input, ignores query output and rejects inconsistent demo labels. The claim is bounded to this finite class.

`workspace/lesson_probe.py` evaluates actual declarations, distinguishes independent/overlapping samples and global uniqueness, records source/tool/rule hashes, and optionally checks public Racket outputs in batches of at most 64. `--require-pass` enables failure exits; `--require-rival-refutation` additionally rejects mere rival survival.

Final generator SHA256: `83d38a64916999f05b2dfcffd7f75fc9c261df02491582b61173a01aab46b0c7`. Probe SHA256: `152e7b7eb98f0a919c303b251ef0c6628aad035ef4b2b09f126814b679413baf`. Only selected Racket target formatting was synchronized; canonical semantics/ledger remain unchanged.

The return contains 215 passing task tests in source/portable layouts, 12 green battery stages, 300 independent and 300 overlapping lessons without surviving declared rivals, 99-case Racket parity, two findings-only audits, and honest blind/exposed solve records. Hidden solve verdicts and Qwen improvement remain unmeasured. Use this return's `RESULTS.json`, not inherited historical counts.
## Current reviewer considerations

Source SHA-256: `5ce2c812c3ded72b7d3401a4a175a106f7f08580076d4d1184e00c5c70b17b49`.

# Decisions for `d70726fd510f` — `review-b234206ce6588830`

## D1 — reject invalid call scalars at the public entry point

**Choice.** `seed` must have exact type `int`; `sample_index` must have exact
type `int` and be nonnegative. Rejection occurs before override validation or
random draws.

**Rationale.** The before-phase defect lint showed 24 accepted invalid calls
across easy/default/hard probes. Boolean values are integers in Python's type
hierarchy, floats such as `1.0` can silently resemble integers, strings are
accepted by some random seed APIs, and negative indices silently select a
schedule residue through modulo arithmetic. These are call-contract defects,
not useful generator diversity.

**Alternatives rejected.** Coercing values with `int()` would merge distinct
inputs, hide caller bugs, and accept lossy values. Leaving the behavior to
`gen_ctx` would preserve inconsistent contracts across generators. Adding a
shared-framework patch is outside this selected task's allowed delta. Two local
guards are the smallest source-bound repair.

**Evidence.** `checks/strict-scalar-red.log`,
`checks/strict-scalar-green.log`, and final battery defect lint under
`checks/after/`. The final generator hash is
`5ce2c812c3ded72b7d3401a4a175a106f7f08580076d4d1184e00c5c70b17b49`.

## D2 — keep rule parameters small and episode-level

**Choice.** The proposal varies only the Boolean occupancy operation
(`xor|and|or`) and output color (`1..9`). One pair is selected once and used by
all three demonstrations and the query.

**Rationale.** These parameters preserve the original object roles, panel
alignment, separator, occupancy abstraction, and cellwise reasoning. The four
occupancy states `00,01,10,11` distinguish XOR, AND, and OR, while any selected
cell identifies the output color. The canonical default remains XOR/color 2.

**Alternatives rejected.** Varying panel alignment, separator color, geometry,
or palette semantics would mix input-distribution changes with rule changes and
would no longer be a small rule-family extension. Adding more Boolean functions
would increase declared ambiguity without a clear curricular need. Selecting a
new rule per pair would make a lesson incoherent.

## D3 — keep the extension separate from canonical production

**Choice.** The runnable prototype and tests live under
`workspace/parametric/` and `tests/`; the selected generator and canonical
Racket ledger do not call it.

**Rationale.** The assignment asks for a proposal and evidence, not authority or
training approval. The extension emits exact Racket programs and public/private
records, refuses output-directory overwrite, and records source/program hashes.
The finite audit proves only the declared 27-setting contract on retained cases.

**Limits.** One episode per setting, sample indices `0..3`, and five canonical
pairs do not cover every seed, grid, difficulty, or undeclared rival. The
intentionally ambiguous diagnostic is retained. Production integration remains
a maintainer decision.

## D4 — make direct tests portable without weakening the CLI boundary

**Choice.** Direct unit tests provide a hash-verified selected generator bundle
to the prototype. Normal CLI execution still calls
`reviewer_support.load_selected_generator()` in its own process.

**Rationale.** The first portable task run loaded the frozen fixture's
`puzzle_generators` package before the new tests asked the source-bound loader to
load the repository mirror. The loader correctly rejected that second tree.
Explicit injection avoids importing two equivalent mirrors in one interpreter,
while the test verifies the provided source hash and the actual CLI continues to
exercise the official loader.

**Alternatives rejected.** Clearing `sys.modules` would weaken isolation and can
corrupt other tests. Disabling the loader's cached-dependency check would remove
an important source-integrity guarantee. Skipping portable CLI tests would hide
the deployment boundary.

## D5 — preserve the ordered lesson contract and report rotation limits

The existing selected generator uses three demonstrations and one query. Final
production smoke is 12/12 identifiable. Diagnostic query rotations are 43/48
unambiguous and 5/48 ambiguous against fixed-shape/fixed-separator rivals. This
review changes only scalar validation, so it does not redesign the existing
schedule merely to satisfy an optional rotation diagnostic. Arbitrary rotation
support is explicitly unclaimed.

## D6 — retain rather than patch drawn audit targets

`4650a2421296` and `17f92e205b34` are findings-only audit targets. Their exact
source hashes match `AUDIT_ASSIGNMENT.json`; neither source was edited. Reproducers,
validator results, defect-lint/override receipts, and canonical Racket outputs
are retained under `checks/audit/` for maintainer triage.
