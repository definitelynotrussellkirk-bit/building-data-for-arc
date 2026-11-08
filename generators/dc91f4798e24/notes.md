# Working notes: dc91f4798e24

## Current native parametric result — review-4cc2ac4c1214163e

Native-ready adapter in `workspace/parametric/`; owner exact-source acceptance
is pending. Canonical generator SHA-256 remains
`2dadb7679e19dc75fe6c86017bafc4502f292ddd2ae6931c50f0618346b4fbcd`, and the
`all` default returns the canonical Racket program byte-for-byte.

The alternative `blue_count_threshold` first counts blue four-connected bodies
(k), then counts target-color bodies with actual cell area at least k. Inputs
are matched across modes, with 2–6 demonstrations (default3) and1–4 independent
queries (default4). Query shapes are7×8,12×16,24×24,30×30; the large case has45
bodies,50 distractor cells, content in every quadrant and contact with all borders.

Two constructive lessons use k=2 and4. The k=4 L-triomino replaces an initially
considered k=3 lesson: k=2/3 cannot distinguish area from bounding-box area.
Blue areas[2,3] in the first lesson also distinguish k from largest-blue area.
Diagonal contacts and a foreign-color bridge expose wrong connectivity in either
stage. These repairs retain two demonstrations and meaningful rule branches.

Checks:113 task tests pass;8 boundary jobs/64 pair labels and4 native
qualification jobs/28 pair labels pass protected Racket. The bounded audit
covers16 canonical/23 alternative Racket rivals with no demo-fitting,
query-changing survivor. The k=2 versus forced-k=3 causal witness is freshly
replayed and bound to qualification. Public exports use visible-byte hashes and
first-turn projection contains exactly one query. Evidence lives in
`checks/dc91f4798e24/` in this return; the native source/evidence inventory is
`workspace/parametric/evidence/manifest.json`.

The inherited task-test helper imported two historical peers missing from rotating
packets. Its runtime staging now includes only locally available sources;
explicit absent-peer audits still fail visibly. A fresh code review also exposed
an overly permissive witness writer; it now rejects failed/foreign/stale
qualifications, verifies exact qualified program membership, and freshly replays
both causal labels. Earlier failing logs are retained as resolved iterations.

Limits: finite parameter/rival/seed checks, deterministic bounded placement rather
than a proof for every seed; no measured learning gain or training admission.
Only the owner can accept the exact integrated native source.

## Review 2026-10-02 — review-43bfa46e57f55f67

Imported version 2.1.1 produced isolated singletons and rejected all five canonical inputs. Canonical examples establish multi-cell bodies and distractor colors, but leave four- versus eight-neighbor connectivity ambiguous. Pixel counting solved the old sampler but did not fit canonical pairs; eight-neighbor counting fit both. No reference-rule edit was warranted.

Version 3.0.1 plants separately owned bodies and grows four-neighbor frontiers without merging same-color components. Areas vary independently of counts; at least one area exceeds one. Different colors may touch, diagonal same-color pairs can stay separate, borders are reachable, and irrelevant colors 4–9 are included. The positive/contrasted three-row curriculum is retained.

A failed intermediate profile gate showed medium/hard had lost canonical-scale support. The repaired 40% shape/palette mixture restores that support without copying grids. Another failed iteration correctly exposed negative fixtures being advertised as ordinary legal textures; metadata now distinguishes the domains. Ownership uses a plain integer matrix, not the ARC-color-constrained grid helper. Placement is bounded and fails explicitly instead of falling back to a simpler scene.

The exact reviewed generator hash is `2dadb7679e19dc75fe6c86017bafc4502f292ddd2ae6931c50f0618346b4fbcd`. Retained packet evidence: final 12/12 battery, standalone lint, 43 explicit task-local tests, and 1,000-draw independent Racket census (879 unique inputs; seeds 0–249 × four difficulty settings, index `seed % 16`). Pixel/eight-neighbor/binary rivals are refuted on 1,000/679/325 draw attempts respectively. Canonical acceptance is 5/5.

Known limitations: finite morphology/count range; not every assembled lesson is proven identifiable; repository-wide timeout test still fails in this environment; Landlock unavailable. A copied-runtime Python-audit proof passes but is not an OS sandbox. The fresh solve used only visible examples during its solve phase, with earlier rule exposure disclosed and masked-query correctness withheld.

The full return contains `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md`, `AUDIT.md`, `RESULTS.json`, failure logs and exact counterexamples. See workspace README for the next-agent handoff. Audit targets were not modified. Preserve review/admission separation.

Imported associated notes remain in `evidence/associated_notes.jsonl`; none were overwritten.
## Current reviewer considerations

Source SHA-256: `2dadb7679e19dc75fe6c86017bafc4502f292ddd2ae6931c50f0618346b4fbcd`.

# Decisions and retained reasoning — review-43bfa46e57f55f67

## G1: Preserve the rule; change the support of the input generator

The reference computes same-color four-connected components of colors 1, 2 and 3, and paints a three-row left-aligned histogram of width `max(1,n1,n2,n3)`. Canonical examples agree with the reference. The original singleton-only distribution and validator do not. The imported notes do not explain why singletons were required; that original rationale is **unknown**, rather than retroactively inferred to be deliberate curriculum design.

Rejected: changing Racket to count pixels, deleting canonical examples, weakening the reference checks, or hiding failing samples. Each would conceal the mismatch instead of repairing the generator. The rule and all authority files remain byte-identical.

## G1: Independent component counts and sizes

Counts are selected first, independently of component growth sizes. Each planted component owns its cells. A proposed growth cell is legal only if it cannot join a different planted component of the same color. Growth uses four-neighbor frontiers. At least one target body has more than one cell on every ordinary draw, so pixel counting cannot accidentally remain a universal solver for generated data.

Counts remain positive for all three rows and at least two differ, retaining the original didactic contrast. Easy uses up to 3 components per color, medium/default up to 5, and hard up to 7, with a capacity cap `h*w//12`. These bounds are a deliberate finite curriculum, not the full mathematical domain of the reference.

Areas vary by texture: sparse up to 2, default 3, dense 5, varied 6, diagonal 4, capped on small grids. Sparse is not synonymous with singleton-only. The generator never returns labels; Python histogram functions are diagnostic rivals/witnesses and all reference census labels execute Racket.

Rejected: one fixed area per component, a fixed lattice with several-cell stamps, or count-independent post-hoc painting that could merge components. These would respectively preserve area shortcuts, positional shortcuts, or incorrect planted counts.

## G2: Diagonal and different-color contacts

Eight-neighbor counting and binary foreground grouping both fit all five canonical pairs. The former is the strongest straightforward connectivity rival used in `QUESTION_ANSWER.md`. An explicit `diagonal` texture plants two diagonal cells of the same color into different four-connected bodies. Ownership prevents them from joining during growth. Some default/varied draws also force this feature, and random placement adds further witnesses.

Different target colors and distractors may touch orthogonally. Components remain monochromatic. This supplies cases against treating all nonzero cells as one foreground mask. Witness predicates are defined by actual rival output disagreement, not merely a suggestive geometric flag. The tests verify that fired witnesses refute their named rivals.

Rejected: requiring isolated objects separated from every color, or counting a diagonal-contact flag as proof without comparing actual outputs. The final census refutes the eight-neighbor rival on 679/1,000 draws and the binary rival on 325/1,000, on the exact final hash and seed cohort in `REVIEW.md`.

## G3: Distractors and canonical-scale support

Colors 4–9 are irrelevant to the three requested counts. They are placed only on empty cells, may touch target bodies, and never overwrite them. Noise is optional outside the canonical-scale branch. The branch uses one distractor, preserving the canonical five-color palette envelope (background, 1, 2, 3, one ignored color).

An initial repair used larger difficulty-scaled grids but lost exact canonical profile support in medium and hard. `checks/red-canonical-scale.log` demonstrates that failure. The fix uses a **40% mixture of canonical dimension profiles at every difficulty**: 7×8, 8×9, 8×11, 9×9, 9×10. These are only shape/palette summaries; no canonical grids or outputs are copied. The remaining 60% retains difficulty-scaled dimensions. Explicit height and width overrides always take precedence.

Rejected: opting out of the profile gate, widening the gate until it passed, or forcing every grid to the canonical dimensions. The final gate accepts all five canonical inputs and observes exact profile support in each band. All thresholds are unchanged.

## G3: Truthful overrides and negative fixtures

Only `grid_h`, `grid_w`, and `texture` are declared. Every supported dimension can be requested in every band. Unknown keys, nonintegral dimensions, bool dimensions, unknown difficulties and invalid texture values raise errors rather than being silently ignored or truncated. No incompatibility exclusions were introduced.

The old `equal_counts`, `missing_color`, and `no_components` negative fixtures remain available only when explicitly requested. They are intentionally invalid under the ordinary positive/contrasted curriculum and are **not advertised as ordinary legal AXES values**. The first repaired metadata mistakenly advertised them, causing defect/override failures in `checks/after/`; this was corrected in the declaration rather than disabling checks. Tests verify explicit negative behavior and honored dimensions.

`self_check` accepts all canonical inputs and arbitrary valid multi-cell/noise geometry within its semantic/count bounds. It is deliberately not an exact membership oracle for the sampler: a valid singleton-only input may be accepted even though ordinary generation always includes a multi-cell body. Requiring every arbitrary input to refute every rival would improperly reject lawful canonical cases.

## G1: Bounded placement, no silent simplification

There are at most 64 deterministic layout attempts with fixed requested counts and sizes. Exhaustion raises an error containing seed, sample index, shape and texture. There is no fallback to singleton-only bodies or easier counts. This makes rare failures detectable and reproducible. Zero such failures were observed in the retained default census and final battery; this is not a proof for all seeds.

A local profile identified repeated full-grid scans during seeding. Version 3.0.1 uses uniform rejection sampling for at most 32 tries per seed, then a uniform choice over all legal candidates if necessary. It preserves the placement constraints and avoids scanning every pixel for every new seed in the common case. The entire final battery was rerun after this change. `checks/placement-profile-before.log` and `checks/placement-profile-final.log` retain the diagnostic, but their version-changed realized grids are not an identical-input performance benchmark.

## Tests and evidence, including failed iterations

Write-first tests exposed the original behavior before the repair. `checks/red-tests.log` records 32 failed / 6 passed. The first implementation incorrectly used the ARC-colored `full_grid` helper with -1 for ownership; the helper correctly rejected the non-ARC color. `checks/green-tests-1.log` records 26 failed / 12 passed. A plain integer ownership matrix fixes the cause without changing the shared helper.

Subsequent runs reached 38 passes. Four canonical-scale tests then failed (39 passed) before the 40% profile mixture was implemented. The current suite has 43 passes. All intermediate generator sources and failure logs remain in `checks/iterations/` and `checks/`. The historical directory `after-final` contains the pre-optimization generator, not the final hash. Only `after-verified` is used for final battery claims.

The first standalone reference-probe attempts failed to import `scripts.comment_solutions` from the raw source layout. The reusable probe now calls the shipped `prepare_runtime` API to obtain the conventional import layout. It does not invent module aliases, import a sibling checkout, or replace Racket outputs with Python outputs. Failed initial logs are retained.

## T1: Diagnose shared-suite failure without editing shared scope

Both full repository runs report the same 169/1 outcome; an isolated rerun also fails. In 12 diagnostic trials, normal startup loses the initial line in all three 0.2-second cases and retains it in all three 1-second cases. Normal first-output latencies in the latter cases are 0.484–0.595 seconds. With `-S`, all six trials retain the line, including all three 0.2-second cases (first output 0.007–0.008 seconds).

This supports a startup-budget explanation in this execution environment. It does not establish that every possible streaming/timeout implementation is correct. The shared test and runtime are unchanged; no timeout was raised in the actual suite and no test was skipped. Feedback F3 proposes a narrowly scoped follow-up. The failure stays in `remaining_failures`.

## T2: Relocation versus OS sandboxing

The default portable harness calls the repository's Landlock read-denial tool. It fails here with `OSError: [Errno 38] Landlock unavailable`; the failed proof is retained. We did not silently skip it. A separate explicit `--isolation python-audit` mode prepares a copied runtime and copied Racket installation, strips source import paths, checks the original source path is unreadable through Python audit events, then runs tests and a Racket census.

That separate mode passes 43 tests and 100 draw/reference comparisons at the recorded runtime directory. Its report says `os_sandbox_verified: false`: a Python audit hook is not a hardened process-wide filesystem boundary and is not inherited by Racket as a security sandbox. No stronger isolation claim is made. The proof runtime is temporary and not shipped in the return.

## A1 / A2: Findings-only audits, not unauthorized patches

A1 is a concrete accepted-domain semantic coverage gap: bbox top-left order can differ from row-major first-cell order, but the sampled envelope placement does not distinguish them. Both validators accept the saved counterexample.

A2 is different: vertical same-color run deduplication is a wrong rule on a lawful per-cell input, but the target generator explicitly excludes that morphology/palette profile. The counterexample is validator-rejected. Whether to expand that curriculum is a domain decision, not proof of mislabeled emitted samples. Both target files retain their assigned hashes.

## Solve integrity and next decision boundary

The example-only solve started after the final generator freeze and used one genuine solution revision. Earlier exposure to the rule was disclosed; no blind-solve claim is made. Hidden query labels remained closed. The visible metamorphic checks and diagnostic rivals are tests of the author's hypothesis, not fabricated natural failures. The solve's `training_admitted` flag remains false.

A maintainer should inspect/apply this delta, independently rerun the task tests and final battery, review the shared timeout failure and isolation caveat, and score the masked queries through the normal intake process. More sample volume alone will not resolve the two audit rivals; targeted geometric counterexamples are the useful next work, in separate authorized assignments.
