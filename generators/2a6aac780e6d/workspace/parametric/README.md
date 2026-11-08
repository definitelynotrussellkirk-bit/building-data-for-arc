# Native parametric family

`fill_scope=all_qualifying` is the byte-exact canonical rule. In
`fill_scope=key_selected`, a unique `8 ... 5 ... 8` key row supplies a 1-based
rank: the distance from the left `8` to the `5`. Qualifying payload rows are
ordered top-to-bottom and only the ranked row is filled.

Sequential dependency: **A** reads the key and produces the selected payload
row; **B** consumes that row record to paint its endpoint span. `always_first.rkt`
is the protected wrong-intermediate counterfactual.
