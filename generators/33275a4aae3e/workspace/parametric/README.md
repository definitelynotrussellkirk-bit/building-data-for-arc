# Enclosed-area threshold prototype

Status: **proposed, task-local prototype**. This does not alter the selected
generator, canonical Racket authority, catalog, approval state, or production API.

## Design

`min_enclosed_area` has the bounded values **1, 32, 40**. Its canonical/default
setting is **1**. A zero cell becomes red (2) exactly when its four-connected
zero component is enclosed and its area is at least the threshold. Every other
zero becomes green (3); original nonzero cells remain unchanged. The parameter
changes the executed transformation. Component finding, boundary reachability,
network roles, and the order of filling and background recoloring stay intact.

The initial v2.0.0 generator probe (SHA-256 prefix `4d6065d6e67a`) found enclosed
component areas 20–49 in 96 inputs, with no area below 16. Thus 1 and 16 would
be indistinguishable on those draws. Values 32 and 40 give meaningful
alternatives inside the network distribution without inventing a different
input family. This finite probe is motivation, not proof of full support.
Canonical repairs may widen the area distribution; the prototype samples the
currently selected source and does not assume its old lower area bound.

`materialize_racket()` and the Python comparison oracle default to 1.
`build_episode(seed)` selects one value deterministically from the seed;
`build_episode(seed, min_enclosed_area=32)` requests a value explicitly. The
chosen value is fixed across the complete episode. Geometry sampling is
independent of the selected threshold: the same seed produces the same inputs
under all three explicit settings.

Each episode contains three demonstrations and one query, in this order:
**threshold witness, connectivity witness, threshold witness, connectivity
witness**. Each threshold witness is a legacy network with an enclosed component
below 32 and another of area 32–39. Each connectivity witness is a selected
stepped profile with both a nonrectangular enclosure and a diagonal seal; its
nonrectangular region must still refute rectangle enumeration at threshold 40.
These are parameter-independent selection constraints on legal generator
outputs, with a bounded candidate budget and explicit failure if unmet.

The demonstrations collectively distinguish all declared parameter values.
Any one-query holdout leaves at least one witness of each kind. This preserves
the repaired family's connectivity evidence while teaching the area threshold.
It also shows retained red behavior at 40. Not every pair distinguishes all
thresholds by itself. The episode distribution remains narrower than ordinary
canonical generation, and currently requires the selected v2.1.0 source's
`CONNECTIVITY_PROFILES` and semantic witness declarations.

Two additional Python diagnostic rivals are scored against the Racket labels:
complete-rectangle filling filtered by component area, and eight-neighbor
component enclosure using the same threshold. Stepped inputs refute the
rectangle shortcut at all three settings. Their tiny diagonally sealed pockets
are below 32, so they **do not distinguish four- from eight-neighbor enclosure
at 32 or 40**. The eight-neighbor rival's `survived_all` result is retained. It is
refuted at the canonical setting 1. These extra controls are distinct from the
Racket-executed parameter rivals and do not prove universal identifiability.

## Runtime and execution

Dependencies are the packet's existing Python runtime (NumPy, Pillow, pytest for
tests) and its included offline Racket runtime. No new dependency is required.
The runner uses `reviewer_support.find_root`, `load_selected_generator`, and
`canonical_pairs` so source and canonical examples stay tied to its own tree.

Every label and every declared-parameter rival prediction is executed through
the public protected `RacketBridge` API. A plain lexical identity binding for
`rule!` executes the exact materialized callable-lambda program. This adapter
is deliberately restricted to the prototype's lambda-form programs; it is not
a general ARC command interpreter. The Python oracle checks Racket outputs
independently and never supplies authoritative episode labels.

From `WORK/`, using an absolute Python executable for the payload:

```bash
.venv/bin/python run_with_racket.py "$PWD/.venv/bin/python" \
  generators/33275a4aae3e/workspace/parametric/prototype.py \
  --seeds 17,29,41 --out ../checks/parametric/evidence

.venv/bin/python run_with_racket.py "$PWD/.venv/bin/python" \
  -m pytest -q generators/33275a4aae3e/tests/test_parametric_33275a4aae3e.py
```

The first command demonstrates all three explicit settings for each seed.
Use `--min-enclosed-area 32` for only that setting, or `--seed-selected` to
choose each episode's setting from its seed. The output directory must be new;
failed runs retain a failure receipt and private progress containing every
completed episode. The directory is claimed before Racket starts, so even a
startup failure cannot overwrite earlier evidence.

## Evidence boundary

Only `public/episode-*.challenge.json` files are model-visible challenges. They
contain demonstration inputs/outputs and query inputs, with opaque filenames.
They omit hidden parameters, programs, source identity, and query answers.

`private_evidence.json`, `programs/`, and any `failure.json` are authoring
evidence. They retain parameters, seeds, exact programs and SHA-256 hashes,
prototype/generator/runtime source identities, accepted sample indices,
selection rejection counts, input/output hashes, canonical positive controls,
declared-rival comparisons, all query rotations, and actual payload invocation.
Every selected scene profile is also drawn once and checked at all three
thresholds, including profiles that the episode area-band filter cannot admit.
Those separate semantic controls do not establish teachability for those shapes.
An export fails if any recorded source changes while it runs.
Source-bound evidence is finite; it is not universal identifiability, production
integration, or training admission. The CLI reports only the settings and seeds
actually executed. A failed macro-wrapper exploration and its successful plain
binding replacement are retained in `checks/parametric/api_probe.json`.
