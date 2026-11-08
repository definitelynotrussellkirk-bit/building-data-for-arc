# Native parametric family: e777125624ca

Parameter `rule_mode` has two episode-fixed settings:

- `nor` — the exact canonical rule: output 8 at aligned `00` cells.
- `sparser_difference` — count occupied cells in both panels, select the uniquely
  sparser panel, then output 8 where that panel is empty and the other is occupied.

The alternate has a real sequential dependency: **A** computes both panel
occupancy counts; the intermediate is `left` or `right`; **B** uses that side to
choose whether aligned state `01` or `10` is marked. Inputs are independent of
this hidden setting, contain all four aligned states, and alternate the selected
side across demonstrations and queries.

Supported calls use 2–6 demonstrations and 1–4 queries. A four-query call is:

```sh
python3 -m arcpuzzles parametric generate e777125624ca \
  --settings '{"rule_mode":"sparser_difference"}' --seed 0 --demos 2 --queries 4
```

The canonical domain is fixed at width 7, so exact 30×30 inputs are not lawful;
the maximum stress case is 30×7 with substantive content across both panels.
The evidence is authoring/self-review material only, not owner acceptance or
training admission.
