# 8738d400fb96 translated-footprint cue relay

`finish_rule=translate_only` is the exact selected canonical program.
`finish_rule=translated_cue_relay` performs the same largest-green translation,
reads the unique foreign cue color under the translated footprint, and paints
that color's remote payload together with the translated footprint.

Run focused checks from the packet root:

```bash
python3 review.py run python3 -m pytest generators/8738d400fb96/tests/test_parameters.py -q
python3 review.py run python3 -m arcpuzzles parametric qualify 8738d400fb96 --out ../checks/8738d400fb96/qualification --summary
```
