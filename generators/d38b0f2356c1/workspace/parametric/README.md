# Marker-color parametric prototype

**Status: proposed authoring evidence only.** The canonical generator, selected
Racket authority, approval state, and training admission are unchanged.

`marker_color` is fixed for the episode. The canonical value `8` selects the
unique 3×3 block without cyan and returns the selected program byte-for-byte.
The alternate value `9` selects the unique block without maroon. Every sampled
input has distinct unique no-8 and no-9 blocks, so matched demonstrations expose
which absence rule is active while preserving the original macro-expansion.

The selected rule is structurally fixed to an 11×11 lattice of nine 3×3 blocks;
a 30×30 stress would change the grammar and is therefore not lawful for this
family. The retained evidence instead stresses all block positions, dense
interiors, four distinct queries, demo counts 2–6, and corrupted exports.

From the packet directory:

```bash
python3 review.py run python3 -m pytest \
  generators/d38b0f2356c1/tests/test_parametric_marker_color.py -q
python3 review.py run python3 \
  generators/d38b0f2356c1/workspace/parametric/prototype.py build \
  --seed 17 --demos 3 --queries 4 \
  --out ../checks/d38b0f2356c1-marker-color
```

The writer hashes exact public bytes containing only demonstrations and query
inputs. Private settings, programs, answers, certificates, source bindings, and
protected-Racket identity are stored separately. `verify` replays both programs
against every pair and rejects inventory, runtime, label, and identity tampering.
