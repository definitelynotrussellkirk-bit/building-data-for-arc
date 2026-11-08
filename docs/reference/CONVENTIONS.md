# THIS REPO — running conventions & arbitrary definitions

The load-bearing assumptions and the things we *decided* (not discovered) — stated once, here, so they're
consistent everywhere. If code disagrees with this doc, the code is wrong (or this doc is stale — fix one).
Referenced from CLAUDE.md. (Task #43.)

## 1. Grids
- A grid is a rectangular matrix of ints in **0–9** (10 colors). Height and width are each **1–30**.
- **Color names** (fixed): 0=black 1=blue 2=red 3=green 4=yellow 5=gray 6=magenta 7=orange 8=cyan 9=maroon.
- Scoring is **pixel-perfect, pass@2** (two attempts per test input).

## 2. Background is NOT assumed to be 0
- Color 0 is *often* the background, but ARC frequently uses a different background. **Do not hard-code
  bg=0.** Determine background per task: the **modal color**, or the **border-modal color**, or run a feature
  under a **background-hypothesis bank** b ∈ {0, modal, border-modal, each present color} and let the model
  select. Generators/solvers that assume bg=0 are a recurring defect class.

## 3. "Object" is ambiguous — name the parse
When a feature/solver depends on object segmentation, state which parse it uses. The standard parses:
- **mono-4** — same-color 4-connected components.
- **mono-8** — same-color 8-connected components.
- **multicolor** — 4/8-connected components of all non-background cells (color-agnostic).
- **empty-space** — components of background-b cells (per background hypothesis).
Object-level features are ideally computed under **multiple** parses and broadcast to member cells.

## 4. SENTINEL discipline (critical for the feature bank)
- Absent / not-applicable values MUST use an explicit sentinel **distinct from every valid value** — never
  overload 0 (or "self", or "none"). Feature dropout teaches the model to cope with a *missing* channel; a
  *present* channel carrying an overloaded sentinel silently **lies**, which is worse than absent.
- Use **distinct** sentinels for **distinct facts**: "not applicable", "out of bounds", and "no such target
  exists" are three different things. In the feature modules the default is **`SENTINEL = -1`**.
- Incompleteness is a **correctness bug**, not a robustness knob. Where a feature surfaces a relation it must
  be **exhaustive** over that relation's space (all 10 colors / all 8 directions / all D4 axes / all parses).

## 5. Causal validity (INPUT-ONLY vs OUTPUT-DERIVED)
- **INPUT-ONLY**: derived from an input grid alone → safe on demos AND the test query. → `cell_features.py`.
- **OUTPUT-DERIVED**: derived from the input→output relationship (diff, recolor map, invariance) → available
  ONLY on demonstration pairs. Must be **masked/zeroed on the test query**, or routed to an auxiliary
  prediction target the model learns to infer. → `output_features.py`. **Never** leak these on the query.
- A demo-derived *parameter* (e.g. a recolor map inferred from demos) *applied to the query input* is safe —
  keep provenance explicit.

## 6. Canonical identifiers, not accidental ones
- Do **not** surface raw component/panel/shape IDs from flood-fill traversal order — they change meaning
  across tasks and grids. Surface a **deterministic rank** under a canonical sort
  (top, left, bottom, right, dominant-color, size, raster-signature), or an equality/relative relation.
- Categorical IDs feed the model only via learned embeddings alongside equality/relative features.

## 7. Solutions are Racket
- Every grounded rule, canonical `program_solution`, and taught primitive is **Racket** (the model only reads
  Racket). Python is tooling only. Enumerated lookup tables (`apply-local-rewrite` with grid literals,
  `(if (equal? g <literal>) …)`) are **NOT valid solutions** — they memorize, they don't generalize (task #37).

## 8. Feature-module encoding (task #38)
- Planes are `numpy int64`, one named `HxW` array per feature; whole-grid/object/color scalars are broadcast
  to constant planes. Integers stay **exact** (range ≤ ~30 + sentinel) until the model's projection/embedding
  layer — no premature normalization. Booleans are their own channels. Categoricals (color/id) → embeddings.
- **Feature dropout is family-level**: drop a whole coherent family (all symmetry axes / all period channels /
  all output-derived labels), never truncate *within* a family unless a missingness mask says what was removed.

## 9. Where training actually runs
- Training runs on a **remote RTX 4090 machine**, not locally, not Colab. See CLAUDE.md's
  REMOTE 4090 block for the live commands. Data producers run locally; `/mnt/ai` is a shared mount.
