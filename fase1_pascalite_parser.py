import os
import textwrap
import sys
import tempfile
import uuid
import types
import ply.lex as lex
import ply.yacc as yacc

# ==================================================================
# Lexer/Parser MicroC (construção robusta para ambientes sandboxed)
# ==================================================================
# Este script cria dinamicamente um pequeno módulo contendo as
# definições de tokens/gramática para MicroC, carrega-o em um
# ModuleType e então cria lexer/parser usando ply.lex(module=_pmod)
# e ply.yacc(module=_pmod).
# ==================================================================

CONTEUDO_MODULO = textwrap.dedent(r"""
# microc_module: definições de token e gramática para MicroC (int/bool)

reservadas = {
    'int': 'INT',
    'bool': 'BOOL',
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'read': 'READ',
    'write': 'WRITE',
    'true': 'TRUE',
    'false': 'FALSE',
    'main': 'MAIN',
    'return': 'RETURN'
}

# tokens básicos + palavras reservadas (serão somados)
tokens = [
    'IDENT', 'NUM',
    'ASSIGN', 'EQ', 'NEQ', 'GE', 'LE', 'GT', 'LT',
    'PLUS', 'MINUS', 'TIMES', 'DIV',
    'AND', 'OR', 'NOT',
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
    'SEMI', 'COMMA'
] + list(reservadas.values())

# Tokens com regex (atenção: tokens mais longos primeiro)
t_EQ     = r'=='
t_NEQ    = r'!='
t_GE     = r'>='
t_LE     = r'<='
t_AND    = r'&&'
t_OR     = r'\|\|'
t_ASSIGN = r'='
t_GT     = r'>'
t_LT     = r'<'
t_PLUS   = r'\+'
t_MINUS  = r'-'
t_TIMES  = r'\*'
t_DIV    = r'/'
t_NOT    = r'!'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_SEMI   = r';'
t_COMMA  = r','

# Identificador (com verificação de comprimento)
def t_IDENT(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    if len(t.value) > 20:
        # Reporta erro léxico para identificadores maiores que 20 caracteres
        print(f"Erro Léxico: identificador '{t.value}' maior que 20 caracteres na linha {t.lexer.lineno}")
    t.type = reservadas.get(t.value, 'IDENT')
    return t

# Números inteiros
def t_NUM(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

# Ignora espaços e tabs (mas não newlines)
t_ignore = ' \t'

# Comentários multiline (/* ... */) preservam nova linha
def t_COMMENT_MULTILINE(t):
    r'/\*[\s\S]*?\*/'
    t.lexer.lineno += t.value.count('\n')

# Comentário de linha //
def t_COMMENT_LINE(t):
    r'//.*'
    pass

# Newlines
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Erro léxico
def t_error(t):
    print(f"Erro Léxico: caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

# Precedência (operadores lógicos, relacionais, aritméticos, unário)
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQ', 'NEQ', 'GT', 'LT', 'GE', 'LE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIV'),
    ('right', 'NOT'),
    ('right', 'UMINUS')
)

# ---------------------------
# Regras da gramática (MicroC)
# ---------------------------

# programa obrigatório: tipo main() { ... }
def p_program(p):
    'program : INT MAIN LPAREN RPAREN compound_stmt'
    p[0] = ("program", p[1], p[6])

# bloco composto: { lista_comandos }
def p_compound_stmt(p):
    'compound_stmt : LBRACE statement_list RBRACE'
    p[0] = ("compound", p[2])

# lista de comandos (pode ser vazia)
def p_statement_list(p):
    '''statement_list : statement_list_nonempty
                      | empty'''
    p[0] = p[1]

def p_statement_list_nonempty(p):
    '''statement_list_nonempty : statement
                               | statement statement_list_nonempty'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[2]

def p_empty(p):
    'empty :'
    p[0] = []

# declaração de variáveis: int x, y;
def p_declaration_stmt(p):
    'declaration_stmt : INT id_list SEMI'
    p[0] = ("decl", p[2])

def p_id_list(p):
    '''id_list : IDENT
               | IDENT COMMA id_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

# statement: pode ser atribuição, if, while, read, write, compound, declaration
def p_statement(p):
    '''statement : assignment
                 | if_stmt
                 | while_stmt
                 | read_stmt
                 | write_stmt
                 | compound_stmt
                 | declaration_stmt
                 | SEMI'''  # permite ponto-e-vírgula isolado
    p[0] = p[1] if len(p) > 1 else ("empty_semi",)

# assignment: x = expr;
def p_assignment(p):
    'assignment : IDENT ASSIGN expression SEMI'
    p[0] = ("assign", p[1], p[3])

# if (cond) stmt [ else stmt ]
def p_if_stmt(p):
    '''if_stmt : IF LPAREN expression RPAREN statement
               | IF LPAREN expression RPAREN statement ELSE statement'''
    if len(p) == 6:
        p[0] = ("if", p[3], p[5], None)
    else:
        p[0] = ("if", p[3], p[5], p[7])

# while (cond) stmt
def p_while_stmt(p):
    'while_stmt : WHILE LPAREN expression RPAREN statement'
    p[0] = ("while", p[3], p[5])

# read(x, y);
def p_read_stmt(p):
    'read_stmt : READ LPAREN id_list RPAREN SEMI'
    p[0] = ("read", p[3])

# write(expr, ...);
def p_write_stmt(p):
    'write_stmt : WRITE LPAREN expr_list RPAREN SEMI'
    p[0] = ("write", p[3])

def p_expr_list(p):
    '''expr_list : expression
                 | expression COMMA expr_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

# expressões (binárias, unárias, parênteses, identificador, número, true/false)
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIV expression
                  | expression EQ expression
                  | expression NEQ expression
                  | expression GT expression
                  | expression LT expression
                  | expression GE expression
                  | expression LE expression
                  | expression AND expression
                  | expression OR expression'''
    p[0] = ("binop", p[2], p[1], p[3])

def p_expression_unop(p):
    '''expression : NOT expression
                  | MINUS expression %prec UMINUS'''
    if p[1] == '-':
        p[0] = ("unary", "neg", p[2])
    else:
        p[0] = ("unary", p[1], p[2])

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

def p_expression_value(p):
    '''expression : IDENT
                  | NUM
                  | TRUE
                  | FALSE'''
    p[0] = ("value", p[1])

# erro sintático
def p_error(p):
    if p:
        try:
            lineno = p.lineno
        except AttributeError:
            lineno = '?'
        print(f"Erro Sintático: Token inesperado '{p.value}' na linha {lineno}")
    else:
        print("Erro Sintático: Fim de arquivo inesperado")
""")

# -------------------------
# Cria arquivo temporário do módulo e carrega em ModuleType
# -------------------------
CAMINHO_MODULO = None
try:
    tmpf = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')
    tmpf.write(CONTEUDO_MODULO)
    tmpf.flush()
    tmpf.close()
    CAMINHO_MODULO = tmpf.name
except Exception:
    try:
        CAMINHO_MODULO = os.path.join(os.getcwd(), f'microc_module_{uuid.uuid4().hex}.py')
        with open(CAMINHO_MODULO, 'w', encoding='utf-8') as f:
            f.write(CONTEUDO_MODULO)
    except Exception as e:
        raise RuntimeError(
            'Não foi possível criar arquivo temporário para o módulo microc. '
            'Verifique permissões de escrita no filesystem do ambiente.'
        ) from e

if not CAMINHO_MODULO or not os.path.exists(CAMINHO_MODULO):
    raise RuntimeError(f"Arquivo de módulo não encontrado em {CAMINHO_MODULO}")

nome_modulo = 'microc_module'
_pmod = types.ModuleType(nome_modulo)
_pmod.__file__ = CAMINHO_MODULO
exec(compile(CONTEUDO_MODULO, CAMINHO_MODULO, 'exec'), _pmod.__dict__)
sys.modules[nome_modulo] = _pmod

# Ajuste: criar lexer/parser a partir do módulo dinâmico
try:
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
def analisa_codigo(codigo_string, descricao):
    print("=" * 70)
    print(f"Análise do Código: {descricao}")
    print("=" * 70)

    # Análise léxica usando o lexer criado (novo lexer temporário para listar tokens)
    temp_lexer = lex.lex(module=_pmod)
    temp_lexer.input(codigo_string)

    print('\n--- Tokens (Análise Léxica) ---')
    while True:
        tok = temp_lexer.token()
        if not tok:
            break
        try:
            last_newline = codigo_string.rfind('\n', 0, tok.lexpos)
            column = tok.lexpos - last_newline
        except Exception:
            column = '?'
        print(f"Linha: {tok.lineno}, Coluna: {column} - Token: {tok.type} - Lexema: {tok.value}")

    # Análise sintática usando o parser criado
    print('\n--- Análise Sintática ---')
    try:
        # Resetar lexer e usar para parser
        lexer.lineno = 1
        lexer.input(codigo_string)
        result = parser.parse(codigo_string, lexer=lexer)
        if isinstance(result, tuple):
            print('\nAnálise sintática concluída com sucesso (Árvore gerada).')
            # Mostra a tupla/árvore gerada resumida
            print('Árvore (resumo):', result)
        else:
            print('\nAnálise sintática concluída (verificar mensagens de erro acima se houver).')
    except Exception as e:
        print(f'\nErro durante análise sintática: {e}')

    print('-' * 70)

# ==========================
# Casos de teste MicroC
# ==========================
codigo_correto = """
int main() {
    int x, y;
    x = 10;
    y = x + 5;
    write(y);
}
"""

codigo_erro_lexico = """
int main() {
    int a;
    a = 10;
    b = &a; // caractere '&' ilegal
}
"""

codigo_erro_sintaxe_semi = """
int main() {
    int x
    x = 5;
}
"""

codigo_identificador_longo = """
int main() {
    int this_identifier_is_way_too_long_to_be_valid;
}
"""

codigo_expressao_malformada = """
int main() {
    int x;
    x = 5 + * 2;
}
"""

codigo_comentarios = """
int main() {
    /* comentario
       multiplas linhas */
    int x;
    x = 1; // comentario de linha
    write(x);
}
"""

codigo_precedencia = """
int main() {
    int r;
    r = 5 + 3 * 2;
    r = (5 + 3) * 2;
    write(r);
}
"""

codigo_if_while = """
int main() {
    int a, b;
    a = 1;
    b = 5;
    if (a != b) {
        write(a);
    } else {
        write(b);
    }
    while (a < b) {
        a = a + 1;
    }
    write(a);
}
"""

# Executa as análises
analisa_codigo(codigo_correto, "Código Correto (MicroC)")
analisa_codigo(codigo_erro_lexico, "Erro Léxico (caractere ilegal)")
analisa_codigo(codigo_erro_sintaxe_semi, "Erro Sintático (ponto-e-vírgula ausente)")
analisa_codigo(codigo_identificador_longo, "Erro Léxico (identificador muito longo)")
analisa_codigo(codigo_expressao_malformada, "Erro Sintático (expressão mal formada)")
analisa_codigo(codigo_comentarios, "Teste de Comentários")
analisa_codigo(codigo_precedencia, "Teste de Precedência e Parênteses")
analisa_codigo(codigo_if_while, "Teste if/while")