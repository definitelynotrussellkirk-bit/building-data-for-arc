# Review workspace

`reference_probe.py` is an independent task-local geometry oracle, rival suite,
canonical-data loader, and real-Racket parity helper.  It deliberately does not
reuse production generator analysis functions.

`probes/authority_inputs.json` contains disconnected/nonconcentric inputs used
with the supported `arcpuzzles apply` command to check the selected Racket rule.
The selected implementation remains `../generator.py`; workspace files are never
automatically selected for production.
