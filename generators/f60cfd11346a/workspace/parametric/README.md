# f60cfd11346a native parametric family

`mode=canonical` preserves the selected program byte-for-byte. In
`mode=reachable_port_relay`, step A computes the red seed's `{0,2}` reachable
component. The input-dependent intermediate is the number (1–3) of color-1
ports cardinally adjacent to that component. Step B uses that count to select
the corresponding row-major color-3 anchor and fills its remote zero chamber.
Three total ports are always present; the non-counted ports border an isolated
pocket, so counting all ports skips the required flood and selects the wrong
chamber.

The input stream is identical across settings, supports 2–6 demonstrations and
1–4 prefix-stable private queries, and includes a substantive 30×30 fourth
query.

From the packet outer directory:

```bash
python3 review.py run python3 -m pytest \
  generators/f60cfd11346a/tests/test_parametric_reachable_port_relay.py -q
python3 review.py run python3 -m arcpuzzles parametric qualify f60cfd11346a \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/f60cfd11346a/qualification --summary
```
