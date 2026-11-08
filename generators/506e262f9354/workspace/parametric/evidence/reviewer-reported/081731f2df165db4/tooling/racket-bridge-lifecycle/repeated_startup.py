import time
from arc_repl.racket_bridge import RacketBridge
for i in range(1, 9):
    print('start', i, flush=True)
    t=time.monotonic()
    with RacketBridge() as b:
        print('ready', i, round(time.monotonic()-t,3), b.eval_text('(+ 1 2)'), flush=True)
    print('closed', i, round(time.monotonic()-t,3), flush=True)
print('done', flush=True)
