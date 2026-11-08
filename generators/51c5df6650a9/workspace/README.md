# Workspace tools for 51c5df6650a9

`reference_probe.py` is a portable, independent Python mirror of the selected
legend/crop/pack behavior. It loads canonical pairs through `reviewer_support`
and exposes two explicit rival rules:

- `fixed_columns_rival`: read only legend columns 0, 2 and 4. This fits all five
  canonical pairs and is the strongest retained canonical shortcut.
- `body_scan_order_rival`: ignore the legend and pack body components in reading
  order.

The selected regression suite is `../tests/test_generator.py`. Both files run in
the source checkout and in the isolated task-test snapshot prepared by
`arcpuzzles check --stage task_tests`.
