# Workspace tools

The selected implementation is `../generator.py`; workspace files are support
artifacts and are never selected automatically.

## `reference_probe.py`

This independent finite-domain probe exhausts all 36 `pair_index` values × all
4 `bad_mask` values in each of the four difficulty settings. It checks the
public exact overrides, `self_check`, override observation, and `rule_mirror`
against a separate Python translation of the pinned rule. It also reports the
20/12/4 census of valid placements adding zero/one/two diamonds, the 144-input
exact domain, its 37-output codomain, and the 17-output default sampler probe.

Run from the repository root:

```bash
PYTHONPATH=shared/runtime:src \
python3 generators/56072bfdb820/workspace/reference_probe.py \
  --out /tmp/56072bfdb820-probe.json \
  --inputs-dir /tmp/56072bfdb820-apply-inputs
```

`arcpuzzles apply` accepts at most 64 inputs per call, so `--inputs-dir` emits
three directly consumable files (64, 64, and 16 inputs) plus a manifest:

```bash
for input in /tmp/56072bfdb820-apply-inputs/inputs-*.json; do
  PYTHONPATH=shared/runtime:src \
  python3 -m arcpuzzles apply 56072bfdb820 \
    --input "$input" \
    --out "${input%.json}-outputs.json"
done
```

`--inputs-out FILE` is also available when a single 144-input analysis file is
more convenient, but that file must be split before use with `arcpuzzles apply`.
All output paths are create-only. The probe is bounded and deterministic; it
does not read canonical answers or private labels.
