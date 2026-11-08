"""
S-expression parser for the ARC REPL.

Adapted from rack/core. Tokenizes and parses S-expressions into nested
Python lists of Symbol, int, str, bool, and list values.

Additions over rack: {k v} dict literals, [[row] [row]] grid literals.
"""


class Symbol:
    """Interned symbol — identity comparison."""
    __slots__ = ('name',)
    _interned = {}

    def __new__(cls, name):
        if name in cls._interned:
            return cls._interned[name]
        obj = super().__new__(cls)
        obj.name = name
        cls._interned[name] = obj
        return obj

    def __repr__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self is other or (isinstance(other, Symbol) and self.name == other.name)


class StrLit:
    """String literal (distinct from Symbol)."""
    __slots__ = ('value',)

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f'"{self.value}"'

    def __eq__(self, other):
        return isinstance(other, StrLit) and self.value == other.value


def tokenize(text):
    """Break text into tokens."""
    tokens = []
    i = 0
    n = len(text)

    while i < n:
        c = text[i]

        # Whitespace
        if c in ' \t\n\r':
            i += 1

        # Comments
        elif c == ';':
            while i < n and text[i] != '\n':
                i += 1

        # Parens and brackets
        elif c in '()[]{}':
            tokens.append(c)
            i += 1

        # String literal
        elif c == '"':
            j = i + 1
            s = []
            while j < n and text[j] != '"':
                if text[j] == '\\' and j + 1 < n:
                    j += 1
                    if text[j] == 'n':
                        s.append('\n')
                    elif text[j] == 't':
                        s.append('\t')
                    else:
                        s.append(text[j])
                else:
                    s.append(text[j])
                j += 1
            if j >= n:
                raise SyntaxError("Unterminated string literal")
            tokens.append(StrLit(''.join(s)))
            i = j + 1

        # Quote shorthand
        elif c == "'":
            tokens.append("'")
            i += 1

        # Atom (symbol, number, bool, keyword)
        else:
            j = i
            while j < n and text[j] not in ' \t\n\r()[]{}";':
                j += 1
            atom = text[i:j]
            i = j

            # Booleans
            if atom == '#t':
                tokens.append(True)
            elif atom == '#f':
                tokens.append(False)
            # Numbers
            elif _is_int(atom):
                tokens.append(int(atom))
            elif _is_float(atom):
                tokens.append(float(atom))
            # Keyword args (#:key)
            elif atom.startswith('#:'):
                tokens.append(atom)
            else:
                tokens.append(Symbol(atom))

    return tokens


def _is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def _is_float(s):
    try:
        float(s)
        return '.' in s
    except ValueError:
        return False


# Bound recursion so a pathologically deep candidate fails as a clean
# SyntaxError instead of leaking Python's RecursionError (which crashed the
# solver worker on malformed model output). The deepest real grounded program
# nests 33 levels; 400 gives >10x headroom while staying well under the
# interpreter's ~1000-frame recursion limit.
_MAX_PARSE_DEPTH = 400


def parse_tokens(tokens, pos=0, depth=0):
    """Recursive descent parser. Returns (value, next_pos)."""
    if depth > _MAX_PARSE_DEPTH:
        raise SyntaxError("expression nesting exceeds the parser depth limit")
    if pos >= len(tokens):
        raise SyntaxError("Unexpected end of expression")

    tok = tokens[pos]

    if tok in (')', ']', '}'):
        raise SyntaxError(f"Unexpected {tok}")

    # Quote
    if tok == "'":
        val, pos = parse_tokens(tokens, pos + 1, depth + 1)
        return [Symbol('quote'), val], pos

    # List
    if tok == '(':
        lst = []
        pos += 1
        while pos < len(tokens) and tokens[pos] != ')':
            val, pos = parse_tokens(tokens, pos, depth + 1)
            lst.append(val)
        if pos >= len(tokens):
            raise SyntaxError("Missing )")
        return lst, pos + 1

    # Grid/row literal [...]
    if tok == '[':
        lst = []
        pos += 1
        while pos < len(tokens) and tokens[pos] != ']':
            val, pos = parse_tokens(tokens, pos, depth + 1)
            lst.append(val)
        if pos >= len(tokens):
            raise SyntaxError("Missing ]")
        return lst, pos + 1

    # Dict literal {k v k v}
    if tok == '{':
        pairs = []
        pos += 1
        while pos < len(tokens) and tokens[pos] != '}':
            val, pos = parse_tokens(tokens, pos, depth + 1)
            pairs.append(val)
        if pos >= len(tokens):
            raise SyntaxError("Missing }")
        # Convert to dict
        if len(pairs) % 2 != 0:
            raise SyntaxError("Dict literal needs even number of elements")
        return dict(zip(pairs[0::2], pairs[1::2])), pos + 1

    # Atom (already converted by tokenizer)
    return tok, pos + 1


def parse(text):
    """Parse a single S-expression from text."""
    tokens = tokenize(text)
    if not tokens:
        return None
    val, pos = parse_tokens(tokens, 0)
    if pos != len(tokens):
        raise SyntaxError("Unexpected trailing tokens after expression")
    return val


def parse_all(text):
    """Parse all S-expressions from text."""
    tokens = tokenize(text)
    results = []
    pos = 0
    while pos < len(tokens):
        val, pos = parse_tokens(tokens, pos)
        results.append(val)
    return results
