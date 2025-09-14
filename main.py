import os
import textwrap
import sys
import tempfile
import uuid
import types
import ply.lex as lex
import ply.yacc as yacc

# ==================================================================
# PascalLite lexer/parser (robust build for sandboxed environments)
# ==================================================================
# This script writes the token/grammar definitions to a temporary
# source file and then executes that source into a new ModuleType
# object. We avoid importlib.spec_from_file_location because in some
# sandboxes it returns a spec with a None loader. Using compile()+exec
# into a ModuleType (and ensuring the file exists at MODULE_PATH)
# guarantees inspect.getsourcelines and PLY's introspection work.
# ==================================================================

MODULE_CONTENT = textwrap.dedent(r"""
# pascallite_module: token and grammar definitions for PascalLite

reserved = {
    'program': 'PROGRAM',
    'var': 'VAR',
    'integer': 'INTEGER',
    'boolean': 'BOOLEAN',
    'begin': 'BEGIN',
    'end': 'END',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
    'read': 'READ',
    'write': 'WRITE',
    'true': 'TRUE',
    'false': 'FALSE',
    'div': 'DIV',
    'mod': 'MOD',
    'not': 'NOT',
    'or': 'OR',
    'and': 'AND'
}

tokens = [
    'IDENTIFICADOR', 'NUMERO',
    'ATRIBUICAO', 'MAIOR', 'MENOR', 'IGUAL', 'DIFERENTE', 'MAIORIGUAL', 'MENORIGUAL',
    'SOMA', 'SUB', 'MUL', 'DIVISAO',
    'DOISPONTOS', 'PONTOEVIRGULA', 'VIRGULA', 'PONTO',
    'ABREPAREN', 'FECHAPAREN'
] + list(reserved.values())

# Simple token regexes
t_ATRIBUICAO = r':='

t_MAIORIGUAL = r'>='

t_MENORIGUAL = r'<='

t_DIFERENTE = r'<> '

# Ensure t_DIFERENTE is set correctly to '<>' (we will strip later).

t_MAIOR = r'>'

t_MENOR = r'<'

t_IGUAL = r'='

t_SOMA = r'\+'

t_SUB = r'-'

t_MUL = r'\*'

t_DIVISAO = r'/'

t_DOISPONTOS = r':'

t_PONTOEVIRGULA = r';'

t_VIRGULA = r','

t_PONTO = r'\.'

t_ABREPAREN = r'\('

t_FECHAPAREN = r'\)'

# Identifier and reserved words (note: enforce length > 20 as lexical error)
def t_IDENTIFICADOR(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    if len(t.value) > 20:
        # Report lexical error for identifiers longer than 20 characters
        print(f"Erro Léxico: identificador '{t.value}' maior que 20 caracteres na linha {t.lexer.lineno}")
    t.type = reserved.get(t.value.lower(), 'IDENTIFICADOR')
    return t

# Integers
def t_NUMERO(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

# Ignored characters (spaces and tabs)
t_ignore = ' \t'

# Comments: (* ... *) and { ... } and //... (preserve line numbers)
def t_comment_multiline(t):
    r'\(\*[\s\S]*?\*\)'
    t.lexer.lineno += t.value.count('\n')


def t_comment_braces(t):
    r'\{[^}]*\}'
    t.lexer.lineno += t.value.count('\n')


def t_comment_line(t):
    r'//.*'
    pass

# Newlines
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Lexical error
def t_error(t):
    print(f"Erro Léxico: caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

# Operator precedence and grammar rules (PascalLite grammar simplified)
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'IGUAL', 'DIFERENTE', 'MAIOR', 'MENOR', 'MAIORIGUAL', 'MENORIGUAL'),
    ('left', 'SOMA', 'SUB'),
    ('left', 'MUL', 'DIVISAO', 'DIV', 'MOD'),
    ('right', 'NOT')
)

def p_programa(p):
    'programa : PROGRAM IDENTIFICADOR PONTOEVIRGULA bloco PONTO'
    p[0] = ("programa", p[2], p[4])

def p_bloco(p):
    '''bloco : declaracoes comando_composto
              | comando_composto'''
    if len(p) == 3:
        p[0] = ("bloco", p[1], p[2])
    else:
        p[0] = ("bloco", p[1])

def p_declaracoes(p):
    'declaracoes : VAR declaracao_lista'
    p[0] = ("declaracoes", p[2])

def p_declaracao_lista(p):
    '''declaracao_lista : declaracao PONTOEVIRGULA declaracao_lista
                         | declaracao PONTOEVIRGULA'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_declaracao(p):
    'declaracao : lista_ident DOISPONTOS tipo'
    p[0] = ("declaracao", p[1], p[3])

def p_lista_ident(p):
    '''lista_ident : IDENTIFICADOR
                    | IDENTIFICADOR VIRGULA lista_ident'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_tipo(p):
    '''tipo : INTEGER
             | BOOLEAN'''
    p[0] = p[1]

def p_comando_composto(p):
    'comando_composto : BEGIN lista_comandos END'
    p[0] = ("comando_composto", p[2])

def p_lista_comandos(p):
    '''lista_comandos : comando PONTOEVIRGULA lista_comandos
                       | comando'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_comando(p):
    '''comando : atribuicao
                | comando_if
                | comando_while
                | comando_read
                | comando_write
                | comando_composto'''
    p[0] = p[1]

def p_atribuicao(p):
    'atribuicao : IDENTIFICADOR ATRIBUICAO expressao'
    p[0] = ("atribuicao", p[1], p[3])

def p_comando_if(p):
    '''comando_if : IF expressao THEN comando
                   | IF expressao THEN comando ELSE comando'''
    if len(p) == 5:
        p[0] = ("if", p[2], p[4], None)
    else:
        p[0] = ("if", p[2], p[4], p[6])

def p_comando_while(p):
    'comando_while : WHILE expressao DO comando'
    p[0] = ("while", p[2], p[4])

def p_comando_read(p):
    'comando_read : READ ABREPAREN lista_ident FECHAPAREN'
    p[0] = ("read", p[3])

def p_comando_write(p):
    'comando_write : WRITE ABREPAREN lista_expressoes FECHAPAREN'
    p[0] = ("write", p[3])

def p_lista_expressoes(p):
    '''lista_expressoes : expressao
                         | expressao VIRGULA lista_expressoes'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_expressao(p):
    '''expressao : expressao IGUAL expressao
                 | expressao DIFERENTE expressao
                 | expressao MAIOR expressao
                 | expressao MENOR expressao
                 | expressao MAIORIGUAL expressao
                 | expressao MENORIGUAL expressao
                 | expressao SOMA expressao
                 | expressao SUB expressao
                 | expressao MUL expressao
                 | expressao DIVISAO expressao
                 | expressao DIV expressao
                 | expressao MOD expressao
                 | NOT expressao
                 | ABREPAREN expressao FECHAPAREN
                 | IDENTIFICADOR
                 | NUMERO
                 | TRUE
                 | FALSE'''
    if len(p) == 2:
        p[0] = ("valor", p[1])
    elif len(p) == 3:
        p[0] = ("unario", p[1], p[2])
    elif len(p) == 4:
        if p.slice[1].type == 'ABREPAREN':
            p[0] = p[2]
        else:
            p[0] = ("binario", p[2], p[1], p[3])

def p_error(p):
    if p:
        print(f"Erro Sintático: Token inesperado '{p.value}' na linha {p.lineno}")
    else:
        print("Erro Sintático: Fim de arquivo inesperado")
""")

# Create a temporary file for the module source. We try system temp dir
# first, then cwd as a fallback. The file must exist because inspect
# often reads the source file when retrieving source lines.
MODULE_PATH = None

# Attempt 1: NamedTemporaryFile in system temp dir
try:
    tmpf = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')
    tmpf.write(MODULE_CONTENT)
    tmpf.flush()
    tmpf.close()
    MODULE_PATH = tmpf.name
except Exception:
    # Attempt 2: write to current working directory
    try:
        MODULE_PATH = os.path.join(os.getcwd(), f'pascallite_module_{uuid.uuid4().hex}.py')
        with open(MODULE_PATH, 'w', encoding='utf-8') as f:
            f.write(MODULE_CONTENT)
    except Exception as e:
        raise RuntimeError(
            'Não foi possível criar arquivo temporário para o módulo pascallite. ' 
            'Verifique permissões de escrita no filesystem do ambiente.'
        ) from e

# Sanity check: the file must exist and be readable
if not MODULE_PATH or not os.path.exists(MODULE_PATH):
    raise RuntimeError(f"Arquivo de módulo não encontrado em {MODULE_PATH}")

# Build a new ModuleType and execute the module source into it. This
# ensures the module object has a __file__ and functions with code
# objects referencing MODULE_PATH, so PLY/inspect can find source lines.
module_name = 'pascallite_module'
_pmod = types.ModuleType(module_name)
_pmod.__file__ = MODULE_PATH
# Execute the source with filename set to MODULE_PATH so code objects
# have co_filename pointing to the real file.
exec(compile(MODULE_CONTENT, MODULE_PATH, 'exec'), _pmod.__dict__)
# Register in sys.modules so other tools can import it if needed
sys.modules[module_name] = _pmod

# Now create lexer and parser by passing the module to PLY
try:
    # Fix potential trailing spaces in token regexes before building
    # PLY's lexer: ensure t_DIFERENTE is a clean '<>' pattern
    if hasattr(_pmod, 't_DIFERENTE') and isinstance(_pmod.t_DIFERENTE, str):
        _pmod.t_DIFERENTE = _pmod.t_DIFERENTE.strip()
    lexer = lex.lex(module=_pmod)
except Exception as e:
    print('\nErro ao criar o lexer com ply.lex(module=_pmod):', e)
    raise

try:
    parser = yacc.yacc(module=_pmod)
except Exception as e:
    print('\nErro ao criar o parser com ply.yacc(module=_pmod):', e)
    raise


# -----------------------------
# Funções de teste / utilitários
# -----------------------------

def analyze_code(code_string, description):
    print("=" * 60)
    print(f"Análise do Código: {description}")
    print("=" * 60)

    # Lexical analysis using the created lexer
    lexer.lineno = 1
    lexer.input(code_string)

    print('\n--- Tokens (Análise Léxica) ---')
    while True:
        tok = lexer.token()
        if not tok:
            break
        # compute column for nicer output (if lexpos available)
        try:
            last_newline = code_string.rfind('\n', 0, tok.lexpos)
            column = tok.lexpos - last_newline
        except Exception:
            column = '?'
        print(f"Linha: {tok.lineno}, Coluna: {column} - Token: {tok.type} - Lexema: {tok.value}")

    # Syntactic analysis using the created parser
    print('\n--- Análise Sintática ---')
    try:
        result = parser.parse(code_string, lexer=lexer)
        print('\nAnálise sintática concluída (verificar mensagens de erro acima se houver)')
    except Exception as e:
        print('\nErro durante análise sintática:', e)

    print('-' * 60)


# ==========================
# Casos de teste (mantidos + extras)
# ==========================

# Test (original) - mantido exatamente
codigo_correto = """
program exemplo;
var x, y: integer;
begin
    x := 10;
    y := x + 5;
    write(y);
end.
"""

# Testes adicionais (erros léxicos / sintáticos)
codigo_erro_lexico = """
program ErroLexico;
var a: integer;
begin
    a := 10;
    b := &a; // caractere & ilegal
end.
"""

codigo_erro_sintaxe_ponto_virgula = """
program ErroSintaxe;
var x: integer
begin
    x := 5;
end.
"""

codigo_identificador_longo = """
program IdentLong;
var this_identifier_is_way_too_long_to_be_valid: integer;
begin
end.
"""

codigo_expressao_malformada = """
program ExprErr;
var x: integer;
begin
    x := 5 + * 2;
end.
"""

codigo_comentarios = """
program Coments;
var x: integer;
(* comentario de
multiplas linhas *)
begin
    x := 1; // comentario linha
    write(x);
end.
"""

# Teste extra: precedence and parentheses
codigo_precedencia = """
program Preced;
var r: integer;
begin
    r := 5 + 3 * 2;
    r := (5 + 3) * 2;
    write(r);
end.
"""

# Teste extra: operador diferente '<>'
codigo_diferente = """
program Dif;
var a, b: integer;
begin
    a := 1;
    b := 2;
    if a <> b then
        write(a);
end.
"""

# Execute analyses (original tests preserved)
analyze_code(codigo_correto, "Código Correto")
analyze_code(codigo_erro_lexico, "Erro Léxico (caractere ilegal)")
analyze_code(codigo_erro_sintaxe_ponto_virgula, "Erro Sintático (ponto e vírgula ausente)")
analyze_code(codigo_identificador_longo, "Erro Léxico (identificador muito longo)")
analyze_code(codigo_expressao_malformada, "Erro Sintático (expressão mal formada)")
analyze_code(codigo_comentarios, "Teste de Comentários")
analyze_code(codigo_precedencia, "Teste de Precedência e Parênteses")
analyze_code(codigo_diferente, "Teste operador '<>' (DIFERENTE)")
