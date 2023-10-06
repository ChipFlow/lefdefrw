
from .lefdefschema import _def_parse_schema

class ArrayIter:
    def __init__(self, items, n=None):
        self.items = items
        self.i = 0
        if isinstance(n, int) and n > 0:
            assert(n == len(items))
        else:
            n = len(items)
        self.n = n

    def next_value(self, move=True):
        n = self.n
        if self.i >= self.n:
            return None
        v = self.items[self.i]
        if move:
            self.i += 1
        assert(v is not None)
        return v

def writeDEF(filename, st):
    fout = open(filename, "wt")
    line = []
    wr_ptr = []
    def _save_ptr():
        wr_ptr.append(len(line))
    def _restore_ptr():
        i = wr_ptr.pop()
        del line[i:]
    def _move_ptr():
        wr_ptr.pop()
    stack = []
    svs = []
    def _save_stack():
        st = [len(stack), None]
        if isinstance(stack[-1], ArrayIter):
            st[1] = stack[-1].i
        svs.append(st)
    def _restore_stack():
        st = svs.pop()
        del stack[st[0]:]
        if st[1] is not None:
            assert(isinstance(stack[-1], ArrayIter))
            stack[-1].i = st[1]
    def _value(move=True):
        v = stack[-1]
        if isinstance(v, ArrayIter):
            v = v.next_value(move)
        return v
    def _flush():
        if line:
            start = True
            for item in line:
                if not item.isspace() and not start:
                    fout.write(" ")
                fout.write(item)
                start = (item == '\n')
            line.clear()
    def _write(s):
        line.append(s)
    def _check_args(obj, args):
        for name, val in args.items():
            if name not in obj:
                return False
            if obj[name] != val:
                return False
        return True
    def _update_element(el):
        if isinstance(el, str):
            el = _def_parse_schema[el]
        return el
    def _check_element(el, top=True):
        if top:
            _save_stack()
        el = _update_element(el)
        ok = False
        if el[0] == "STRUCT":
            v = stack[-1]
            ok = isinstance(v, dict)
            if ok:
                ok = _check_element(el[1], False)
            elif isinstance(v, ArrayIter):
                v = v.next_value(False)
                if v is None:
                    ok = False
                else:
                    stack.append(v)
                    ok = _check_element(el[1], False)
                    stack.pop()
        elif el[0] == "OPT":
            if el[-1] and _check_args(_value(False), el[-1]):
                ok = True
            else:
                ok = _check_element(el[1])
        elif el[0] == "SEQ":
            if el[-1]:
                v = _value(False)
                if v is None:
                    ok = False
                else:
                    ok = _check_args(v, el[-1])
            else:
                ok = True
                for item in el[1]:
                    item = _update_element(item)
                    if not isinstance(item, tuple):
                        continue
                    if item[0] in {"OPT", "KEY"}:
                        continue
                    if not _check_element(item):
                        ok = False
                        break
        elif el[0] == "CHOICE":
            ok = False
            for item in el[1]:
                if _check_element(item):
                    ok = True
                    break
        elif el[0] == "VAR":
            v = _value(False)
            ok = isinstance(v, dict)
            if ok:
                ok = el[-1] in v
        elif el[0] == "KEY":
            v = _value(False)
            if el[-1] is not None:
                ok = el[-1] == v
            else:
                ok = True
        elif el[0] == "NSEQ":
            for item in el[1]:
                if not _check_element(item):
                    return False
            return True
        elif el[0] == "REPEAT":
            ok = True
        elif el[0] == "EOL":
            ok = True
        else:
            assert(False), el
        if top:
            _restore_stack()
        return ok

    def _write_element(el):
        _save_ptr()
        if __write_element(el):
            _move_ptr()
            return True
        _restore_ptr()
        return False
    def __write_element(el):
        if el == str:
            item = _value()
            if item is None:
                return False
            assert(isinstance(item, str))
            _write(item)
            return True
        if el == int:
            item = _value()
            if item is None:
                return False
            assert(isinstance(item, int))
            _write(str(item))
            return True
        el = _update_element(el)
        if el[0] == "KEY":
            _write(el[1])
            return True
        if el[0] == "SEQ":
            for item in el[1]:
                if not _write_element(item):
                    return False
            return True
        if el[0] == "CHOICE":
            #_check_choice(el[1])
            choices = []
            for item in el[1]:
                if _check_element(item):
                    choices.append(item)
            if not choices:
                return False
            assert(len(choices) == 1), (choices, el[1])
            return _write_element(choices[0])
        if el[0] == "VAR":
            obj = stack[-1]
            if not isinstance(obj, dict):
                return False
            assert(el[-1] in obj), (el[-1], obj)
            stack.append(obj[el[-1]])
            ok = _write_element(el[1])
            stack.pop()
            return ok
        if el[0] == "STRUCT":
            v = stack[-1]
            if isinstance(v, ArrayIter):
                v = _value()
                if v is None:
                    ok = False
                else:
                    stack.append(v)
                    ok = _write_element(el[1])
                    stack.pop()
            else:
                ok = _write_element(el[1])
            return ok
        if el[0] == "NSEQ":
            for item in el[1]:
                if not _write_element(item):
                    return False
            return True
        if el[0] == "ARRAY":
            arr = stack[-1]
            if isinstance(arr, ArrayIter):
                arr = arr.next_value()
                if arr is None:
                    return False
            assert(isinstance(arr, (list, tuple))), arr
            stack.append(ArrayIter(arr, el[-1]))
            while _write_element(el[1]):
                pass
            stack.pop()
            return True
        elif el[0] == "OPT":
            if _check_element(el[1]):
                return _write_element(el[1])
            return True
        elif el[0] == "REPEAT":
            while _write_element(el[1]):
                pass
            return True
        elif el[0] == "NOTNEXT":
            return True
        elif el[0] == "EOL":
            _write("\n")
            if len(stack) < 2:
                _flush()
            return True
        assert(False), el
    stack.append(st)
    if not _write_element("FILE"):
        return False
    _flush()
    fout.flush()
    fout.close()
    return True
