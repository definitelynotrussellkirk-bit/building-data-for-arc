# Reviewer authoring tools — October 3 update

Astra implemented source-identical battery resume with prior-attempt retention,
current environment/settings checks, validated checkpoint restoration and kernel
writer exclusion. Source changes require fresh output. Override checking now
prints a cost PLAN before work and periodic progress; optional compact reports
preserve results/hashes/witnesses while omitting successful case detail. Defaults
stay compatible. Missing pytest is classified as dependency_missing.

Both per-puzzle materializers now originate accepted sample positions, split/pair
indices and full input hashes, plus rejection reasons and next sample index.
Census reports actual accepted train/test residues separately from requested
starts. Additive metadata does not change the generator RNG or model harness.

The public CPU suite passed 302 tests; Astra's focused set passed 35, root's
materializer/census set 21, and extracted packet focused tests 33. These sets
overlap and their counts must not be summed as unique tests. A real extracted
Racket smoke exercised query rotation and actual indices: two production lessons
were unambiguous; one of eight rotated queries was ambiguous. That limitation is
retained in the source-bound task note, not suppressed. Full qualification receipts
are in var/review/tooling-qualification/resume-indices-20261003/.

The resume guide is included in the sendable packet and WELCOME gives the commands.
Tools support reviewer work; they do not add routine maintainer batteries, change
ARC2's model harness, replay private solves or admit trajectories to training.
