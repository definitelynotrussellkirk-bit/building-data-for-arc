"""Convert main.tex to the Kaggle markdown: python3 latex2md.py main.tex ../building-data-for-arc.md figures (after latexmk)."""
import re
import sys
from pathlib import Path

TEX = Path(sys.argv[1])
AUX = TEX.with_suffix('.aux')
OUT = Path(sys.argv[2])
FIGDIR = sys.argv[3] if len(sys.argv) > 3 else 'figures'

src = TEX.read_text()
labels = {}
for m in re.finditer(r'\\newlabel\{([^}]*)\}\{\{([^}]*)\}', AUX.read_text()):
    labels[m.group(1)] = m.group(2)


def strip_comments(t):
    return '\n'.join(re.sub(r'(?<!\\)%.*$', '', line) if not line.lstrip().startswith('%') else '' for line in t.split('\n'))


def arg(t, i):
    """Return (content, end) of the balanced {...} group starting at t[i] == '{'."""
    assert t[i] == '{', t[i:i + 40]
    depth, j = 0, i
    while j < len(t):
        c = t[j]
        if c == '\\':
            j += 2
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return t[i + 1:j], j + 1
        j += 1
    raise ValueError('unbalanced')


def replace_cmd(t, name, fn, nargs=1, opt=False):
    out, i, pat = [], 0, '\\' + name
    while True:
        k = t.find(pat, i)
        if k < 0:
            out.append(t[i:])
            return ''.join(out)
        after = k + len(pat)
        if after < len(t) and (t[after].isalpha()):
            out.append(t[i:after]); i = after
            continue
        j = after
        optval = None
        if opt and j < len(t) and t[j] == '[':
            e = t.index(']', j); optval = t[j + 1:e]; j = e + 1
        while j < len(t) and t[j] in ' \n' and nargs:
            j += 1
        args = []
        for _ in range(nargs):
            if j >= len(t) or t[j] != '{':
                break
            a, j = arg(t, j)
            args.append(a)
        if len(args) < nargs:
            out.append(t[i:after]); i = after
            continue
        out.append(t[i:k])
        out.append(fn(*args) if not opt else fn(optval, *args))
        i = j


cites = {}
for n, m in enumerate(re.finditer(r'\\bibitem\{([^}]*)\}', src), 1):
    cites[m.group(1)] = n


def code_text(x):
    x = x.replace('\\_', '_').replace('\\textasciitilde', '~').replace('{}', '').replace('\\{', '{').replace('\\}', '}')
    x = x.replace('\\&', '&').replace('\\%', '%').replace('\\#', '#').replace('\\allowbreak', '').replace('\\$', '$')
    x = x.replace('\\textbackslash', '\\')
    return x


def inline(t):
    t = replace_cmd(t, 'todo', lambda x: f'**TODO:** {x}')
    t = replace_cmd(t, 'gen', lambda x: f'`{code_text(x)}`')
    t = replace_cmd(t, 'texttt', lambda x: f'`{code_text(x)}`')
    t = replace_cmd(t, 'url', lambda x: f'<{x}>')
    t = replace_cmd(t, 'href', lambda u, x: f'[{x}]({u})', nargs=2)
    t = replace_cmd(t, 'emph', lambda x: f'*{x}*')
    t = replace_cmd(t, 'textit', lambda x: f'*{x}*')
    t = replace_cmd(t, 'textbf', lambda x: f'**{x}**')
    t = replace_cmd(t, 'cite', lambda x: '[' + ', '.join(str(cites.get(k.strip(), k)) for k in x.split(',')) + ']')
    t = replace_cmd(t, 'ref', lambda x: labels.get(x, x))
    t = replace_cmd(t, 'label', lambda x: '')
    t = replace_cmd(t, 'setlength', lambda a, b: '', nargs=2)
    t = replace_cmd(t, 'color', lambda x: '')
    for c in ('centering', 'small', 'footnotesize', 'noindent', 'raggedright', 'allowbreak', 'arraybackslash',
              'normalsize', 'medskip', 'smallskip', 'bigskip', 'clearpage', 'newpage'):
        t = re.sub(r'\\' + c + r'(?![a-zA-Z])\s*', '', t)
    t = t.replace('\\textdegree{}', '°').replace('\\textdegree', '°')
    t = t.replace('\\textasciitilde', '~')
    # protect math
    parts = re.split(r'((?<!\\)\$[^$]+?(?<!\\)\$)', t)
    for i, p in enumerate(parts):
        if p.startswith('$'):
            continue
        p = p.replace('---', '—').replace('--', '–').replace('``', '“').replace("''", '”')
        p = p.replace('\\%', '%').replace('\\&', '&').replace('\\_', '_').replace('\\#', '#')
        p = p.replace('\\dots', '…').replace('\\ldots', '…')
        p = re.sub(r'(?<!\\)~', ' ', p)
        p = p.replace('\\\\', ' ')
        p = re.sub(r'\\ ', ' ', p)
        parts[i] = p
    return ''.join(parts)


def table_rows(body):
    body = re.sub(r'\\(toprule|midrule|bottomrule|hline|addlinespace|endhead|endfirsthead|endfoot|endlastfoot)(\[[^]]*\])?', '', body)
    body = re.sub(r'\\cmidrule(\([^)]*\))?\{[^}]*\}', '', body)
    rows = []
    for r in re.split(r'(?<!\\)\\\\', body):
        r = r.strip()
        if not r:
            continue
        cells = [inline(c.strip()).replace('\n', ' ').replace('|', '\\|') for c in re.split(r'(?<!\\)&', r)]
        cells = [re.sub(r'\s+', ' ', c).strip() for c in cells]
        rows.append(cells)
    # drop repeated header rows (xltabular)
    if rows:
        head = rows[0]
        rows = [head] + [r for r in rows[1:] if r != head]
    return rows


def md_table(rows):
    if not rows:
        return ''
    n = max(len(r) for r in rows)
    rows = [r + [''] * (n - len(r)) for r in rows]
    out = ['| ' + ' | '.join(rows[0]) + ' |', '|' + '@@SEP@@|' * n]
    out += ['| ' + ' | '.join(r) + ' |' for r in rows[1:]]
    return '\n'.join(out)


def find_tabular(t):
    m = re.search(r'\\begin\{(tabularx|xltabular|tabular)\}', t)
    if not m:
        return None
    env = m.group(1)
    j = m.end()
    if env in ('tabularx', 'xltabular'):
        _, j = arg(t, j)
    while j < len(t) and t[j] in ' \n':
        j += 1
    if t[j] == '[':
        j = t.index(']', j) + 1
    _, j = arg(t, j)
    e = t.index('\\end{' + env + '}', j)
    return t[m.start():m.start()], t[j:e], m.start(), e + len('\\end{' + env + '}')


counters = {'figure': 0, 'table': 0}


def convert_float(env, body):
    counters[env] += 1
    n = counters[env]
    cap = ''
    k = body.find('\\caption')
    if k >= 0:
        c, e = arg(body, body.index('{', k))
        cap = inline(re.sub(r'\s+', ' ', c)).strip()
        body = body[:k] + body[e:]
    if env == 'figure':
        imgs = []
        for m in re.finditer(r'\\includegraphics(\[[^]]*\])?\{([^}]*)\}', body):
            f = m.group(2)
            if f.endswith('.pdf'):
                f = f[:-4] + '.png'
            imgs.append(f'![Figure {n}]({FIGDIR}/{f})')
        return '\n\n'.join(imgs) + f'\n\n*Figure {n}: {cap}*\n'
    tb = find_tabular(body)
    rows = table_rows(tb[1]) if tb else []
    return '\n' + md_table(rows) + (f'\n\n*Table {n}: {cap}*\n' if cap else '\n')


def lists(t):
    def conv(env, body):
        items = re.split(r'\\item\b', body)[1:]
        out = []
        for i, it in enumerate(items, 1):
            it = it.strip()
            lab = ''
            if it.startswith('['):
                e = it.index(']'); lab = it[1:e]; it = it[e + 1:].strip()
            text = re.sub(r'\s*\n\s*', ' ', inline(it)).strip()
            if env == 'description' or lab:
                out.append(f'- **{inline(lab)}** {text}')
            elif env == 'enumerate':
                out.append(f'{i}. {text}')
            else:
                out.append(f'- {text}')
        return '\n'.join(out) + '\n'
    pat = re.compile(r'\\begin\{(itemize|enumerate|description)\}(\[[^]]*\])?(.*?)\\end\{\1\}', re.S)
    while True:
        m = pat.search(t)
        if not m:
            return t
        t = t[:m.start()] + '\n' + conv(m.group(1), m.group(3)) + '\n' + t[m.end():]


def main():
    t = strip_comments(src)
    title = arg(t, t.index('{', t.index('\\title')))[0]
    body = t[t.index('\\begin{document}') + len('\\begin{document}'):t.index('\\end{document}')]
    body = body.replace('\\maketitle', '')
    body = re.sub(r'\{\\(footnotesize|small)\s*\n(\\begin\{xltabular\}.*?\\end\{xltabular\})\}', r'\2', body, flags=re.S)
    # bibliography
    bib = ''
    bm = re.search(r'\\begin\{thebibliography\}\{[^}]*\}(.*?)\\end\{thebibliography\}', body, re.S)
    if bm:
        entries = re.split(r'\\bibitem\{[^}]*\}', bm.group(1))[1:]
        bib = '\n## References\n\n' + '\n'.join(f'{i}. {re.sub(r"\s+", " ", inline(e)).strip()}' for i, e in enumerate(entries, 1)) + '\n'
        body = body[:bm.start()] + '@@BIB@@' + body[bm.end():]
    # abstract
    body = re.sub(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', lambda m: '\n## Abstract\n\n' + m.group(1).strip() + '\n', body, flags=re.S)
    # code listings
    def lst(m):
        opt = m.group(1) or ''
        lang = re.search(r'language=(\w+)', opt)
        return f'\n```{lang.group(1).lower() if lang else ""}\n{m.group(2).strip(chr(10))}\n```\n'
    blocks = []
    def stash(m):
        blocks.append(lst(m)); return f'@@CODE{len(blocks) - 1}@@'
    body = re.sub(r'\\begin\{lstlisting\}(\[[^]]*\])?\n?(.*?)\\end\{lstlisting\}', stash, body, flags=re.S)
    # floats
    def fl(m):
        return '\n' + convert_float(m.group(1), m.group(3)) + '\n'
    body = re.sub(r'\\begin\{(figure|table)\}(\[[^]]*\])?(.*?)\\end\{\1\}', fl, body, flags=re.S)
    # bare tabulars inside center/minipage or standalone
    body = re.sub(r'\\begin\{(center|minipage)\}(\{[^}]*\})?', '', body)
    body = re.sub(r'\\end\{(center|minipage)\}', '', body)
    while True:
        tb = find_tabular(body)
        if not tb:
            break
        body = body[:tb[2]] + '\n\n' + md_table(table_rows(tb[1])) + '\n\n' + body[tb[3]:]
    # quotes
    body = re.sub(r'\\begin\{quote\}(.*?)\\end\{quote\}',
                  lambda m: '\n' + '\n'.join('> ' + l for l in re.sub(r'\s*\n\s*', ' ', inline(m.group(1))).strip().split('\n')) + '\n',
                  body, flags=re.S)
    body = lists(body)
    # display math
    maths = []

    def dstash(m):
        maths.append('\n$$' + re.sub(r'\s+', ' ', m.group(1)).strip() + '$$\n')
        return f'@@MATH{len(maths) - 1}@@'
    body = re.sub(r'\\\[(.*?)\\\]', dstash, body, flags=re.S)
    # sections
    appendix = False
    def sec(level):
        def f(x):
            return f'@@SEC{level}@@{x}@@'
        return f
    body = body.replace('\\appendix', '@@APPENDIX@@')
    body = replace_cmd(body, 'section', sec(2))
    body = replace_cmd(body, 'subsection', sec(3))
    body = replace_cmd(body, 'paragraph', lambda x: f'@@PARA@@{x}@@')
    body = inline(body)
    # number sections from aux order
    sec_labels = [v for k, v in labels.items()]
    out_lines, s_num, a_num, sub = [], 0, 0, 0
    pieces = re.split(r'(@@SEC\d@@.*?@@|@@APPENDIX@@|@@PARA@@.*?@@)', body)
    res = []
    for p in pieces:
        if p == '@@APPENDIX@@':
            appendix = True
            res.append('\n# Appendices\n')
            continue
        m = re.match(r'@@SEC(\d)@@(.*?)@@', p)
        if m:
            lvl, name = int(m.group(1)), m.group(2)
            if lvl == 2:
                sub = 0
                if appendix:
                    a_num += 1; num = chr(64 + a_num)
                else:
                    s_num += 1; num = str(s_num)
                cur = num
                res.append(f'\n## {num} {name}\n\n')
            else:
                sub += 1
                res.append(f'\n### {cur}.{sub} {name}\n\n')
            continue
        m = re.match(r'@@PARA@@(.*?)@@', p)
        if m:
            res.append(f'**{m.group(1).strip()}** ')
            continue
        res.append(p)
    body = ''.join(res)
    for i, b in enumerate(blocks):
        body = body.replace(f'@@CODE{i}@@', b)
    for i, b in enumerate(maths):
        body = body.replace(f'@@MATH{i}@@', b)
    body = body.replace('@@BIB@@', bib)
    # paragraphs: join wrapped lines, keep blank lines, tables, lists, code, quotes, headings
    lines = body.split('\n')
    out, buf, in_code = [], [], False
    def flush():
        if buf:
            out.append(' '.join(x.strip() for x in buf).strip())
            buf.clear()
    for l in lines:
        if l.startswith('```'):
            flush(); out.append(l); in_code = not in_code; continue
        if in_code:
            out.append(l); continue
        s = l.strip()
        if not s:
            flush(); out.append(''); continue
        if s.startswith(('|', '- ', '> ', '#', '![', '*Figure', '*Table', '$$')) or re.match(r'\d+\. ', s):
            flush(); out.append(s); continue
        buf.append(s)
    flush()
    md = '\n'.join(out)
    md = md.replace('@@SEP@@', '---')
    md = re.sub(r'\n{3,}', '\n\n', md).strip() + '\n'
    md = f'# {" ".join(inline(title).split())}\n\n' + md
    OUT.write_text(md)
    left = sorted(set(re.findall(r'\\[a-zA-Z]+', re.sub(r'```.*?```', '', re.sub(r'\$[^$]*\$', '', md), flags=re.S))))
    print('written', OUT, len(md.split()), 'words; leftover commands outside math/code:', left[:40])


main()
