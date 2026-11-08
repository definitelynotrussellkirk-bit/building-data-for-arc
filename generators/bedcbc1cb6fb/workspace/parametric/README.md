# Nested rings and an area key

This task-local candidate preserves the exact canonical `rings` program. The alternative `ring_area_fill` first completes those rings, measures the occupied area of the innermost marker color **inside the blue frame**, selects the unique outside shape with that occupied-cell count, and fills the selected shape's bounding box in that marker color. The completed rings and all other shapes remain visible.

The rule parameter is fixed for an entire episode. Both settings use the same input draws. The ordinary interface has three demonstrations and four private queries; it independently supports 2–6 demonstrations and 1–4 queries. Queries are distinct from the demonstrations and each other. Every delivered label is executed by the included protected Racket runtime.

## Domain and intended reasoning

Inputs have one blue frame, 2–5 distinct nonzero/nonblue diagonal marker colors, and three connected nonrectangular outside shapes. Outside colors are distinct and disjoint from marker colors; their cells are off the main diagonal and outside the frame. The markers can have gaps. The last visible marker color's completed center occupies a positive number of cells. Exactly one outside shape has that occupied area. Shape geometry, color, position, and area rank vary.

This is a separate extension of the calibrated production grammar. Production version 3.0.0 and its existing approval are unchanged. Its retained diagonal-versus-row-major audit remains open. The extension's outside shapes make that distinction observable; a finite teaching audit measures only its declared competitors.

The sampler varies frame dimensions independently of marker count. The first two examples have three and five markers, and the first palette is deliberately nonnumeric. A bounded guard chooses their layouts by requiring demo-only refutation of the declared finite rivals under both settings. It considers at most 64 candidates per demonstration (128 total), never accesses a query, and fails explicitly if it cannot construct a teaching pair. `teaching_metadata(seed)` reports the actual selection work. The diagnostics used by this guard are reused by the finite audit; that audit is therefore not an independent search over teaching hypotheses. Its intended predictions are separately checked against actual protected Racket labels. The default first three demonstrations include the same frame size with different marker counts and the same marker count with different frame sizes. The smallest query is 14×16; the largest is 30×30 with three substantial shapes, a large frame, and boundary contacts. Transposition preserves the diagonal/frame semantics; arbitrary rotation is not an advertised augmentation.

A: fill the nested rectangles using diagonal order. Intermediate: the count of the last marker color within the completed frame. B: use that count to select an outside component and complete its bounding box. The retained wrong-intermediate witness keeps A identical and changes only the numeric lookup, so it changes which outside object is completed. This proves the bounded causal contrast, not universal algorithmic depth. In this grammar the same center area can be calculated directly as `(frame_height - 2*k) * (frame_width - 2*k)`, where `k` is marker count. The independent review executed that equivalent formula and obtained identical outputs. The dependency is on computed center geometry and an external shape lookup; this is not a claim that literal painting is computationally indispensable or that the task performs irreducible iterative simulation.

## Public-evaluation inspiration

Assignment `review-9544fb4fd1048d92` pins public-evaluation task `f560132c`, challenge SHA-256 `b141518eed470efcd0dba940f1cbf7e722b9f3c48eba852dc6432bb66df9cea6`, from `shared/data/raw/arc-agi_evaluation_challenges.json`. Its supplied training pairs show a compact multicolor cue and reconstruction from separated monochrome shapes. The transferred idea is key-guided geometric reconstruction. The ring-derived numeric area lookup is newly authored here, not an asserted mechanism of that source task. `relationship_verified` remains false; no held-out solution, equivalent lineage, inherited human difficulty, or training admission is claimed.

## Execution and exports

Run from the outer packet directory, using the interpreter that passes `review.py python-check`:

```sh
WORK/.venv/bin/python review.py run python3 generators/bedcbc1cb6fb/workspace/parametric/prototype.py --out ../checks/bedcbc1cb6fb/examples --seed 17 --demos 3
WORK/.venv/bin/python review.py run python3 -m pytest generators/bedcbc1cb6fb/tests/test_native_parametric.py -q
WORK/.venv/bin/python review.py run python3 generators/bedcbc1cb6fb/workspace/parametric/self_audit.py --out ../checks/bedcbc1cb6fb/self-audit --seeds 0 2 3 17 9223372036854775807
```

`program(settings)` materializes exact Racket source; `generate(seed, settings, demos=3, queries=4)` returns labeled private pairs and that source. `sample_inputs` is setting-independent. Seed values must be exact integers 0..2**63−1; booleans, noninteger counts, undeclared settings and unsupported counts fail explicitly.

`public_turn(episode, query_index=0)` exposes demonstrations and exactly one query input. The consumer reveals later queries one at a time after the preceding answer, without a count, final-turn cue, future inputs or private metadata. No controller or training loop is introduced. The first turn is identical for one-query and four-query generation. Public filenames hash the exact bytes written by `reviewer_support.public_challenge_bytes`; private seeds, settings, programs and query answers cannot affect those bytes or names. The example writer retains both settings' four-query episodes privately and writes their first turns publicly. Its destination must be new or empty; a nonempty destination is rejected before generation or writes, preserving existing public/private evidence. Use a fresh `--out` when rerunning the example command.

## Review boundary

`adapter.py`, `promotion.json`, the native inventory and source-bound qualification are the owner handoff. Reviewer qualification does not accept this candidate. Fresh owner qualification and exact-source acceptance remain required after integration. No training activation follows from this work.
