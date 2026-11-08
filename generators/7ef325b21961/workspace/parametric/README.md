# Local frame statistic parametric family

The canonical `majority` setting preserves the exact catalog Racket bytes.  The
nearby `minority` setting keeps the same frame discovery, local color counting,
border preservation, interior fill, and outside-noise erasure, but selects the
least frequent local dot color instead of the most frequent one.

For every frame, step A discovers that frame's interior and computes its two
input-dependent local counts.  Step B consumes the selected local color to fill
that frame; using another frame's statistic changes the output.

Focused verification from the packet outer directory:

```sh
python3 review.py run python3 -m pytest generators/7ef325b21961/tests/test_parametric_frames.py -q
python3 review.py run python3 -c 'from pathlib import Path; import importlib.util, json; p=Path("generators/7ef325b21961/workspace/parametric/prototype.py"); s=importlib.util.spec_from_file_location("p",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(json.dumps(m.audit(),indent=2))'
```

The audit is bounded to the declared two-setting family and named finite rivals;
it is not a universal uniqueness proof or owner acceptance.
