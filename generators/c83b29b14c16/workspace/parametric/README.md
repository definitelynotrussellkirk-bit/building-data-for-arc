# Exact-count connector prototype

**Status: proposed, not accepted.** The production generator and canonical
Racket authority remain separate. This prototype keeps the original alignment,
object-count, and line-filling reasoning while making the qualifying occurrence
count episode-fixed: `required_count=2` is the exact canonical rule and
`required_count=3` connects only collinear three-marker colors between their
extrema.

Inputs are identical across settings for a given seed and request. Every scene
contains horizontal and vertical groups of both counts, plus skew two-marker and
non-collinear three-marker controls. Thus labels—not input statistics—identify
the setting. Requests support 2–6 demonstrations and 1–8 queries independently;
the first four query profiles are 13×17, 18×18, 24×20, and a substantive 30×30
boundary-spanning scene. Settings, seed, Racket source, certificates, and query
answers are controller-private. `reviewer_support.public_challenge_bytes` exposes
only demonstrations and masked query inputs.

From the outer packet directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/c83b29b14c16/tests/test_parametric_count_mode.py
```

The focused test executes every retained label for both settings through the
bundled protected Racket runtime. Finite identification is only against the two
declared settings; it is not uniqueness against unrestricted programs, owner
qualification, variant acceptance, or training admission.
