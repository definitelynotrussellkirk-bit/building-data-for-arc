# Native cap-policy family for `2da4094bc0e1`

- `both_sides` is the byte-exact canonical rule.
- `cue_controlled_side` selects the nearest yellow length-4/5 control bar to
  the unique red cue; length 4 means left caps and length 5 means right caps.
- Inputs are matched across settings, support 2–6 demonstrations and 1–4
  prefix-stable queries, and include a substantive 30×30 case.
- `farthest_control_side.rkt` is a causal counterfactual for the selected
  control intermediate, not a promoted setting.
- `audit.py` provides bounded finite-rival and qualification/public-export
  auditing for future reviewers.
