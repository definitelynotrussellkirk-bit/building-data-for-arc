# Marker-vector direction family

`direction=one_to_two` is the byte-exact canonical rule. `two_to_one` reverses
the marker relation while retaining the same two-stage reasoning: derive the
input-dependent marker displacement, then translate every green component by it.
The sampler keeps both translations in bounds, uses multiple green components,
supports 2–6 demonstrations and 1–4 queries independently, and places a
substantive 30×30 scene in the four-query bank.
