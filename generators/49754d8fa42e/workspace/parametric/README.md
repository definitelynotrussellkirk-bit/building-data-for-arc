# Native parametric family for `49754d8fa42e`

The native adapter adds an input-dependent composition while preserving the
selected production generator and exact canonical Racket source. The episode
fixes one private parameter:

| `orientation` | Executed transformation |
|---|---|
| `canonical` (default) | Count nonzero cells; the unique modal color 1, 2, or 3 selects the original gray plus, T, or right-facing L. |
| `modal_components` | Select that same color, count its monochrome 4-connected components, and rotate its original glyph clockwise by `(component_count - 1) % 4` quarter-turns. |

Stage A supplies the selected color and its cell mask. Stage B must examine
components of that particular mask to choose the rotation. Counting all colors'
objects, using an 8-connected mask, and choosing the largest spatial object are
different rules. Output remains a 3×3 grid containing only zero and gray.

## Runnable entry points

Use the Python 3.12+ interpreter that passed `review.py python-check`. These
commands run from the packet's outer directory after `review.py setup`:

```bash
python3 review.py run python3 -m pytest \
  generators/49754d8fa42e/tests/test_native_adapter.py \
  generators/49754d8fa42e/tests/test_native_composition.py \
  generators/49754d8fa42e/tests/test_native_export.py \
  generators/49754d8fa42e/tests/test_native_audit.py -q

python3 review.py run python3 \
  generators/49754d8fa42e/workspace/parametric/audit_native.py \
  --out ../checks/49754d8fa42e/audit-replay

python3 review.py run python3 \
  generators/49754d8fa42e/workspace/parametric/make_examples.py \
  --seed 0 --demos 3 --queries 4 \
  --out ../checks/49754d8fa42e/examples-replay

python3 review.py run python3 -m arcpuzzles parametric qualify 49754d8fa42e \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/49754d8fa42e/qualification-replay --summary
```

Choose fresh output paths when replaying. The qualification command expects the
current native source/evidence inventory. If source changes, regenerate that
inventory with `arcpuzzles parametric manifest` and its guarded `--replace`
mechanism before qualifying again; an old receipt cannot qualify edited code.

`adapter.py` delegates to `composition.py`. The latter reuses the legacy
prototype's glyph and canonical-program helpers, returns deterministic claimed
labels, and does not execute a nested Racket audit. Native qualification and
`make_examples.py` independently execute the complete setting programs through
protected Racket before producing validated labels.

## Teaching and sampling contract

Demonstration and query counts are independent: **2–6 demos and 1–4 queries**,
defaulting to three and four. The first two demonstrations use the same modal
class and histogram but different modal connectivity. This makes a fixed
per-color glyph or count-only orientation insufficient for the composed rule.
Diagonal contacts distinguish four- from eight-neighbor connectivity. Minority
colors provide counting, endpoint, bounding-box, and largest-object decoys.
Query modal classes are restricted to those demonstrated in that episode.

Inputs are matched across the two settings for the same seed and request.
Query inputs differ from each other and from the demonstrations. The fourth
query extends the grammar to a substantive 30×30 scene rather than placing a
small scene in empty padding. This larger native grammar is separate from the
unchanged production generator's 3..10 dimension controls.

`audit_native.py` executes the two setting programs and a bounded catalog of
alternative selectors, connectivity rules, and rotation rules. It fits each
candidate to demonstrations first, freezes the survivor set, and then checks
query disagreement. Selector rivals feed their chosen color into both glyph
selection and the component counter. Runtime errors fail the audit; they do not
count as evidence against a hypothesis. Equivalent surviving rules are reported
as survivors, not falsely called refuted. The private audit includes exact
programs, hashes, execution identity, and retained cases.

## One-query model interface

`export.public_turn(episode, query_index)` returns exactly the demonstrations and
one current query input. It excludes answers, settings, private metadata, future
queries, total query count, and final-turn hints. Its first-turn bytes are the
same whether the controller later continues or stops after one answer.

`make_examples.py` materializes both settings through protected Racket and
`export.write_batch` writes:

| Path | Consumer and contents |
|---|---|
| `turns/<visible-byte-sha256>.json` | Actor: demos and one query input only. |
| `public/<visible-byte-sha256>.json` | Controller: demos and all query inputs; do not send this whole object to an actor. |
| `private/metadata.jsonl` | Controller: ordered turn IDs, settings, programs, query answers, and execution certificates. |

The controller reveals a new turn only after receiving the preceding answer.
The exporter refuses existing destinations and rejects duplicate visible
payloads before writing. Public IDs depend only on exact canonical visible bytes.
The transport writer itself does not authenticate labels; use the protected
example builder or native execution before calling it.

## Scope and retained legacy API

The selected production generator remains v3.3.0, SHA-256
`99216a3011a7653571ee5539b6782bc5403d40f207bfab945fadeefdf02af6c6`.
The default program is preserved byte-for-byte. The original
`prototype.py`, `verify.py`, `quarter_turns_clockwise ∈ {0,1,2,3}` API, and its
five-demo/two-query artifacts remain historical, separate functionality.
The native promotion contract exposes only the two `orientation` settings.

Qualification and the counterfactual witness are bounded, source-bound reviewer
evidence. They do not establish uniqueness against arbitrary programs, universal
sampler coverage, measured learning benefit, owner acceptance, or training
admission. Exact-source owner qualification and acceptance remain the next
integration step; exported examples explicitly retain pending status.
