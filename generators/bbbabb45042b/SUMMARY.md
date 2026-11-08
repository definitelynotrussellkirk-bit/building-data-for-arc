# bbbabb45042b

A zero-background grid contains one connected four-cell red (2) template, one to three isolated blue (1) anchor cells, and sometimes one smaller singleton red distractor.  Normalize the largest red component by its bounding-box top-left and copy those offsets in blue at every anchor, preserving the input.  Therefore an anchor is part of the copied shape when the template contains normalized offset (0, 0), but remains as an extra marker when that offset is absent.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
