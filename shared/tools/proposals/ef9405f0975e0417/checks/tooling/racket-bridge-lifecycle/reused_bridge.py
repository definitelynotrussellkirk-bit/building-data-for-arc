from arc_repl.racket_bridge import RacketBridge
with RacketBridge() as bridge:
    for index in range(1, 9):
        value = bridge.eval_text(f'(+ {index} 2)')
        print('eval', index, value, flush=True)
print('done', flush=True)
