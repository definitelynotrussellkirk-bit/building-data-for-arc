from reviewer_support import canonical_pairs, find_root, load_selected_generator
import hashlib, json
ROOT=find_root(__file__)
for task in ('3079e46d051f','08b346c559d6'):
    gen, src, sha=load_selected_generator(task, root=ROOT)
    pairs=canonical_pairs(task, root=ROOT, labeled_only=True)
    print('====',task,sha,'pairs',len(pairs),'====')
    for i,p in enumerate(pairs):
        inp=p['input']; out=p['output']
        colors=sorted({v for row in inp for v in row})
        print('PAIR',i,'in',len(inp),len(inp[0]),'out',len(out),len(out[0]),'colors',colors)
        print('INPUT',json.dumps(inp,separators=(',',':')))
        print('OUTPUT',json.dumps(out,separators=(',',':')))
        try: print('SELF',gen.self_check(inp))
        except Exception as e: print('SELF_EXC',repr(e))
