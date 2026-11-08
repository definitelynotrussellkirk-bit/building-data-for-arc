# Source-bound supplementary finding

## 74e83caa0660

**Ticket:** `ticket-e3e109a04bde408f` (`api_boundary`)  
**Pinned source:** `generators/74e83caa0660/generator.py` v2.0.1, SHA-256
`26f5b1f9c343e2e9faa3a69fb4d7065dc8ca33d7e9ec44754f0199023b89e690`.

`AXES` advertises `n_pairs` with valid range `1..8`, but `generate` performs its
count draw under the different key `pairs`. The one-shot probe showed:

- baseline: 2 active colors;
- advertised valid `n_pairs=1`: accepted, byte-identical to baseline;
- advertised invalid `n_pairs=9`: accepted, byte-identical to baseline;
- undocumented `pairs=2`: 2 active colors;
- undocumented `pairs=4`: 4 active colors.

Thus the public override is inert and its declared validity boundary is not
enforced. This can silently defeat exact-control authoring and allows invalid
requests to appear successful. Suggested repair: validate unknown overrides,
consume `n_pairs` under its advertised name, and add exact tests for `1`, `8`,
a non-integer, and an out-of-range value. No peer source was edited in this
assignment. Reproducer and receipt:
`checks/tickets/ticket-e3e109a04bde408f/probe.py` and
`checks/tickets/ticket-e3e109a04bde408f/result.json`.
