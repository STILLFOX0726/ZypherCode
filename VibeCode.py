#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║            VibeCode   —  VibeCode                        ║
║   A programming language that speaks fluent Gen Z. No cap.              ║
║                                                                          ║
║   Phases: Lexical Analysis  →  Syntax Analysis  →  Semantic Analysis   ║
╚══════════════════════════════════════════════════════════════════════════╝

  VibeCode  —  QUICK REFERENCE
  ┌──────────────────┬──────────────────────────────────────────────────┐
  │  numfr           │  Numeric data type  (int / float)                │
  │  texting         │  String data type   (text value)                 │
  │  vibe            │  Boolean data type  (slay / flop)                │
  │  hits            │  Assignment operator  (like = )                  │
  │  periodt         │  End-of-statement delimiter  (like ; )           │
  │  spill           │  Output keyword  (like print)                    │
  │  lowkey          │  If-keyword                                       │
  │  ngl             │  Else-keyword                                     │
  │  highkey         │  While-loop keyword                               │
  │  era             │  Block-open  (like { )                           │
  │  done            │  Block-close  (like } )                          │
  │  slaps           │  Comparison ==                                    │
  │  ghosted         │  Comparison !=                                    │
  │  glowing         │  Comparison  >                                    │
  │  cringe          │  Comparison  <                                    │
  │  slay            │  Boolean true                                     │
  │  flop            │  Boolean false                                    │
  │  // ...          │  Single-line comment                              │
  └──────────────────┴──────────────────────────────────────────────────┘
"""

import re

# ═══════════════════════════════════════════════════════════════════
#  TERMINAL COLORS
# ═══════════════════════════════════════════════════════════════════
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
PINK   = "\033[95m"
BLUE   = "\033[94m"
ORANGE = "\033[38;5;214m"
WHITE  = "\033[97m"

# ═══════════════════════════════════════════════════════════════════
#  LANGUAGE SPECIFICATION
# ═══════════════════════════════════════════════════════════════════

KEYWORDS = {
    "numfr":    "DATATYPE",
    "texting":  "DATATYPE",
    "vibe":     "DATATYPE",
    "spill":    "OUTPUT_KW",
    "lowkey":   "IF_KW",
    "ngl":      "ELSE_KW",
    "highkey":  "WHILE_KW",
    "era":      "BLOCK_OPEN",
    "done":     "BLOCK_CLOSE",
    "slay":     "BOOL_LITERAL",
    "flop":     "BOOL_LITERAL",
}

ASSIGN_OP = "hits"
DELIMITER = "periodt"

COMPARISONS = {
    "slaps":   "EQ",
    "ghosted": "NEQ",
    "glowing": "GT",
    "cringe":  "LT",
}

ARITH_OPS = {'+', '-', '*', '/'}

# ═══════════════════════════════════════════════════════════════════
#  PRETTY PRINT HELPERS
# ═══════════════════════════════════════════════════════════════════

def phase_header(title):
    bar = "─" * 62
    print(f"\n{BOLD}{CYAN}{bar}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{bar}{RESET}")

def divider():
    print(f"  {CYAN}{'·' * 58}{RESET}")

def lexer_log(token, ttype):
    labels = {
        "DATATYPE":        f"{PINK}DATATYPE {RESET}",
        "IDENTIFIER":      f"{WHITE}IDENTIFIER {RESET}",
        "ASSIGN_OP":       f"{ORANGE}ASSIGN_OP {RESET}",
        "NUMERIC_LITERAL": f"{GREEN}NUMERIC_LITERAL {RESET}",
        "STRING_LITERAL":  f"{YELLOW}STRING_LITERAL {RESET}",
        "BOOL_LITERAL":    f"{PINK}BOOL_LITERAL {RESET}",
        "DELIMITER":       f"{CYAN}DELIMITER {RESET}",
        "OUTPUT_KW":       f"{GREEN}OUTPUT_KW {RESET}",
        "IF_KW":           f"{BLUE}IF_KW {RESET}",
        "ELSE_KW":         f"{BLUE}ELSE_KW {RESET}",
        "WHILE_KW":        f"{BLUE}WHILE_KW {RESET}",
        "BLOCK_OPEN":      f"{ORANGE}BLOCK_OPEN {RESET}",
        "BLOCK_CLOSE":     f"{ORANGE}BLOCK_CLOSE {RESET}",
        "COMPARISON":      f"{PINK}COMPARISON {RESET}",
        "ARITH_OP":        f"{YELLOW}ARITH_OP {RESET}",
        "LPAREN":          f"{WHITE}LPAREN{RESET}",
        "RPAREN":          f"{WHITE}RPAREN{RESET}",
    }
    label = labels.get(ttype, f"{WHITE}{ttype}{RESET}")
    print(f"  {PINK}[LEXER]{RESET}   Found {BOLD}{token!r:<20}{RESET} ->  {label}")

def ok(msg):   print(f"  {GREEN}OK  {msg}{RESET}")
def err(msg):  print(f"  {RED}ERR  {BOLD}{msg}{RESET}")
def warn(msg): print(f"  {YELLOW}WARN  {msg}{RESET}")
def info(tag, msg, color=PINK):
    print(f"  {color}[{tag}]{RESET}  {msg}")

# ═══════════════════════════════════════════════════════════════════
#  TOKEN
# ═══════════════════════════════════════════════════════════════════

class Token:
    def __init__(self, ttype, value, pos):
        self.ttype = ttype
        self.value = value
        self.pos   = pos
    def __repr__(self):
        return f"Token({self.ttype}, {self.value!r})"

# ═══════════════════════════════════════════════════════════════════
#  PHASE 1 — LEXER
# ═══════════════════════════════════════════════════════════════════

def tokenize(source: str) -> list:
    phase_header("PHASE 1 — LEXICAL ANALYSIS  (The Lexer)")
    info("LEXER", f"Source received: {source!r}")
    divider()

    tokens  = []
    unknown = []

    # Strip single-line comments  //  ...
    s = re.sub(r'//[^\n]*', '', source).strip()
    if s != source.strip():
        info("LEXER", "Comment stripped before tokenization")

    pos = 0
    while pos < len(s):
        if s[pos].isspace():
            pos += 1
            continue

        matched = False

        # ── Assignment keyword "hits" ──────────────────────────
        if s[pos:pos+4] == "hits":
            end = pos + 4
            if end >= len(s) or (not s[end].isalnum() and s[end] != '_'):
                tok = Token("ASSIGN_OP", "hits", pos)
                tokens.append(tok)
                lexer_log("hits", "ASSIGN_OP")
                pos += 4
                matched = True

        # ── Delimiter "periodt" ────────────────────────────────
        if not matched and s[pos:pos+7] == "periodt":
            end = pos + 7
            if end >= len(s) or (not s[end].isalnum() and s[end] != '_'):
                tok = Token("DELIMITER", "periodt", pos)
                tokens.append(tok)
                lexer_log("periodt", "DELIMITER")
                pos += 7
                matched = True

        # ── Comparison keywords ────────────────────────────────
        if not matched:
            for comp in COMPARISONS:
                if s[pos:pos+len(comp)] == comp:
                    end = pos + len(comp)
                    if end >= len(s) or (not s[end].isalnum() and s[end] != '_'):
                        tok = Token("COMPARISON", comp, pos)
                        tokens.append(tok)
                        lexer_log(comp, "COMPARISON")
                        pos += len(comp)
                        matched = True
                        break

        if not matched:
            # ── String literal ─────────────────────────────────
            if s[pos] == '"':
                end = s.find('"', pos + 1)
                if end == -1:
                    warn(f"Bestie, unclosed string at pos {pos}. That's giving unfinished era (Panic Mode: skipping)")
                    unknown.append(s[pos:])
                    pos = len(s)
                else:
                    val = s[pos:end+1]
                    tok = Token("STRING_LITERAL", val, pos)
                    tokens.append(tok)
                    lexer_log(val, "STRING_LITERAL")
                    pos = end + 1
                matched = True

            # ── Numeric literal ─────────────────────────────────
            elif s[pos].isdigit() or (s[pos] == '-' and pos+1 < len(s) and s[pos+1].isdigit()):
                m = re.match(r'-?\d+(\.\d+)?', s[pos:])
                if m:
                    val = m.group()
                    tok = Token("NUMERIC_LITERAL", val, pos)
                    tokens.append(tok)
                    lexer_log(val, "NUMERIC_LITERAL")
                    pos += len(val)
                    matched = True

            # ── Arithmetic operators ─────────────────────────────
            elif s[pos] in ARITH_OPS:
                tok = Token("ARITH_OP", s[pos], pos)
                tokens.append(tok)
                lexer_log(s[pos], "ARITH_OP")
                pos += 1
                matched = True

            # ── Parentheses ─────────────────────────────────────
            elif s[pos] == '(':
                tokens.append(Token("LPAREN", '(', pos))
                lexer_log('(', "LPAREN")
                pos += 1
                matched = True
            elif s[pos] == ')':
                tokens.append(Token("RPAREN", ')', pos))
                lexer_log(')', "RPAREN")
                pos += 1
                matched = True

            # ── Keywords / Identifiers ───────────────────────────
            elif s[pos].isalpha() or s[pos] == '_':
                m = re.match(r'[A-Za-z_]\w*', s[pos:])
                if m:
                    val = m.group()
                    ttype = KEYWORDS.get(val, "IDENTIFIER")
                    tokens.append(Token(ttype, val, pos))
                    lexer_log(val, ttype)
                    pos += len(val)
                    matched = True

            # ── Unknown ─────────────────────────────────────────
            if not matched:
                ch = s[pos]
                unknown.append(ch)
                warn(f"Unknown token {ch!r} at pos {pos} — not it chief  (Panic Mode Recovery: skipping)")
                pos += 1

    divider()
    if unknown:
        warn(f"Lexical Analysis: caught {len(unknown)} sus token(s): {unknown}")
        warn("Panic Mode Recovery was applied — unknown tokens were skipped")
    else:
        ok("Lexical Analysis COMPLETE. 0 Unknown Tokens. Slay!")

    return tokens


# ═══════════════════════════════════════════════════════════════════
#  PHASE 2 — PARSER
# ═══════════════════════════════════════════════════════════════════

class ParseError(Exception):
    pass


def parse(tokens: list) -> list:
    phase_header("PHASE 2 — SYNTAX ANALYSIS  (The Parser)")
    info("PARSER", f"Examining {len(tokens)} token(s). The plot thickens... ", BLUE)
    divider()

    if not tokens:
        err("No tokens to parse bestie. That's an empty era.")
        return []

    idx = 0

    def peek(offset=0):
        i = idx + offset
        return tokens[i] if i < len(tokens) else None

    def consume(expected_type=None):
        nonlocal idx
        tok = peek()
        if tok is None:
            raise ParseError(f"Ran out of tokens — expected {expected_type} but got nothing. GHOSTED.")
        if expected_type and tok.ttype != expected_type:
            raise ParseError(
                f"Expected {expected_type} but found {tok.ttype} ({tok.value!r}) at pos {tok.pos}. Not it."
            )
        idx += 1
        return tok

    def parse_expr():
        left = peek()
        if left is None:
            raise ParseError("Expected expression but got nothing.")
        if left.ttype in ("NUMERIC_LITERAL", "STRING_LITERAL", "BOOL_LITERAL", "IDENTIFIER"):
            consume()
            while peek() and peek().ttype == "ARITH_OP":
                op_tok = consume("ARITH_OP")
                right  = consume()
                if right.ttype not in ("NUMERIC_LITERAL", "IDENTIFIER"):
                    raise ParseError(f"Expected numeric operand after '{op_tok.value}', not {right.ttype}")
                info("PARSER", f"  Arithmetic sub-expression: {left.value} {op_tok.value} {right.value}", BLUE)
                left = right
            return left
        elif left.ttype == "LPAREN":
            consume("LPAREN")
            inner = parse_expr()
            consume("RPAREN")
            return inner
        else:
            raise ParseError(f"Expression: got {left.ttype} ({left.value!r}). That's giving confusion.")

    def parse_condition():
        left = parse_expr()
        if peek() and peek().ttype == "COMPARISON":
            op    = consume("COMPARISON")
            right = parse_expr()
            info("PARSER", f"  Condition: {left.value} {op.value} {right.value}", BLUE)
            return (left, op, right)
        elif left.ttype == "BOOL_LITERAL":
            info("PARSER", f"  Boolean condition: {left.value}", BLUE)
            return (left, None, None)
        else:
            raise ParseError("Condition must use: slaps, ghosted, glowing, or cringe. No cap.")

    def parse_block():
        consume("BLOCK_OPEN")
        stmts = []
        while peek() and peek().ttype != "BLOCK_CLOSE":
            stmts.append(parse_statement())
        consume("BLOCK_CLOSE")
        return stmts

    def parse_statement():
        first = peek()
        if first is None:
            raise ParseError("Expected a statement but got nothing.")

        if first.ttype == "DATATYPE":
            info("PARSER", "Trying rule: [DATATYPE] [IDENTIFIER] [hits] [EXPR] [periodt]", BLUE)
            dtype  = consume("DATATYPE")
            ident  = consume("IDENTIFIER")
            assign = consume("ASSIGN_OP")
            expr   = parse_expr()
            delim  = consume("DELIMITER")
            info("PARSER", f"Rule SLAY OK  ->  {dtype.value} {ident.value} hits {expr.value} periodt", BLUE)
            return {"kind": "DECLARATION", "dtype": dtype, "ident": ident, "expr": expr}

        elif first.ttype == "OUTPUT_KW":
            info("PARSER", "Trying rule: [spill] [EXPR] [periodt]", BLUE)
            kw    = consume("OUTPUT_KW")
            expr  = parse_expr()
            delim = consume("DELIMITER")
            info("PARSER", f"Rule SLAY OK  ->  spill {expr.value} periodt", BLUE)
            return {"kind": "OUTPUT", "expr": expr}

        elif first.ttype == "IF_KW":
            info("PARSER", "Trying rule: lowkey [COND] era STMTS done  [ngl era STMTS done]", BLUE)
            consume("IF_KW")
            cond      = parse_condition()
            then_body = parse_block()
            else_body = []
            if peek() and peek().ttype == "ELSE_KW":
                consume("ELSE_KW")
                else_body = parse_block()
            info("PARSER", "lowkey/ngl (if/else) rule SLAY OK", BLUE)
            return {"kind": "IF", "cond": cond, "then": then_body, "else": else_body}

        elif first.ttype == "WHILE_KW":
            info("PARSER", "Trying rule: highkey [COND] era STMTS done", BLUE)
            consume("WHILE_KW")
            cond = parse_condition()
            body = parse_block()
            info("PARSER", "highkey (while) rule SLAY OK", BLUE)
            return {"kind": "WHILE", "cond": cond, "body": body}

        else:
            raise ParseError(f"Statement starts with {first.ttype} ({first.value!r}). Giving confusion.")

    ast     = []
    had_err = False
    while idx < len(tokens):
        try:
            stmt = parse_statement()
            ast.append(stmt)
        except ParseError as e:
            warn(f"Syntax Error: {e}")
            warn("Phrase-Level Recovery: scanning for next 'periodt'... ")
            found = False
            while idx < len(tokens):
                if tokens[idx].ttype == "DELIMITER":
                    idx += 1
                    found = True
                    warn("Recovery complete! Resuming after 'periodt'. We move.")
                    break
                idx += 1
            if not found:
                warn("No 'periodt' found. Parsing stopped early.")
                break
            had_err = True

    divider()
    if had_err:
        warn("Syntax Analysis complete but we had some lore... (Phrase-Level Recovery applied)")
    else:
        ok("Syntax Analysis COMPLETE. Structure is immaculate.")
    return ast


# ═══════════════════════════════════════════════════════════════════
#  PHASE 3 — SEMANTIC ANALYSER
# ═══════════════════════════════════════════════════════════════════

class SemanticError(Exception):
    pass


class SymbolTable:
    def __init__(self):
        self.table = {}

    def bind(self, name, dtype, value, level=0):
        self.table[name] = {"type": dtype, "value": value, "level": level}

    def lookup(self, name):
        return self.table.get(name)

    def dump(self):
        if not self.table:
            print(f"  {YELLOW}(Symbol Table is empty — no variables were bound this era){RESET}")
            return
        w = 20
        # Group entries by scope level
        by_level = {}
        for name, e in self.table.items():
            lv = e["level"]
            by_level.setdefault(lv, []).append((name, e))

        print(f"  {BOLD}{WHITE}{'IDENTIFIER':<{w}} {'TYPE':<{w}} {'VALUE':<{w}} {'LEVEL':<8}{RESET}")
        print(f"  {CYAN}{'─'*w} {'─'*w} {'─'*w} {'─'*8}{RESET}")
        for lv in sorted(by_level):
            label = "Global (Level 0)" if lv == 0 else f"Scope Level {lv}"
            print(f"  {BOLD}{ORANGE}── {label} ──{RESET}")
            for name, e in by_level[lv]:
                print(f"  {GREEN}{name:<{w}}{RESET} {PINK}{e['type']:<{w}}{RESET} {YELLOW}{str(e['value']):<{w}}{RESET} {CYAN}{lv:<8}{RESET}")
            print(f"  {BOLD}{WHITE}  Subtotal (Level {lv}): {len(by_level[lv])} variable(s){RESET}")
        print(f"  {CYAN}{'─'*(w*3+8+6)}{RESET}")
        print(f"  {BOLD}{GREEN}GRAND TOTAL: {len(self.table)} variable(s) across {len(by_level)} level(s){RESET}")


def analyse(ast: list, sym: SymbolTable):
    phase_header("PHASE 3 — SEMANTIC ANALYSIS  (The Analyser)")
    errors = 0

    def check_expr(expr_tok, expected_dtype):
        val   = expr_tok.value
        ttype = expr_tok.ttype

        if ttype == "IDENTIFIER":
            entry = sym.lookup(val)
            if entry is None:
                raise SemanticError(f"'{val}' was never declared. That variable is a ghost.")
            info("SEMANTICS", f"  Identifier '{val}' resolved -> type={entry['type']}, value={entry['value']}")
            if expected_dtype and entry["type"] != expected_dtype:
                raise SemanticError(f"Type mismatch: '{val}' is '{entry['type']}' but expected '{expected_dtype}'. Mixed signals.")
            return entry["value"]

        elif ttype == "NUMERIC_LITERAL":
            if expected_dtype == "texting":
                raise SemanticError(f"'{val}' is a NUMBER but variable declared as 'texting' (string). Not it bestie.")
            return float(val) if '.' in val else int(val)

        elif ttype == "STRING_LITERAL":
            if expected_dtype == "numfr":
                raise SemanticError(f"'{val}' is a STRING but variable declared as 'numfr' (number). That's a MAJOR flop.")
            return val.strip('"')

        elif ttype == "BOOL_LITERAL":
            if expected_dtype == "numfr":
                raise SemanticError(f"'{val}' is a BOOLEAN but variable declared as 'numfr'. Wrong energy.")
            return val == "slay"

        return val

    def visit(stmt, depth=0):
        nonlocal errors
        kind = stmt["kind"]

        if kind == "DECLARATION":
            dtype = stmt["dtype"]
            ident = stmt["ident"]
            expr  = stmt["expr"]
            info("SEMANTICS", f"Checking type compatibility for '{ident.value}'... ")
            info("SEMANTICS", f"  Declared type  : {PINK}{dtype.value}{RESET}")
            info("SEMANTICS", f"  Assigned value : {YELLOW}{expr.value}{RESET}  (token type: {expr.ttype})")
            try:
                resolved = check_expr(expr, dtype.value)
                info("SEMANTICS", "  Types are vibing. No coercion needed.")
                info("SEMANTICS", f"Binding '{ident.value}' into Symbol Table at Level {depth}. Main character moment.")
                sym.bind(ident.value, dtype.value, resolved, level=depth)
                ok(f"'{ident.value}' successfully bound. That variable is iconic.")
            except SemanticError as se:
                err(f"SEMANTIC ERROR: {se}")
                warn("Recovery Strategy: assignment discarded to protect memory. We move.")
                errors += 1

        elif kind == "OUTPUT":
            expr = stmt["expr"]
            info("SEMANTICS", f"'spill' incoming! Resolving: {expr.value}")
            if expr.ttype == "IDENTIFIER":
                entry = sym.lookup(expr.value)
                if entry is None:
                    err(f"SEMANTIC ERROR: '{expr.value}' is undeclared. Can't spill what doesn't exist.")
                    errors += 1
                else:
                    ok(f"spill -> {BOLD}{expr.value}{RESET}{GREEN} = {entry['value']}")
            else:
                ok(f"spill -> {expr.value}")

        elif kind == "IF":
            info("SEMANTICS", "Checking 'lowkey' (if) condition... ")
            left, op, right = stmt["cond"]
            if op:
                info("SEMANTICS", f"  Condition: {left.value} {op.value} {right.value}")
            ok("Condition structure is slay.")
            info("SEMANTICS", f"Analysing 'era' (then) block at Level {depth + 1}... ")
            for s in stmt["then"]:
                visit(s, depth + 1)
            if stmt["else"]:
                info("SEMANTICS", f"Analysing 'ngl era' (else) block at Level {depth + 1}... ")
                for s in stmt["else"]:
                    visit(s, depth + 1)

        elif kind == "WHILE":
            info("SEMANTICS", "Checking 'highkey' (while) loop condition... ")
            left, op, right = stmt["cond"]
            if op:
                info("SEMANTICS", f"  Condition: {left.value} {op.value} {right.value}")
            ok("Loop condition structure is valid.")
            info("SEMANTICS", f"Analysing loop body at Level {depth + 1}...")
            for s in stmt["body"]:
                visit(s, depth + 1)

    for stmt in ast:
        visit(stmt, 0)
        divider()

    phase_header("SYMBOL TABLE  —  the main characters")
    sym.dump()

    print()
    if errors == 0:
        ok("Semantic Analysis COMPLETE. Absolutely slayin'. No errors. We eat.")
    else:
        err(f"Semantic Analysis COMPLETE with {errors} error(s). That's giving compiler trauma.")


# ═══════════════════════════════════════════════════════════════════
#  COMPILER RUNNER
# ═══════════════════════════════════════════════════════════════════

def run_compiler(source: str):
    sym = SymbolTable()
    tokens = tokenize(source)
    ast    = parse(tokens)
    analyse(ast, sym)


# ═══════════════════════════════════════════════════════════════════
#  MAIN — USER DECIDES THE INPUT
# ═══════════════════════════════════════════════════════════════════

def print_banner():
    print(f"""
{BOLD}{PINK}╔══════════════════════════════════════════════════════════════╗{RESET}
{BOLD}{PINK}║{RESET}  {BOLD}{WHITE}S L A Y . L A N G   C O M P I L E R{RESET}              {BOLD}{PINK}║{RESET}
{BOLD}{PINK}║{RESET}  {CYAN}the programming language that hits different, no cap{RESET}    {BOLD}{PINK}║{RESET}
{BOLD}{PINK}╚══════════════════════════════════════════════════════════════╝{RESET}""")


def print_reference():
    print(f"""
{BOLD}{WHITE}  NeoMind QUICK REFERENCE:{RESET}
  {CYAN}{'─'*56}{RESET}
  {PINK}DATA TYPES   {RESET}  numfr (number)  |  texting (string)  |  vibe (bool)
  {PINK}ASSIGN OP    {RESET}  hits
  {PINK}DELIMITER    {RESET}  periodt
  {PINK}OUTPUT       {RESET}  spill <value> periodt
  {PINK}IF / ELSE    {RESET}  lowkey <cond> era ... done  [ngl era ... done]
  {PINK}WHILE LOOP   {RESET}  highkey <cond> era ... done
  {PINK}BLOCK        {RESET}  era  (open)  /  done  (close)
  {PINK}COMPARISONS  {RESET}  slaps(==)  ghosted(!=)  glowing(>)  cringe(<)
  {PINK}BOOLEANS     {RESET}  slay (true)  |  flop (false)
  {PINK}COMMENTS     {RESET}  // your comment here
  {CYAN}{'─'*56}{RESET}

  {BOLD}{WHITE}EXAMPLE PROGRAMS:{RESET}

  {YELLOW}# Basic declaration + output{RESET}
  {GREEN}numfr rizz hits 100 periodt{RESET}
  {GREEN}spill rizz periodt{RESET}

  {YELLOW}# String variable{RESET}
  {GREEN}texting mood hits "absolutely thriving" periodt{RESET}
  {GREEN}spill mood periodt{RESET}

  {YELLOW}# Arithmetic{RESET}
  {GREEN}numfr clout hits 50 + 25 periodt{RESET}

  {YELLOW}# If / else  (lowkey / ngl){RESET}
  {GREEN}lowkey rizz glowing 50 era{RESET}
  {GREEN}    spill rizz periodt{RESET}
  {GREEN}done ngl era{RESET}
  {GREEN}    texting result hits "flopped" periodt{RESET}
  {GREEN}done{RESET}

  {YELLOW}# While loop  (highkey){RESET}
  {GREEN}numfr ctr hits 0 periodt{RESET}
  {GREEN}highkey ctr cringe 3 era{RESET}
  {GREEN}    spill ctr periodt{RESET}
  {GREEN}done{RESET}

  {YELLOW}# Boolean vibe type{RESET}
  {GREEN}vibe isIconic hits slay periodt{RESET}
  {GREEN}spill isIconic periodt{RESET}
  {CYAN}{'─'*56}{RESET}
  {WHITE}Tip: multi-statement programs work too — just use{RESET}
  {WHITE}periodt to end each statement as usual.{RESET}
  {CYAN}{'─'*56}{RESET}""")


def get_input() -> str:
    """
    User types their Neomind code.
    Multi-line supported — press Enter on a blank line to finish.
    Single-line also works — just press Enter once after writing.
    """
    print(f"\n  {BOLD}{WHITE}Write your Neomind code below.{RESET}")
    print(f"  {CYAN}Press Enter twice on a blank line when you're done.{RESET}")
    print(f"  {CYAN}{'─'*56}{RESET}")

    lines = []
    while True:
        try:
            line = input(f"  {PINK}>{RESET} ")
        except EOFError:
            break
        if line == "" and lines:
            break
        lines.append(line)

    return "\n".join(lines)


def main():
    print_banner()

    while True:
        print(f"\n  {BOLD}{WHITE}What do you want to do?{RESET}")
        print(f"  {CYAN}[1]{RESET}  Write and compile NeoMind code")
        print(f"  {CYAN}[2]{RESET}  View language reference + examples")
        print(f"  {CYAN}[q]{RESET}  Exit")

        choice = input(f"\n  {PINK}Enter choice:{RESET} ").strip().lower()

        if choice == 'q':
            print(f"\n  {GREEN}Compiler session ended. Stay iconic bestie.{RESET}\n")
            break

        elif choice == '2':
            print_reference()

        elif choice == '1':
            source = get_input()

            if not source.strip():
                warn("You gave me nothing bestie. That's an empty era.")
                continue

            bar = "═" * 62
            preview = source.replace('\n', ' ')[:54] + ("..." if len(source.replace('\n', ' ')) > 54 else "")
            print(f"\n{BOLD}{PINK}╔{bar}╗{RESET}")
            print(f"{BOLD}{PINK}║{RESET}  COMPILING: {preview:<54}{BOLD}{PINK}║{RESET}")
            print(f"{BOLD}{PINK}╚{bar}╝{RESET}")

            run_compiler(source)

            print(f"\n  {CYAN}{'─'*56}{RESET}")
            again = input(f"  {PINK}Compile another? [y/n]:{RESET} ").strip().lower()
            if again != 'y':
                print(f"\n  {GREEN}Compiler session ended. Stay iconic bestie.{RESET}\n")
                break

        else:
            warn("That option doesn't exist bestie. Try 1, 2, or q.")


if __name__ == "__main__":
    main()
