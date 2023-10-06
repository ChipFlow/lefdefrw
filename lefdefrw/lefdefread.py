import re
import os

from .lefdefschema import _def_parse_schema

class TokenReader:
    def __init__(self, it):
        self.it = it
        self.buf = []
        self.pos = 0
        self.stack = []

    def token(self):
        if self.pos < len(self.buf):
            tok = self.buf[self.pos]
            self.pos += 1
        else:
            tok = next(self.it)
            if self.stack:
                self.buf.append(tok)
            else:
                self.buf.clear()
            self.pos = len(self.buf)
        return tok

    def save_ptr(self):
        self.stack.append(self.pos)

    def restore_ptr(self):
        self.pos = self.stack.pop()

    def move_ptr(self):
        self.stack.pop()
        if not self.stack:
            del self.buf[:self.pos]
            self.pos = 0

_re_space = re.compile("\s+")

def readDEF(filename):
    i_line = 0
    def _tokens():
        nonlocal i_line
#        cmd = []
        with open(filename, "rt") as f:
            for line in f:
                i_line += 1
                for part in _re_space.split(line.strip()):
                    if part.startswith('#'):
                        break
                    yield part
    toks = TokenReader(_tokens())
    stack = []
    def _next_item():
        return toks.token()
    st = {}
    stack.append(st)
    def _push_value(v):
        if stack and isinstance(stack[-1], list):
            _stack = stack[-1]
        else:
            _stack = stack
        _stack.append(v)
    def _set_args(args):
        i = 0
        while True:
            i -= 1
            if isinstance(stack[i], dict):
                stack[i].update(args)
                break
    def _set_arg(name, val):
        i = 0
        while True:
            i -= 1
            if isinstance(stack[i], dict):
                stack[i][name] = val
                break
    def _parse_keyword(word, val):
        v = _next_item()
        if v != word:
            return False
        if val is not None:
            _push_value(val)
        return True
    def _parse_str():
        v = _next_item()
        if v in ";+-\"()":
            return False
        _push_value(v)
        return True
    def _parse_int():
        v = _next_item()
        try:
            v = int(v)
        except:
            return False
        _push_value(int(v))
        return True
    def _parsed_ok(item):
        toks.save_ptr()
        if _parse_element(item):
            toks.move_ptr()
            return True
        toks.restore_ptr()
        return False
    def _parse_choice(items):
        for item in items:
            if _parsed_ok(item):
                return True
        return False
    def _parse_sequence(items, args):
        for i, item in enumerate(items):
            if not _parse_element(item):
                return False
        _set_args(args)
        return True
    def _update_element(el):
        if isinstance(el, str):
            return _def_parse_schema[el]
        return el
    def _parse_element(el):
        if el == str:
            return _parse_str()
        if el == int:
            return _parse_int()
        el = _update_element(el)
        if el[0] == "KEY":
            return _parse_keyword(*el[1:])
        if el[0] == "OPT":
            if _parsed_ok(el[1]):
                _set_args(el[-1])
            return True
        if el[0] == "CHOICE":
            if _parse_choice(el[1]):
                return True
            return False
        if el[0] == "SEQ":
            return _parse_sequence(el[1], el[-1])
        if el[0] == "NSEQ":
            idx = set(range(len(el[1])))
            while True:
                found = False
                for i in idx:
                    item = _update_element(el[1][i])
                    if item[0] == "OPT":
                        ok = _parsed_ok(item[1])
                        if ok:
                            _set_args(item[-1])
                    else:
                        ok = _parsed_ok(item)
                    if ok:
                        found = True
                        idx.discard(i)
                        break
                if not found:
                    break
            if not idx:
                return True
            ok = all(map(lambda i: _update_element(el[1][i])[0] == "OPT", idx))
            return ok
        if el[0] == "STRUCT":
            i = len(stack)
            stack.append({})
            if not _parse_element(el[1]):
                del stack[i:]
                return False
            arr = stack.pop()
            assert(i == len(stack)), st
            _push_value(arr)
            return True
        if el[0] == "REPEAT":
            while _parsed_ok(el[1]):
                pass
            return True
        if el[0] == "ARRAY":
            i_stack = len(stack)
            stack.append([])
            i = 0
            n = el[-1]
            toks.save_ptr()
            while _parsed_ok(el[1]):
                i += 1
                if n is not None and i == n:
                    break
            ok = n is None or i == n or (n == "NonEmpty" and i > 0)
            if ok:
                arr = stack.pop()
                assert(i_stack == len(stack))
                _push_value(arr)
                toks.move_ptr()
            else:
                del stack[i_stack:]
                toks.restore_ptr()
            return ok
        if el[0] == "VAR":
            i = len(stack)
            stack.append(el[-1])
            if _parse_element(el[1]):
                v = stack.pop()
            else:
                del stack[i:]
                return False
            name = stack.pop()
            assert(i == len(stack)), name
            _set_arg(name, v)
            return True
        if el[0] == "NOTNEXT":
            toks.save_ptr()
            ok = not _parse_element(el[1])
            toks.restore_ptr()
            return ok
        if el[0] == "EOL":
            return True
        assert(False)
    if not _parse_element("FILE"):
        assert(False)
    return st
