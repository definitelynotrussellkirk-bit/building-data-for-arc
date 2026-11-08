# Non-applying frozen-fixture migration proposal

The selected baseline fixture remains byte-identical to the supplied packet.
Its fixed `Path(__file__).parents[1]` lookup points under the task in a portable
runtime, causing required task_tests preflight to fail before execution.
The patch replaces only source/canonical-data loading with the public
`reviewer_support` helpers, preserving all five tests and their assertions.
This proposal must be reviewed by the maintainer; it is not applied by this
return. `checks/fixture-proposal/` contains an independently runnable migrated
copy and the separate test result. Passing it does not make the unchanged
required task_tests stage pass.
