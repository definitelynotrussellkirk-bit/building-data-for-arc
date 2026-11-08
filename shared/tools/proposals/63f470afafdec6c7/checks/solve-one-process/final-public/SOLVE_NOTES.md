# Final-source solve and administrative recovery

Earlier rule exposure: yes, during this generator repair. Reference consulted
during this final visible-only solve phase: no. I had also previously attempted
this same deterministic final-source public challenge. This is an exposed
reviewer work log, not an independent blind solve or a token-level trace.

The visible examples are 12 by 12, 4 by 7, and 5 by 4. Their occupied row and
column cross at zero-based (5,10), (2,4), and (3,2). All eight neighbors become
color4; the center and outside pixels are preserved. The first center follows
the horizontal line. The second preserves color1 despite color9 being more
frequent. These observations reject diagonal-only painting, row/column
coordinate copying, and replacing the center with the modal input color.

My submitted Python finds the complete occupied row and column, copies the
input and paints their eight neighboring cells. This is the same behavioral
hypothesis previously checked on this final-source challenge. Query inputs
are 11 by 7 and 6 by 6; their labels and correctness remain unknown.

An intermediate-source completed solve and later mixed public sessions are
retained in checks/prior-solve. After a verified whole-directory move, old
attempt files and an old finish snapshot unexpectedly reappeared across tool
calls. Generic packet-source inspection found no copy-back path. The cause
of that cross-call restoration is unresolved; it should not be attributed
solely to reviewer cleanup or to packet rehydration. Two official finish
failures are administrative failures, not wrong visible predictions.

This recovery archives the whole public directory, then runs official
prepare/check/finish in one process with directory inventories between steps.
It keeps old frozen bytes and private controller state intact. Preparation
uses the same final generator and deterministic public challenge, so the
recheck is not another independent sampled episode. The current implementation
is my own working program, carried forward before this preparation. After
preparation only public examples, this own Python and visible check feedback
are used; no generator/rule source, private labels or external solution is
consulted. Actual active revision numbering and finish status are recorded
by the official commands, not edited by this recovery.

I stop after all three visible examples pass. The maintainer must independently
score the masked queries. No hidden-query success is claimed.
