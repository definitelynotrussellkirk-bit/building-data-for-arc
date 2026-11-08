# Working notes: 5f9a2df57599

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/5f9a2df57599/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current native proposal

The retained `side_boundary_policy=canvas_edges|gray_walls` programs now have a
thin native adapter, promotion contract and separate constructive sampler.
`prototype.py` is unchanged. Production version 2.0.0 remains at SHA-256
`f641de5c1ef15a254272dce952d0951d29a2be87c6d88873638543dcac41a51e`,
with canonical rule hash `5b73d3931a5c` and exact program SHA-256
`e8cf01347e8f1013e5af75c1170767e3bac1afd1974dca142f8ff406e41672bd`.
The canonical side-edge allowances, full top/bottom wall tests and multi-row
column-zero exception remain intact; the alternative requires literal gray sides.

Prior choice → current choice: the old builder selected only inherited production
profiles; native generation constructs teaching contrasts. Its first two demos
jointly expose all four complete-side tests, small rejected L components, large
eligible regions, nonrectangular cell masks, multiple selections and asymmetric
boundary behavior. Both policies use identical inputs. Independent counts are
2–6 demos and 1–4 queries, default 3/4, sliced from a fixed 6/4 bank. Queries cover
8×8, medium, tall/wide with a side of 30, and substantive 30×30 scenes.

The first compact implementation had only four possible 8×8 inputs because its
gray background erased the intended variation. A failing diversity regression
exposed this; the current construction varies 2–6 extra black cells while
preserving an interior positive and the core teaching scenes. The final bounded
probe produced 240 distinct inputs and 96 distinct queries over 24 seeds, with
144/144 successful requests and one construction attempt per scene. These are
Python claim-label observations, not 144 independently qualified episodes.

A further source-derived check found a shape-only shortcut: reject every
nonrectangular three-cell component and otherwise use boundary eligibility. It
matched twelve retained seed-zero labels without reading gray walls. The final
core scenes add eligible three-cell L shapes with intact walls, so identical
normalized shapes receive opposite labels when wall context changes. Protected
before/after evidence is retained in `checks/5f9a2df57599/shape-shortcut-before/`
and the release audit. No incorrect old intended label is claimed.

The dependency is input-derived: four-neighbor component membership determines
bounding boxes, complete side facts and the actual cells selected for painting.
Two qualified wrong-intermediate witnesses replace four-neighbor grouping with
eight-neighbor grouping. Protected construction and independent replay change
six cells in a 22×27 strict-policy demo and three cells in a canonical 30×30 query.
This is a geometric dependency, not an iterative-state claim.

Current verification: 63 focused tests; an independent audit with 594 protected
Racket evaluations across six jobs; 60 native qualification evaluations on seeds
0/17/101 with three demos/four queries; 20 protected example-export evaluations;
and two causal cases with four construction plus four replay evaluations.
The first two demos reject all fourteen non-equivalent tested rivals. Under the
strict policy the column-zero exception is redundant; it is recorded as such.
Native query files expose one current input only; all-query containers, answers,
settings, full metadata and native execution remain private.

Evidence: `checks/5f9a2df57599/native-wall-teaching-audit-release/report.json`,
`checks/5f9a2df57599/sampler-release.json`,
`checks/5f9a2df57599/native-export-release-report.json`,
`checks/5f9a2df57599/qualification-release/qualification.json`, and
`checks/5f9a2df57599/causal-release/witness.json` with its sibling replay receipt.
Earlier native audit/export/sampler files, including the intermediate `-final`
files, bind pre-refinement sources and are provisional history. Only the release
files and current inventory support the returned source. The unchanged production battery
and old prototype's broad tests were not rerun.

### Additional training-data gate

`workspace/parametric/check_wall_teaching.py` implements a cheap opt-in
counterbalance: demonstrations must include a painted region with a bbox side
longer than four, plus the same compact interior shape both painted behind
complete walls and rejected with a failed bbox side. It reads demonstrations only and performs no reference
execution. Apply it to already verified labels.

Fresh replay of the unchanged prototype's seed-zero three-demo/four-query lesson
under both policies shows a policy-aware size-only rule matching all fourteen
labels while inspecting no gray walls (28 protected calls, intended plus rival).
Both original lessons and both pre-refinement native lessons fail the strengthened
gate; both release exports pass, each with two matched-shape contrasts. This is a
reproduced distribution shortcut, not an incorrect intended label. Evidence:
`checks/5f9a2df57599/legacy-shortcut.json`,
`checks/5f9a2df57599/wall-gate-legacy-release.json`,
`checks/5f9a2df57599/wall-gate-prior-native-release.json` and
`checks/5f9a2df57599/wall-gate-native-release.json`.

A task intentionally restricted to small rooms, or a useful lesson without this
exact repeated-shape contrast, can be rejected falsely. Restrict the gate to families intended
to teach arbitrary-size wall selection. The cheapest test is a Python pass over
already reference-verified demos; no further Racket or Qwen run is needed. No
training benefit or mixture change is claimed.

### Open boundaries and next action

The existing production size-limited shortcut and top-row distribution findings
remain unresolved at their original production hash. This native sampler
addresses their relevant geometry/teaching limitations in a separate proposal;
it does not resolve the production audit index. Finite seeds and named rivals do
not prove all-seed success or unrestricted uniqueness. Reviewer status is ready;
after integration the owner must qualify and freshly accept the exact integrated
source. No owner acceptance, approval mutation or training admission was performed.
