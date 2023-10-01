import os
import re

def generate_test_def(filename, **params):
    units = int(params.get("units", 1000))
    width = int(params.get("width", 200) * units)
    height = int(params.get("height", 200) * units)
    def _lines():
        yield 'VERSION 5.8 ;'
        yield 'DIVIDERCHAR "/" ;'
        yield 'BUSBITCHARS "[]" ;'
        yield 'DESIGN test_project ;'
        yield f'UNITS DISTANCE MICRONS {units} ;'
        yield f'DIEAREA ( 0 0 ) ( {width} {height} ) ;'
        # rows
        yield 'ROW ROW_0 unithd 5520 10880 FS DO 6323 BY 1 STEP 460 0 ;'
        # tracks
        yield 'TRACKS X 170 DO 8588 STEP 340 LAYER met1 ;'
        yield 'VIAS 1 ;'
        yield '    - via4_3100x3100 + VIARULE M4M5_PR + CUTSIZE 800 800  + LAYERS met4 via4 met5  + CUTSPACING 800 800  + ENCLOSURE 350 350 350 350  + ROWCOL 2 2  ;'
        yield 'END VIAS'
        yield 'COMPONENTS 0 ;'
        yield 'END COMPONENTS'
        yield 'PINS 1 ;'
        yield '    - io_in[0] + NET io_in[0] + DIRECTION INPUT + USE SIGNAL + PLACED ( 2921200 32980 ) N + LAYER met3 ( -3600 -600 ) ( 3600 600 ) ;'
        yield 'END PINS'
        yield 'BLOCKAGES 5 ;'
        yield '    - LAYER met1 RECT ( 0 0 ) ( 0 0 ) ;'
        yield '    - LAYER met2 RECT ( 0 0 ) ( 0 0 ) ;'
        yield '    - LAYER met3 RECT ( 0 0 ) ( 0 0 ) ;'
        yield '    - LAYER met4 RECT ( 0 0 ) ( 0 0 ) ;'
        yield '    - LAYER met5 RECT ( 0 0 ) ( 0 0 ) ;'
        yield 'END BLOCKAGES'
        yield 'SPECIALNETS 1 ;'
        yield '    - vccd1 ( PIN vccd1 ) + USE POWER'
        yield '      + ROUTED met4 0 + SHAPE STRIPE ( 2928100 3522800 ) via4_3100x3100'
        yield '      NEW met4 0 + SHAPE STRIPE ( 2890520 3522800 ) via4_3100x3100 ;'
        yield 'END SPECIALNETS'
        yield 'NETS 0 ;'
        yield 'END NETS'
        yield 'END DESIGN'

    with open(filename, "wt") as f:
        for line in _lines():
            f.write(line)
            f.write("\n")

#generate_test_def("test.def",width=3000,height=3000)

re_space = re.compile("\s+")

def _KEY(word, val=None):
    return ("KEY", word, val)

def _SEQ(*items, **args):
    return ("SEQ", items, args)

def _STRUCT(item):
    return ("STRUCT", item)

def _CHOICE(*items):
    return ("CHOICE", items)

def _OPT(item, **args):
    return ("OPT", item, args)

def _REPEAT(item):
    return ("REPEAT", item)

def _ARRAY(item, num=None):
    return ("ARRAY", item, num)

def _VAR(item, name):
    return ("VAR", item, name)

_END_CMD = _KEY(";")

_def_parse_schema = {
    "FILE": _SEQ(_VAR(_STRUCT("HDR"), "Hdr"), _VAR(_STRUCT("DESIGN"), "Design")),
    "HDR": _REPEAT(_CHOICE("VERSION_CMD", "DIVIDERCHAR_CMD", "BUSBITCHARS_CMD")),
    "VERSION_CMD": _SEQ(_KEY("VERSION"), _VAR(str, "Version"), _END_CMD),
    "DIVIDERCHAR_CMD": _SEQ(_KEY("DIVIDERCHAR"), _VAR(str, "Divider"), _END_CMD),
    "BUSBITCHARS_CMD": _SEQ(_KEY("BUSBITCHARS"), _VAR(str, "BusBitsChars"), _END_CMD),
    "DESIGN": _SEQ("DESIGN_CMD", "DESIGN_INFO", _VAR(_ARRAY("DESIGN_ITEM"),"Items"), "ENDDESIGN_CMD"),
    "DESIGN_CMD": _SEQ(_KEY("DESIGN"), _VAR(str, "Name"), _END_CMD),
    "ENDDESIGN_CMD": _SEQ(_KEY("END"), _KEY("DESIGN"), _END_CMD),
    "DESIGN_ITEM": _CHOICE("ROW_CMD", "TRACKS_CMD", "VIAS", "COMPONENTS", "PINS", "BLOCKAGES", "SPECNETS", "NETS"),
    "DESIGN_INFO": _REPEAT(_CHOICE("UNITS_CMD", "DIEAREA_CMD")),
    "UNITS_CMD": _SEQ(_KEY("UNITS"), _KEY("DISTANCE"), _KEY("MICRONS"), _VAR(int, "Dbu"), _END_CMD),
    "DIEAREA_CMD": _SEQ(_KEY("DIEAREA"), _VAR(_ARRAY("XY"), "DieArea"), _END_CMD),
    "XY": _SEQ(_KEY('('), _ARRAY(int, 2), _KEY(')')),
    "ORIENT": _CHOICE(_KEY("N", "North"),
                      _KEY("S", "South"),
                      _KEY("E", "East"),
                      _KEY("W", "West"),
                      _KEY("FN", "FlipNorth"),
                      _KEY("FS", "FlipSouth"),
                      _KEY("FE", "FlipEast"),
                      _KEY("FW", "FlipWest")),
    "ROW_CMD": _STRUCT(_SEQ(_KEY("ROW"), _VAR(str, "Name"), _VAR(str, "Site"),
                       _VAR(_ARRAY(int, 2), "Origin"), _VAR("ORIENT", "Orient"),
                       _OPT(_SEQ(_KEY("DO"), _VAR(int, "NX"), _KEY("BY"), _VAR(int, "NY"),
                       _OPT(_SEQ(_KEY("STEP"), _VAR(int, "DX"), _VAR(int, "DY"))))), _END_CMD, Type="Row")),
    "TRACKS_CMD": _STRUCT(_SEQ(_KEY("TRACKS"), _CHOICE("HTRACKS", "VTRACKS"), _END_CMD)),
    "HTRACKS": _SEQ(_KEY("X"), _VAR(int, "X"),
                    _KEY("DO"), _VAR(int, "Number"), _KEY("STEP"), _VAR(int, "DX"),
                    _OPT("TRACKMASK"), _OPT("LAYER"),
                    Type="Tracks", Direction="Vertical", Y=0),
    "VTRACKS": _SEQ(_KEY("Y"), _VAR(int, "Y"),
                    _KEY("DO"), _VAR(int, "Number"), _KEY("STEP"), _VAR(int, "DX"),
                    _OPT("TRACKMASK"), _OPT("LAYER"),
                    Type="Tracks", Direction="Vertical", Y=0),
    "TRACKMASK": _SEQ(_KEY("MASK"), _VAR(int, "MaskNum"), _OPT(_KEY("SAMEMASK"), SameMask=True)),
    "LAYER": _SEQ(_KEY("LAYER"), _VAR(_ARRAY(str), "Layers")),
    "VIAS": _STRUCT(_SEQ("VIAS_CMD", _VAR(_ARRAY("VIA_CMD"), "Items"), "ENDVIAS_CMD", Type="Vias")),
    "VIAS_CMD": _SEQ(_KEY("VIAS"), _VAR(int, "Number"), _END_CMD),
    "VIA_CMD": _STRUCT(_SEQ(_KEY("-"), _VAR(str, "Name"),
                            _CHOICE("VIARULE",
                                    _VAR(_ARRAY(_CHOICE("RECT","POLYGON")), "Shapes")), _END_CMD)),
    "ENDVIAS_CMD": _SEQ(_KEY("END"), _KEY("VIAS")),
    "VIARULE": _SEQ(_KEY("+"), _KEY("VIARULE"), _VAR(str, "Rule"),
                    _KEY("+"), _KEY("CUTSIZE"), _VAR(_ARRAY(int, 2), "CutSize"),
                    _KEY("+"), _KEY("LAYERS"), _VAR(_ARRAY(str, 3), "Layers"),
                    _KEY("+"), _KEY("CUTSPACING"), _VAR(_ARRAY(int, 2), "CutSpacing"),
                    _KEY("+"), _KEY("ENCLOSURE"), _VAR(_ARRAY(_ARRAY(int, 2), 2), "Enclosure"),
                    _OPT(_SEQ(_KEY("+"), _KEY("ROWCOL"), _VAR(_ARRAY(int, 2), "NumCuts"))),
                    _OPT(_SEQ(_KEY("+"), _KEY("ORIGIN"), _VAR(_ARRAY(int, 2), "Origin"))),
                    _OPT(_SEQ(_KEY("+"), _KEY("OFFSET"), _VAR(_ARRAY(_ARRAY(int, 2), 2), "Offset"))),
                    _OPT(_SEQ(_KEY("+"), _KEY("PATTERN"), _VAR(str, "Pattern")))),
    "RECT": _STRUCT(_SEQ(_KEY("+"), _KEY("RECT"), _VAR(str, "Layer"),
                         _OPT(_SEQ(_KEY("+"),"MASKNUM")),
                         _VAR(_ARRAY("XY", 2), "Points"), Type="Rect")),
    "MASKNUM": _SEQ(_KEY("MASK"), _VAR(int, "MaskNum")),
    "POLYGON": _STRUCT(_SEQ(_KEY("+"), _KEY("POLYGON"), _VAR(str, "Layer"),
                       _OPT(_SEQ(_KEY("+"),"MASKNUM")),
                       _VAR(_ARRAY("XY"), "Points"), Type="Polygon")),
    "COMPONENTS": _STRUCT(_SEQ("COMPONENTS_CMD", _VAR(_ARRAY("COMPONENT_CMD"), "Items"),
                               "ENDCOMPONENTS_CMD", Type="Components")),
    "COMPONENTS_CMD": _SEQ(_KEY("COMPONENTS"), _VAR(int, "Number"), _END_CMD),
    "ENDCOMPONENTS_CMD": _SEQ(_KEY("END"), _KEY("COMPONENTS")),
    "COMPONENT_CMD": _STRUCT(_SEQ(_KEY("-"), _VAR(str, "Name"), _END_CMD)),
    "PINS": _STRUCT(_SEQ("PINS_CMD", _VAR(_ARRAY("PIN_CMD"), "Items"), "ENDPINS_CMD", Type="Pins")),
    "PINS_CMD": _SEQ(_KEY("PINS"), _VAR(int, "Number"), _END_CMD),
    "ENDPINS_CMD": _SEQ(_KEY("END"), _KEY("PINS")),
    "PIN_CMD": _STRUCT(_SEQ(_KEY("-"), _VAR(str, "Name"), _KEY("+"), _KEY("NET"), _VAR(str, "Net"),
                            _OPT(_SEQ(_KEY("+"), _KEY("SPECIAL")), Special=True),
                            _OPT(_SEQ(_KEY("+"), _KEY("DIRECTION"),
                                      _VAR(_CHOICE(_KEY("INPUT", "Input"),
                                                   _KEY("OUTPUT", "Output"),
                                                   _KEY("INOUT", "InOut"),
                                                   _KEY("FEEDTHRU", "FeedThrough"),
                                                  ), "Direction"))),
                            _OPT(_SEQ(_KEY("+"), _KEY("NETEXPR"), _VAR(str, "NetExpr"))),
                            _OPT(_SEQ(_KEY("+"), _KEY("SUPPLYSENSITIVITY"), _VAR(str, "PowerPin"))),
                            _OPT(_SEQ(_KEY("+"), _KEY("GROUNDSENSITIVITY"), _VAR(str, "GroundPin"))),
                            _OPT("USE"),
                            _OPT(_VAR(_ARRAY(_STRUCT(_CHOICE(
                                            _SEQ(_KEY("+"), _KEY("PORT"), Type="Port"),
                                            _SEQ(_KEY("+"), _KEY("LAYER"),_VAR(str, "Layer"),
                                                 _OPT("MASKNUM"),
                                                 _OPT(_SEQ(_KEY("SPACING"), _VAR(int, "MinSpacing"))),
                                                 _OPT(_SEQ(_KEY("DESIGNRULEWIDTH"), _VAR(int, "EffectiveWidth"))),
                                                 _VAR(_ARRAY("XY", 2), "Points"),
                                                 Type="Rect"),
                                            _SEQ(_KEY("+"), _KEY("POLYGON"),_VAR(str, "Layer"),
                                                 _OPT("MASKNUM"),
                                                 _OPT(_SEQ(_KEY("SPACING"), _VAR(int, "MinSpacing"))),
                                                 _OPT(_SEQ(_KEY("DESIGNRULEWIDTH"), _VAR(int, "EffectiveWidth"))),
                                                 _VAR(_ARRAY("XY"), "Points"),
                                                 Type="Polygon"),
                                            _SEQ(_KEY("+"), _KEY("VIA"),_VAR(str, "Name"),
                                                 _OPT("MASKNUM"),
                                                 _VAR("XY", "Point"),
                                                 Type="Via"),
                                            _SEQ(_KEY("+"), _VAR(_CHOICE(_KEY("COVER", "Cover"),
                                                                         _KEY("FIXED", "Fixed"),
                                                                         _KEY("PLACED", "Placed")),
                                                                 "Type"),
                                                 _VAR("XY", "Point"), _VAR("ORIENT", "Orient"),
                                                 Type="Placement"),
                                                    ))),
                                      "Items")),
                            _END_CMD)),
    "USE": _SEQ(_KEY("+"), _KEY("USE"),
                _VAR(_CHOICE(_KEY("SIGNAL", "Signal"),
                             _KEY("POWER", "Power"),
                             _KEY("GROUND", "Ground"),
                             _KEY("CLOCK", "Clock"),
                             _KEY("TIEOFF", "TieOff"),
                             _KEY("ANALOG", "Analog"),
                             _KEY("SCAN", "Scan"),
                             _KEY("RESET", "Reset"),
                            ), "Use")),
    "BLOCKAGES": _STRUCT(_SEQ("BLOCKAGES_CMD",
                              _VAR(_ARRAY(_CHOICE("BLOCKAGE_LAYER_CMD","BLOCKAGE_PLACEMENT_CMD")), "Items"),
                               "ENDBLOCKAGES_CMD", Type="Blockages")),
    "BLOCKAGES_CMD": _SEQ(_KEY("BLOCKAGES"), _VAR(int, "Number"), _END_CMD),
    "ENDBLOCKAGES_CMD": _SEQ(_KEY("END"), _KEY("BLOCKAGES")),
    "BLOCKAGE_LAYER_CMD": _STRUCT(_SEQ(_KEY("-"), _KEY("LAYER"), _VAR(str, "Layer"),
                                       _REPEAT(_SEQ(_KEY("+", _CHOICE(
                                                            _VAR(_KEY("SLOTS", True), "Slots"),
                                                            _VAR(_KEY("FILLS", True), "Fills"),
                                                            _VAR(_KEY("PUSHDOWN", True), "PushDown"),
                                                            _VAR(_KEY("EXCEPTPGNET", True), "ExceptPowerGround"),
                                                            _SEQ(_KEY("COMPONENT"), _VAR(str, "Component")),
                                                            _SEQ(_KEY("SPACING"), _VAR(int, "MinSpacing")),
                                                            _SEQ(_KEY("DESIGNRULEWIDTH"), _VAR(int, "EffectiveWidth")),
                                                            "MASKNUM",
                                                            )))
                                          ), _VAR(_ARRAY(_STRUCT(_CHOICE(
                                                     _SEQ(_KEY("RECT"), _VAR(_ARRAY("XY", 2), "Points"), Type="Rect"),
                                                     _SEQ(_KEY("POLYGON"), _VAR(_ARRAY("XY"), "Points"), Type="Polygon")
                                                                ))), "Items"), _END_CMD)),
    "BLOCKAGE_PLACEMENT_CMD": _STRUCT(_SEQ(_KEY("-"), _KEY("PLACEMENT"),
                                           _REPEAT(_SEQ(_KEY("+", _CHOICE(
                                                            _VAR(_KEY("SOFT", True), "Soft"),
                                                            _SEQ(_KEY("PARTIAL"), _VAR(str, "MaxDensity")),
                                                            _VAR(_KEY("PUSHDOWN", True), "PushDown"),
                                                            _SEQ(_KEY("COMPONENT"), _VAR(str, "Component")),
                                                            )))
                                                   ), _VAR(_ARRAY(_STRUCT(_CHOICE(
                                                     _SEQ(_KEY("RECT"), _VAR(_ARRAY("XY", 2), "Points"), Type="Rect"),
                                                     #_SEQ(_KEY("POLYGON"), _VAR(_ARRAY("XY"), "Points"), Type="Polygon")
                                                                ))), "Items"), _END_CMD)),
    "SPECNETS": _STRUCT(_SEQ("SPECNETS_CMD", _VAR(_ARRAY("SPECNET_CMD"), "Items"),
                             "ENDSPECNETS_CMD", Type="SpecNet")),
    "SPECNETS_CMD": _SEQ(_KEY("SPECIALNETS"), _VAR(int, "Number"), _END_CMD),
    "ENDSPECNETS_CMD": _SEQ(_KEY("END"), _KEY("SPECIALNETS")),
    "SPECNET_CMD": _STRUCT(_SEQ(_KEY("-"), _VAR(str, "Name"),
                                _VAR(_ARRAY(_STRUCT(_SEQ(
                                       _KEY("("), _CHOICE(_KEY("PIN"), _VAR(str, "Component")),
                                                  _VAR(str, "Pin"),
                                                  _OPT(_VAR(_KEY("SYNTHESIZED", True), "Synthesized")),
                                       _KEY(")")
                                       ))), "Pins"),
                                _REPEAT("SPECNETPARAM"),
                                _OPT(_VAR(_ARRAY("SPECWIRE"), "Wires")),
                                _REPEAT("SPECNETPARAM"),
                                _VAR(_ARRAY(_SEQ(_KEY("+"), _KEY("PROPERTY"),
                                                 _REPEAT(_SEQ(_VAR(str, "Name"), _VAR(str, "Value"))))), "Properties"),
                               _KEY(";"))),
    "SPECNETPARAM": _CHOICE(_SEQ(_KEY("+"), _KEY("VOLTAGE"), _VAR(str, "Voltage")),
                            _SEQ(_KEY("+"), _KEY("SOURCE"),
                                        _VAR(_CHOICE(_KEY("DIST", "Dist"),
                                                     _KEY("NETLIST", "NetList"),
                                                     _KEY("TIMING", "Timing"),
                                                     _KEY("USER", "User")), "Source")),
                            _SEQ(_KEY("+"), _VAR(_KEY("FIXEDBUMP", True), "FixedBump")),
                            _SEQ(_KEY("+"), _KEY("ORIGINAL"), _VAR(str, "Net")),
                            "USE",
                            _SEQ(_KEY("+"), _KEY("PATTERN"),
                                        _VAR(_CHOICE(_KEY("BALANCED", "Balanced"),
                                                     _KEY("STEINER", "Steiner"),
                                                     _KEY("TRUNK", "Trunk"),
                                                     _KEY("WIREDLOGIC", "WiredLogic")), "Pattern")),
                            _SEQ(_KEY("+"), _KEY("ESTCAP"), _VAR(str, "WireCapacitance")),
                            _SEQ(_KEY("+"), _KEY("WEIGHT"), _VAR(str, "Weight")),
                            ),
    "SPECWIRE": _STRUCT(_SEQ(_CHOICE(
                                _SEQ(_KEY("+"), _VAR(_KEY("COVER", True), "Cover")),
                                _SEQ(_KEY("+"), _VAR(_KEY("FIXED", True), "Fixed")),
                                _SEQ(_KEY("+"), _VAR(_KEY("ROUTED", True), "Routed")),
                                _SEQ(_KEY("+"), _KEY("SHIELD"), _VAR(str, "ShieldNet")),
                                ),
                             _CHOICE("SPECWIRE_SHAPES", "SPECWIRE_ROUTES"),
                            )),
    "SPECWIRE_SHAPES": _SEQ(_REPEAT(_CHOICE(_SEQ(_KEY("+"), _KEY("SHAPE"), _VAR(str, "ShapeType")),
                                            _SEQ(_KEY("+"), _KEY("MASK"), _VAR(int, "MaskNum")))),
                            _VAR(_ARRAY(_STRUCT(_CHOICE(
                                        _SEQ(_KEY("+"), _KEY("POLYGON"), _VAR(_ARRAY("XY"), "Points"), Type="Polygon"),
                                        _SEQ(_KEY("+"), _KEY("RECT"), _VAR(_ARRAY("XY",2), "Points"), Type="Rect"),
                                        _SEQ(_KEY("+"), _KEY("VIA"), _VAR(str, "Name"),
                                             _OPT(_VAR("ORIENT", "Orient")), _VAR(_ARRAY("XY"), "Points"), Type="Via"),
                                        )), "NonEmpty"), "Items")
                           ), 
    "SPECWIRE_ROUTES": _VAR(_ARRAY(_SEQ("SPECWIRE_ROUTE",
                                       _REPEAT(_SEQ(_KEY("NEW"), "SPECWIRE_ROUTE")))), "Routes"),
    "SPECWIRE_ROUTE": _STRUCT(_SEQ(_VAR(str, "Layer"), _VAR(int, "Width"),
                                   _OPT(_SEQ(_KEY("+"), _KEY("SHAPE"),
                                             _VAR(_CHOICE(_KEY("RING", "Ring"),
                                                          _KEY("PADRING", "PadRing"),
                                                          _KEY("BLOCKRING", "BlockRing"),
                                                          _KEY("STRIPE", "Stripe"),
                                                          _KEY("FOLLOWPIN", "FollowPin"),
                                                          _KEY("IOWIRE", "IOWire"),
                                                          _KEY("COREWIRE", "CoreWire"),
                                                          _KEY("BLOCKWIRE", "BlockWire"),
                                                          _KEY("BLOCKAGEWIRE", "BlockageWire"),
                                                          _KEY("FILLWIRE", "FillWire"),
                                                          _KEY("FILLWIREOPC", "FillWireOPC"),
                                                          _KEY("DRCFILL", "DRCFill"),
                                                          ), "Shape"))),
                                   _OPT(_SEQ(_KEY("+"), _KEY("STYLE"), _VAR(int, "StyleNum"))),
                                   _VAR(_ARRAY(_SEQ(_STRUCT(_SEQ("ROUTE_POINT", _OPT("ROUTE_TO_VIA"))),
                                            _REPEAT(_STRUCT(
                                                    _CHOICE(_SEQ("ROUTE_TO_POINT", "ROUTE_TO_VIA"), "ROUTE_TO_POINT")))
                                                    ), "NonEmpty"), "Items")
                                 )),
    "ROUTE_POINT": _SEQ(_KEY("("), _VAR(int, "X"), _VAR(int, "Y"),
                        _OPT(_VAR(int, "ExtValue")), _KEY(")"), Start=True, Type="Point"),
    "ROUTE_TO_POINT": _SEQ(_OPT("MASKNUM"),"ROUTE_POINT", Start=False),
    "ROUTE_TO_VIA": _SEQ(_OPT("MASKNUM"), _VAR(str, "ViaName"), _OPT("ORIENT"),
                        _OPT(_SEQ(_KEY("DO"), _VAR(int, "NX"), _KEY("BY"), _VAR(int, "NY"),
                                  _SEQ(_KEY("STEP"), _VAR(int, "DX"), _VAR(int, "DY")))), Type="Via"),
    "NETS": _STRUCT(_SEQ("NETS_CMD", _VAR(_ARRAY("NET_CMD"), "Items"), "ENDNETS_CMD", Type="Nets")),
    "NETS_CMD": _SEQ(_KEY("NETS"), _VAR(int, "Number"), _END_CMD),
    "ENDNETS_CMD": _SEQ(_KEY("END"), _KEY("NETS")),
    "NET_CMD": _STRUCT(_SEQ(_KEY("-"))),
}

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

def parseDEF(filename):
    i_line = 0
    def _tokens():
        nonlocal i_line
#        cmd = []
        with open(filename, "rt") as f:
            for line in f:
                i_line += 1
                for part in re_space.split(line.strip()):
                    if part.startswith('#'):
                        break
                    yield part
                    # if part != ';':
                    #     cmd.append(part)
                    # if part == ';' or (len(cmd)>1 and cmd[-2].upper() == "END"):
                    #     yield cmd
                    #     cmd.clear()
#        if cmd:
#            yield cmd
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
    def _parse_opt(item):
        _parsed_ok(item)
        return True
    def _parse_choice(items):
        for item in items:
            if _parsed_ok(item):
                print("Choiced", item)
                return True
        return False
    def _parse_sequence(items, args):
        for i, item in enumerate(items):
            if not _parse_element(item):
                return False
        _set_args(args)
        return True
    def _parse_element(el):
        if el == str:
            return _parse_str()
        if el == int:
            return _parse_int()
        if isinstance(el, str):
            if el not in _def_parse_schema:
                print(stack, cmd)
            if not _parse_element(_def_parse_schema[el]):
                print(el, "failed")
                return False
            return True
        if el[0] == "KEY":
            return _parse_keyword(*el[1:])
        if el[0] == "OPT":
            if _parsed_ok(el[1]):
                _set_args(el[-1])
            return True
        if el[0] == "CHOICE":
            if _parse_choice(el[1]):
                return True
            print("Choice failed:", el)
            return False
        if el[0] == "SEQ":
            return _parse_sequence(el[1], el[-1])
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
            #print("Start:", el, cmd, pos)
            i = len(stack)
            stack.append(el[-1])
            if _parse_element(el[1]):
                v = stack.pop()
            else:
                del stack[i:]
                #print("Var failed:", el, cmd, pos)
                return False
            name = stack.pop()
            assert(i == len(stack)), name
            _set_arg(name, v)
            print(name, "=", v)
            return True
        assert(False)
    if not _parse_element("FILE"):
        print(st)
        print("Failed at line", i_line)
        assert(False)
    return st

parseDEF("/home/serge/ChipFlow/projects/chipflow-backend/chipflow_backend/pdksetup/efables/sky130/user_project_wrapper.def")
