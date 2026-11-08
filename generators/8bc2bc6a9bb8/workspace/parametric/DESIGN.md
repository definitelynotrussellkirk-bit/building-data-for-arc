# Sort-key parametric family design

## Intent

Build a task-local, unapproved parametric extension for `8bc2bc6a9bb8` that preserves the original palette → component extraction → ranking → recoloring → bottom-aligned packing pipeline while making the ranking measure an episode-fixed rule parameter. The work must also close the selected generator's retained teaching hole: its finite shape bank never made occupied-cell area disagree with bounding-box footprint.

## Goals

- Keep `sort_key=occupied_area` byte-for-byte equal to the canonical Racket program.
- Add `sort_key=bbox_area`, sorting by descending bounding-box area with occupied area and source position as deterministic tie-breaks.
- Sample identical lawful inputs for both settings; every authored demonstration must distinguish the two settings.
- Support independent `2..6` demonstration and `1..8` query counts, with the retained evidence using three demonstrations and four distinct queries.
- Include substantive 30×30 query coverage, real boundary contacts, spread across the canvas, and protected-Racket labels for every pair.
- Keep hidden settings, programs, seeds, and query answers out of public challenge bytes and identifiers.
- Supply a thin `adapter.py`, `promotion.json`, focused tests, bounded adversarial evidence, and the native manifest inventory.
- Preserve the canonical production rule and authority. A proposed variant is not approval or training admission.

## Non-goals and anti-goals

- Do not change the canonical Racket rule or catalog kind.
- Do not parameterize the two secondary targets.
- Do not make the task easier by deleting recoloring, packing, alignment, or spacing branches.
- Do not use query answers to certify identifiability.
- Do not claim uniqueness beyond the declared sort-key rival or claim measured learning benefit.

## Constraints

- Work only in the three assigned generator homes and required packet return files.
- Public grids and outputs must remain rectangular integer ARC grids with dimensions at most 30×30.
- Demonstrations are limited to `2..6`; ordinary evidence uses three. Four-query evidence must include distinct inputs and the same first public turn as a one-query projection.
- The packet has no Git metadata; verification receipts replace commit checkpoints.

## Approaches considered

### 1. Alignment or gap parameter

This would be easy to materialize, but top alignment and zero-gap are already declared canonical rivals. It adds a cosmetic nearby behavior without addressing the open area-versus-footprint under-identification.

### 2. Occupied-area versus bounding-box-area ranking — selected

This changes the central inferred rule while preserving every other reasoning step. It directly uses the retained counterexample class: a five-cell line has footprint five while a four-cell L can have footprint six, so the two settings reverse their first two packed objects. The same inputs can teach both settings, and the canonical default remains exact.

### 3. Add a preprocessing composition

A merge/recolor preprocessing stage could create sequential-state reasoning, but it would be a larger unrelated rule family and would not repair the concrete selected-source teaching defect. It is deferred.

## Architecture

`prototype.py` owns setting validation, exact Racket materialization, a setting-neutral deterministic sampler, independent Python diagnostics, Racket execution, episode construction, public projection, evidence writing, and the CLI. The sampler uses curated connected polyomino profiles whose occupied-area and footprint orders disagree; query profile four is exactly 30×30 and uses real edge contacts and widely separated objects rather than padding.

`adapter.py` is a thin promotion adapter over `prototype.py`. `promotion.json` declares the two settings and bounded count surface. `adversarial_probe.py` exercises minimum/maximum counts, setting/Racket parity, public/private identifier invariance, exact integer cells, and the 30×30 profile. Task-local tests cover both the canonical generator repair and the proposed prototype.

The canonical generator gains a constructive footprint-conflict shape pair in one schedule profile plus a declared executable footprint-primary rival. Every four-profile lesson must refute it.

## Peer checks

- `be5d9fa6fec1`: reject unknown difficulty strings instead of silently falling back to the default profile mixture; add a regression.
- `6fde852adb54`: run one bounded source-bound parser/control probe. Change source only for a clear local defect; otherwise report unchanged.

## Success criteria

- The new canonical shortcut regression fails before the generator repair and passes after it.
- Prototype tests fail before implementation and then pass with real protected-Racket execution.
- Default prototype program equals the canonical source exactly; the alternate produces a different output on every generated pair.
- Three-demo/four-query evidence exists for both settings, includes a 30×30 query, has no duplicate inputs, and passes public export validation.
- The adapter contract and native parametric manifest are current.
- Focused task tests and the bounded peer checks pass, and `review.py package` produces the delta ZIP.
