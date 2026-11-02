#!/usr/bin/env python3
"""
Flask server for slay.lang IDE
Run: python server.py  →  open http://localhost:5000
"""

import re
import os
from flask import Flask, request, jsonify, send_from_directory
from VibeCode import Token, KEYWORDS, COMPARISONS, ARITH_OPS

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'slay_ide.html')


@app.route('/compile', methods=['POST'])
def compile_endpoint():
    data   = request.get_json(silent=True) or {}
    source = data.get('source', '')
    if not source.strip():
        return jsonify({'error': 'empty source'}), 400
    result = compile_to_dict(source)
    return jsonify(result)


# ═══════════════════════════════════════════════════════════════════
#  PHASE 1 — LEXER  (structured / JSON-friendly)
# ═══════════════════════════════════════════════════════════════════

def tokenize_dict(source: str):
    logs    = []
    tokens  = []
    unknown = []

    s = re.sub(r'//[^\n]*', '', source).strip()
    if s != source.strip():
        logs.append({'type': 'lexer-info', 'msg': 'Comment stripped before tokenization 🫶'})

    pos = 0
    while pos < len(s):
        if s[pos].isspace():
            pos += 1
            continue

        matched = False

        # hits
        if s[pos:pos+4] == "hits":
            end = pos + 4
            if end >= len(s) or (not s[end].isalnum() and s[end] != '_'):
                tokens.append(Token("ASSIGN_OP", "hits", pos))
                logs.append({'type': 'token', 'value': 'hits', 'ttype': 'ASSIGN_OP'})
                pos += 4; matched = True

        # periodt
        if not matched and s[pos:pos+7] == "periodt":
            end = pos + 7
            if end >= len(s) or (not s[end].isalnum() and s[end] != '_'):
                tokens.append(Token("DELIMITER", "periodt", pos))
                logs.append({'type': 'token', 'value': 'periodt', 'ttype': 'DELIMITER'})
                pos += 7; matched = True

        # comparison keywords
        if not matched:
            for comp in COMPARISONS:
                if s[pos:pos+len(comp)] == comp:
                    end = pos + len(comp)
                    if end >= len(s) or (not s[end].isalnum() and s[end] != '_'):
                        tokens.append(Token("COMPARISON", comp, pos))
                        logs.append({'type': 'token', 'value': comp, 'ttype': 'COMPARISON'})
                        pos += len(comp); matched = True; break

        if not matched:
            if s[pos] == '"':
                end = s.find('"', pos + 1)
                if end == -1:
                    logs.append({'type': 'warn', 'msg': f"Bestie, unclosed string at pos {pos}. That's giving unfinished era 😬 (Panic Mode: skipping)"})
                    unknown.append(s[pos:])
                    pos = len(s)
                else:
                    val = s[pos:end+1]
                    tokens.append(Token("STRING_LITERAL", val, pos))
                    logs.append({'type': 'token', 'value': val, 'ttype': 'STRING_LITERAL'})
                    pos = end + 1
                matched = True

            elif s[pos].isdigit() or (s[pos] == '-' and pos+1 < len(s) and s[pos+1].isdigit()):
                m = re.match(r'-?\d+(\.\d+)?', s[pos:])
                if m:
                    val = m.group()
                    tokens.append(Token("NUMERIC_LITERAL", val, pos))
                    logs.append({'type': 'token', 'value': val, 'ttype': 'NUMERIC_LITERAL'})
                    pos += len(val); matched = True

            elif s[pos] in ARITH_OPS:
                tokens.append(Token("ARITH_OP", s[pos], pos))
                logs.append({'type': 'token', 'value': s[pos], 'ttype': 'ARITH_OP'})
                pos += 1; matched = True

            elif s[pos] == '(':
                tokens.append(Token("LPAREN", '(', pos))
                logs.append({'type': 'token', 'value': '(', 'ttype': 'LPAREN'})
                pos += 1; matched = True

            elif s[pos] == ')':
                tokens.append(Token("RPAREN", ')', pos))
                logs.append({'type': 'token', 'value': ')', 'ttype': 'RPAREN'})
                pos += 1; matched = True

            elif s[pos].isalpha() or s[pos] == '_':
                m = re.match(r'[A-Za-z_]\w*', s[pos:])
                if m:
                    val  = m.group()
                    ttype = KEYWORDS.get(val, "IDENTIFIER")
                    tokens.append(Token(ttype, val, pos))
                    logs.append({'type': 'token', 'value': val, 'ttype': ttype})
                    pos += len(val); matched = True

            if not matched:
                ch = s[pos]
                unknown.append(ch)
                logs.append({'type': 'warn', 'msg': f"Unknown token {ch!r} at pos {pos} — not it chief 💀 (Panic Mode Recovery: skipping)"})
                pos += 1

    if unknown:
        logs.append({'type': 'warn', 'msg': f"Lexical Analysis: caught {len(unknown)} sus token(s): {unknown}"})
        logs.append({'type': 'warn', 'msg': "Panic Mode Recovery was applied — unknown tokens were yeet'd 🗑️"})
    else:
        logs.append({'type': 'ok', 'msg': "Lexical Analysis COMPLETE. 0 Unknown Tokens. Slay! 🎉"})

    tokens_serial = [{'ttype': t.ttype, 'value': t.value, 'pos': t.pos} for t in tokens]
    return tokens, {'tokens': tokens_serial, 'logs': logs}


# ═══════════════════════════════════════════════════════════════════
#  PHASE 2 — PARSER  (structured)
# ═══════════════════════════════════════════════════════════════════

def parse_dict(tokens: list):
    logs    = []
    idx     = 0
    had_err = False

    def peek(offset=0):
        i = idx + offset
        return tokens[i] if i < len(tokens) else None

    def consume(expected_type=None):
        nonlocal idx
        tok = peek()
        if tok is None:
            raise ValueError(f"Ran out of tokens — expected {expected_type} but got nothing. GHOSTED. 👻")
        if expected_type and tok.ttype != expected_type:
            raise ValueError(f"Expected {expected_type} but found {tok.ttype} ({tok.value!r}) at pos {tok.pos}. Not it. 💀")
        idx += 1
        return tok

    def parse_expr():
        left = peek()
        if left is None:
            raise ValueError("Expected expression but got nothing. 🤐")
        if left.ttype in ("NUMERIC_LITERAL", "STRING_LITERAL", "BOOL_LITERAL", "IDENTIFIER"):
            consume()
            while peek() and peek().ttype == "ARITH_OP":
                op_tok = consume("ARITH_OP")
                right  = consume()
                if right.ttype not in ("NUMERIC_LITERAL", "IDENTIFIER"):
                    raise ValueError(f"Expected numeric operand after '{op_tok.value}', not {right.ttype}")
                logs.append({'type': 'parser-info', 'msg': f"  Arithmetic sub-expression: {left.value} {op_tok.value} {right.value} 🔢"})
                left = right
            return left
        elif left.ttype == "LPAREN":
            consume("LPAREN"); inner = parse_expr(); consume("RPAREN")
            return inner
        else:
            raise ValueError(f"Expression: got {left.ttype} ({left.value!r}). That's giving confusion. 😵\u200d💫")

    def parse_condition():
        left = parse_expr()
        if peek() and peek().ttype == "COMPARISON":
            op    = consume("COMPARISON")
            right = parse_expr()
            logs.append({'type': 'parser-info', 'msg': f"  Condition: {left.value} {op.value} {right.value} 👁️"})
            return (left, op, right)
        elif left.ttype == "BOOL_LITERAL":
            logs.append({'type': 'parser-info', 'msg': f"  Boolean condition: {left.value} 👾"})
            return (left, None, None)
        else:
            raise ValueError("Condition must use: slaps, ghosted, glowing, or cringe. No cap.")

    def parse_block():
        consume("BLOCK_OPEN"); stmts = []
        while peek() and peek().ttype != "BLOCK_CLOSE":
            stmts.append(parse_statement())
        consume("BLOCK_CLOSE")
        return stmts

    def parse_statement():
        first = peek()
        if first is None:
            raise ValueError("Expected a statement but got nothing. 🤫")

        if first.ttype == "DATATYPE":
            logs.append({'type': 'parser-info', 'msg': "Trying rule: [DATATYPE] [IDENTIFIER] [hits] [EXPR] [periodt]"})
            dtype = consume("DATATYPE"); ident = consume("IDENTIFIER")
            consume("ASSIGN_OP");        expr  = parse_expr(); consume("DELIMITER")
            logs.append({'type': 'parser-ok', 'msg': f"Rule SLAY ✓  →  {dtype.value} {ident.value} hits {expr.value} periodt"})
            return {'kind': 'DECLARATION', 'dtype': dtype, 'ident': ident, 'expr': expr}

        elif first.ttype == "OUTPUT_KW":
            logs.append({'type': 'parser-info', 'msg': "Trying rule: [spill] [EXPR] [periodt]"})
            consume("OUTPUT_KW"); expr = parse_expr(); consume("DELIMITER")
            logs.append({'type': 'parser-ok', 'msg': f"Rule SLAY ✓  →  spill {expr.value} periodt"})
            return {'kind': 'OUTPUT', 'expr': expr}

        elif first.ttype == "IF_KW":
            logs.append({'type': 'parser-info', 'msg': "Trying rule: lowkey [COND] era STMTS done  [ngl era STMTS done]"})
            consume("IF_KW"); cond = parse_condition(); then_body = parse_block()
            else_body = []
            if peek() and peek().ttype == "ELSE_KW":
                consume("ELSE_KW"); else_body = parse_block()
            logs.append({'type': 'parser-ok', 'msg': "lowkey/ngl (if/else) rule SLAY ✓"})
            return {'kind': 'IF', 'cond': cond, 'then': then_body, 'else': else_body}

        elif first.ttype == "WHILE_KW":
            logs.append({'type': 'parser-info', 'msg': "Trying rule: highkey [COND] era STMTS done"})
            consume("WHILE_KW"); cond = parse_condition(); body = parse_block()
            logs.append({'type': 'parser-ok', 'msg': "highkey (while) rule SLAY ✓"})
            return {'kind': 'WHILE', 'cond': cond, 'body': body}

        else:
            raise ValueError(f"Statement starts with {first.ttype} ({first.value!r}). Giving confusion. 😵\u200d💫")

    ast = []
    if not tokens:
        logs.append({'type': 'warn', 'msg': "No tokens to parse bestie. That's an empty era. 💀"})
        return ast, {'ast': [], 'logs': logs}

    while idx < len(tokens):
        try:
            ast.append(parse_statement())
        except ValueError as e:
            logs.append({'type': 'warn', 'msg': f"Syntax Error: {e}"})
            logs.append({'type': 'warn', 'msg': "Phrase-Level Recovery: scanning for next 'periodt'... 🔍"})
            found = False
            while idx < len(tokens):
                if tokens[idx].ttype == "DELIMITER":
                    idx += 1; found = True
                    logs.append({'type': 'warn', 'msg': "Recovery complete! Resuming after 'periodt'. We move. 💅"})
                    break
                idx += 1
            if not found:
                logs.append({'type': 'warn', 'msg': "No 'periodt' found. Parsing stopped early. 💀"})
                break
            had_err = True

    if had_err:
        logs.append({'type': 'warn', 'msg': "Syntax Analysis complete but we had some lore... (Phrase-Level Recovery applied) 📖"})
    else:
        logs.append({'type': 'ok', 'msg': "Syntax Analysis COMPLETE. Structure is immaculate. ✨"})

    return ast, {'ast': [], 'logs': logs}   # ast not serialised (used internally)


# ═══════════════════════════════════════════════════════════════════
#  PHASE 3 — SEMANTIC ANALYSER  (structured)
# ═══════════════════════════════════════════════════════════════════

def analyse_dict(ast: list):
    logs      = []
    sym_table = {}
    errors    = 0

    def check_expr(tok, expected_dtype):
        if tok.ttype == "IDENTIFIER":
            entry = sym_table.get(tok.value)
            if entry is None:
                raise ValueError(f"'{tok.value}' was never declared. That variable is a ghost. 👻")
            logs.append({'type': 'sem-info', 'msg': f"  Identifier '{tok.value}' resolved → type={entry['type']}, value={entry['value']} 🔍"})
            if expected_dtype and entry['type'] != expected_dtype:
                raise ValueError(f"Type mismatch: '{tok.value}' is '{entry['type']}' but expected '{expected_dtype}'. Mixed signals. ❌")
            return entry['value']
        elif tok.ttype == "NUMERIC_LITERAL":
            if expected_dtype == "texting":
                raise ValueError(f"'{tok.value}' is a NUMBER but variable declared as 'texting' (string). Not it bestie. ❌")
            return float(tok.value) if '.' in tok.value else int(tok.value)
        elif tok.ttype == "STRING_LITERAL":
            if expected_dtype == "numfr":
                raise ValueError(f"'{tok.value}' is a STRING but variable declared as 'numfr' (number). That's a MAJOR flop. ❌")
            return tok.value.strip('"')
        elif tok.ttype == "BOOL_LITERAL":
            if expected_dtype == "numfr":
                raise ValueError(f"'{tok.value}' is a BOOLEAN but declared as 'numfr'. Wrong energy. ❌")
            return tok.value == "slay"
        return tok.value

    def visit(stmt, depth=0):
        nonlocal errors
        kind = stmt['kind']

        if kind == "DECLARATION":
            dtype, ident, expr = stmt['dtype'], stmt['ident'], stmt['expr']
            logs.append({'type': 'sem-info', 'msg': f"Checking type compatibility for '{ident.value}'... 🔎"})
            logs.append({'type': 'sem-info', 'msg': f"  Declared type  : {dtype.value}"})
            logs.append({'type': 'sem-info', 'msg': f"  Assigned value : {expr.value}  (token type: {expr.ttype})"})
            try:
                resolved = check_expr(expr, dtype.value)
                logs.append({'type': 'sem-info', 'msg': "  Types are vibing. No coercion needed. ✅"})
                logs.append({'type': 'sem-info', 'msg': f"Binding '{ident.value}' into Symbol Table at Level {depth}. Main character moment. 💅"})
                sym_table[ident.value] = {'type': dtype.value, 'value': resolved, 'level': depth}
                logs.append({'type': 'ok', 'msg': f"'{ident.value}' successfully bound. That variable is iconic. 🌟"})
            except ValueError as se:
                logs.append({'type': 'err', 'msg': f"SEMANTIC ERROR: {se}"})
                logs.append({'type': 'warn', 'msg': "Recovery Strategy: assignment discarded to protect memory. We move. 🏃"})
                errors += 1

        elif kind == "OUTPUT":
            expr = stmt['expr']
            logs.append({'type': 'sem-info', 'msg': f"'spill' incoming! Resolving: {expr.value} 📢"})
            if expr.ttype == "IDENTIFIER":
                entry = sym_table.get(expr.value)
                if entry is None:
                    logs.append({'type': 'err', 'msg': f"SEMANTIC ERROR: '{expr.value}' is undeclared. Can't spill what doesn't exist. 💀"})
                    errors += 1
                else:
                    logs.append({'type': 'spill', 'msg': f"{expr.value} = {entry['value']}"})
            else:
                logs.append({'type': 'spill', 'msg': str(expr.value)})

        elif kind == "IF":
            left, op, right = stmt['cond']
            logs.append({'type': 'sem-info', 'msg': "Checking 'lowkey' (if) condition... 🤔"})
            if op:
                logs.append({'type': 'sem-info', 'msg': f"  Condition: {left.value} {op.value} {right.value}"})
            logs.append({'type': 'ok', 'msg': "Condition structure is slay. ✅"})
            logs.append({'type': 'sem-info', 'msg': f"Analysing 'era' (then) block at Level {depth + 1}... 📂"})
            for s in stmt['then']:
                visit(s, depth + 1)
            if stmt['else']:
                logs.append({'type': 'sem-info', 'msg': f"Analysing 'ngl era' (else) block at Level {depth + 1}... 😏"})
                for s in stmt['else']:
                    visit(s, depth + 1)

        elif kind == "WHILE":
            left, op, right = stmt['cond']
            logs.append({'type': 'sem-info', 'msg': "Checking 'highkey' (while) loop condition... 🔄"})
            if op:
                logs.append({'type': 'sem-info', 'msg': f"  Condition: {left.value} {op.value} {right.value}"})
            logs.append({'type': 'ok', 'msg': "Loop condition structure is valid. ✅"})
            logs.append({'type': 'sem-info', 'msg': f"Analysing loop body at Level {depth + 1}... 🏃"})
            for s in stmt['body']:
                visit(s, depth + 1)

    for stmt in ast:
        visit(stmt, 0)
        logs.append({'type': 'divider'})

    if errors == 0:
        logs.append({'type': 'ok', 'msg': "Semantic Analysis COMPLETE. Absolutely slayin'. No errors. We eat. 🍽️✨"})
    else:
        logs.append({'type': 'err', 'msg': f"Semantic Analysis COMPLETE with {errors} error(s). That's giving compiler trauma. 💀"})

    # make sym_table JSON-serialisable (booleans are fine, ints/floats/strings too)
    sym_serial = {k: {'type': v['type'], 'value': v['value'], 'level': v['level']} for k, v in sym_table.items()}

    # build per-level totals
    level_totals = {}
    for entry in sym_table.values():
        lv = entry['level']
        level_totals[lv] = level_totals.get(lv, 0) + 1

    return {'logs': logs, 'symTable': sym_serial, 'levelTotals': level_totals, 'grandTotal': len(sym_table), 'errors': errors}


# ═══════════════════════════════════════════════════════════════════
#  COMPILE ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════

def compile_to_dict(source: str) -> dict:
    tokens, lex_result   = tokenize_dict(source)
    ast,    parse_result = parse_dict(tokens)
    sem_result           = analyse_dict(ast)
    return {
        'lexer':    lex_result,
        'parser':   parse_result,
        'semantic': sem_result,
    }


# ═══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("✨  slay.lang IDE  →  http://localhost:5000")
    app.run(debug=True, port=5000)

