# Biggest avoidable friction: stale witness recipes after a failed template command

F1: The wrapper printed a failed `review_witness template` operation but allowed a chained shell command to continue with the prior recipe. Propagate the wrapped nonzero exit status reliably and add an explicit `--force` option for intentional recipe regeneration.
