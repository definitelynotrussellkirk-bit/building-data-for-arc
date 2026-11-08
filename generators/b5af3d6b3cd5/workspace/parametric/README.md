# Native gravity relay prototype

`mode=canonical` is the exact selected room-gravity rule. In
`mode=bottom_color_relay`, step A applies stable downward gravity; the intermediate
is the number (1–3) of controller-room columns whose settled bottom marker is
color 9; step B uses that number to select one of three payload rooms and recolors
its settled markers to color 8. Inputs are independent of the mode.

The adapter supports 2–6 demonstrations and 1–4 queries. With four queries, the
fourth is a substantive 30×30 case. `verify.py` checks matched inputs, boundaries,
prefix stability through tests, and a finite set of plausible shortcuts. The
protected counterfactual counts color-9 cells on the controller's raw bottom row,
skipping the gravity-derived intermediate.
