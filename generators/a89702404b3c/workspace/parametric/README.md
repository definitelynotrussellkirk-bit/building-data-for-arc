# a89702404b3c parametric family

`corner_crop` is the exact canonical program. `corner_key_payload` first applies
that parity-selected crop, reads its upper-left color as a key, then uses the key
in the bottom marker row to select one of two 2x2 payloads. Marker-to-payload
placement varies independently of width parity; the minimum three demonstrations
show both parity branches and repeat odd parity with opposite marker placement.

Focused run:

```bash
python3 review.py run python3 -m pytest -q \
  generators/a89702404b3c/tests/test_generator_a89702404b3c.py \
  generators/a89702404b3c/tests/test_parametric_corner_key_payload.py
```
