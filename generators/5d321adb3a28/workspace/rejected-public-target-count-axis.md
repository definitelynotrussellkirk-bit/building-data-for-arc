# Rejected public `target_count_profile` axis

The first repair draft exposed `2h1v|1h2v` as a third exact axis. Its focused
regression passed, but the retained frozen fixture asserts the existing public
surface and exact two-key `observe_overrides()` result. Expanding the public
contract was unnecessary to fix the distribution and would make old consumers
see a new key.

The preserved patch is a rejected design, not part of the selected repair. The
selected implementation keeps `AXES` and `observe_overrides()` unchanged and
samples canonical target multiplicity deterministically inside the layout RNG.
