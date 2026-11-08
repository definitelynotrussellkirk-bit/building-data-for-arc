# Native frame-band area relay

`relay_policy=fill_only` returns canonical.rkt byte-for-byte. `key_relay` executes
that same fill, detects the one magenta component adjacent to newly filled cyan,
and recolors the unique blue component of equal occupied area green. Existing
cyan, off-row red, irregular receivers and missing/overflow row selectors matter.

The new grammar has 2–3 nested yellow rectangles, one horizontal magenta key per
band, and five separated blue receivers with distinct areas. It deliberately
extends production with remote receivers; production and its approved source are
unchanged. Receiver shapes need not match key shapes. The ordinary canvas is
22–26 by 26–29; a full 30×30 query has substantial nested and remote content.
The remaining limits are the finite declared grammar, no new arbitrary color
roles, and finite-rival evidence rather than universal identifiability.

`generate(seed, settings, demos, queries)` accepts independent integer counts
2–6 and 1–4. Geometry and query-presentation RNGs are separate from settings.
Always construct and shuffle the full four-query bank before taking a prefix.
`public_view(episode, index)` returns only demo pairs and the current input, with
no total query count. The controller owns the private episode and directory.

Run from the outer packet directory:
```sh
python3 review.py run python3 generators/0f075657ddbb/workspace/parametric/audit.py --out generators/0f075657ddbb/workspace/parametric/evidence/new-audit --seeds 20
python3 review.py task-tests 0f075657ddbb --phase after --out ../checks/new-tests
```
The audit refuses existing output directories, executes all authored rival rules
with protected Racket, writes exact labels privately, and writes public views in
visible-content-hash order. Its sweep counts repeated prefix requests separately
from unique inputs. Native qualification, causal witness replay and owner
acceptance remain distinct operations. No training admission.
