# 07eaf5f238ad object-choice parametric family

This task-local prototype keeps the exact canonical program as the default
`object_choice=first` setting and adds `object_choice=last`. Both settings see
identical deterministic inputs. Each input has three or four distinct header
colours and one or two row-major body components per colour; at least one colour
has two visibly different crops. The selected crops are packed in header order.

The first two demonstrations deliberately cross square/rectangular, even/odd
width, three/four header colours, first/last duplicate position, and
first-component-larger/smaller conditions. `audit.py` checks 14 finite rival
rules across both settings, seeds 0 and 17, and 2/3/6 demonstrations. Native
qualification remains the protected-Racket authority for labels.
