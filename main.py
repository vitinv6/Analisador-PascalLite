import os
import textwrap
import sys
import tempfile
import uuid
import types
import ply.lex as lex
import ply.yacc as yacc

# ==================================================================
# Lexer/Parser PascalLite (construção robusta para ambientes restritos)
# ==================================================================
# Este script escreve as definições de tokens/gramática em um arquivo
# temporário e então executa esse código-fonte dentro de um novo objeto
# ModuleType. Evitamos importlib.spec_from_file_location porque em alguns
# ambientes restritos (sandboxes) ele retorna uma especificação com um loader Nulo.
# Usar compile()+exec em um ModuleType (e garantir que o arquivo exista
# no MODULE_PATH) garante que o inspect.getsourcelines e a introspecção
# da biblioteca PLY funcionem corretamente.
# ==================================================================

MODULE_CONTENT = textwrap.dedent(r"""
# pascallite_module: definições de tokens e da gramática para PascalLite

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

# Regex para tokens simples
t_ATRIBUICAO = r':='
t_MAIORIGUAL = r'>='
t_MENORIGUAL = r'<='
t_DIFERENTE = r'<>'
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

# Identificadores e palavras reservadas (nota: impõe tamanho > 20 como erro léxico)
def t_IDENTIFICADOR(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    if len(t.value) > 20:
        # Reporta erro léxico para identificadores com mais de 20 caracteres
        print(f"Erro Léxico: identificador '{t.value}' maior que 20 caracteres na linha {t.lexer.lineno}")
    t.type = reserved.get(t.value.lower(), 'IDENTIFICADOR')
    return t

# Números inteiros
def t_NUMERO(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

# Caracteres ignorados (espaços e tabs)
t_ignore = ' \t'

# Comentários: (* ... *), { ... } e //... (preserva o número das linhas)
def t_comment_multiline(t):
    r'\(\*[\s\S]*?\*\)'
    t.lexer.lineno += t.value.count('\n')

def t_comment_braces(t):
    r'\{[^}]*\}'
    t.lexer.lineno += t.value.count('\n')

def t_comment_line(t):
    r'//.*'
    pass

# Novas linhas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Erro léxico
def t_error(t):
    print(f"Erro Léxico: caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

# Precedência de operadores e regras da gramática (gramática PascalLite simplificada)
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

# Cria um arquivo temporário para o código do módulo. Tentamos o diretório
# temporário do sistema primeiro, e depois o diretório atual como alternativa.
# O arquivo precisa existir porque a função 'inspect' frequentemente lê o
# arquivo de código-fonte para obter as linhas.
MODULE_PATH = None

# Tentativa 1: NamedTemporaryFile no diretório temporário do sistema
try:
    tmpf = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')
    tmpf.write(MODULE_CONTENT)
    tmpf.flush()
    tmpf.close()
    MODULE_PATH = tmpf.name
except Exception:
    # Tentativa 2: escrever no diretório de trabalho atual
    try:
        MODULE_PATH = os.path.join(os.getcwd(), f'pascallite_module_{uuid.uuid4().hex}.py')
        with open(MODULE_PATH, 'w', encoding='utf-8') as f:
            f.write(MODULE_CONTENT)
    except Exception as e:
        raise RuntimeError(
            'Não foi possível criar arquivo temporário para o módulo pascallite. '
            'Verifique permissões de escrita no filesystem do ambiente.'
        ) from e

# Verificação de sanidade: o arquivo deve existir e ser legível
if not MODULE_PATH or not os.path.exists(MODULE_PATH):
    raise RuntimeError(f"Arquivo de módulo não encontrado em {MODULE_PATH}")

# Constrói um novo ModuleType e executa o código-fonte do módulo nele. Isso
# garante que o objeto do módulo tenha um atributo __file__ e que as funções
# com objetos de código referenciem o MODULE_PATH, para que o PLY/inspect
# consiga encontrar as linhas de código-fonte.
module_name = 'pascallite_module'
_pmod = types.ModuleType(module_name)
_pmod.__file__ = MODULE_PATH
# Executa o código-fonte com o nome do arquivo definido como MODULE_PATH para que
# os objetos de código (code objects) tenham o atributo co_filename apontando para o arquivo real.
exec(compile(MODULE_CONTENT, MODULE_PATH, 'exec'), _pmod.__dict__)
# Registra em sys.modules para que outras ferramentas possam importá-lo se necessário
sys.modules[module_name] = _pmod

# Agora cria o lexer e o parser passando o módulo para o PLY
try:
    # Corrige potenciais espaços extras nas regex dos tokens antes de construir
    # o lexer do PLY: garante que o padrão de t_DIFERENTE seja um '<>' limpo
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

    # Análise léxica usando o lexer criado
    lexer.lineno = 1
    lexer.input(code_string)

    print('\n--- Tokens (Análise Léxica) ---')
    while True:
        tok = lexer.token()
        if not tok:
            break
        # calcula a coluna para uma saída mais legível (se lexpos estiver disponível)
        try:
            last_newline = code_string.rfind('\n', 0, tok.lexpos)
            column = tok.lexpos - last_newline
        except Exception:
            column = '?'
        print(f"Linha: {tok.lineno}, Coluna: {column} - Token: {tok.type} - Lexema: {tok.value}")

    # Análise sintática usando o parser criado
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

# Teste (original) - mantido exatamente
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

# Teste extra: precedência e parênteses
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

# Executa as análises (testes originais preservados)
analyze_code(codigo_correto, "Código Correto")
analyze_code(codigo_erro_lexico, "Erro Léxico (caractere ilegal)")
analyze_code(codigo_erro_sintaxe_ponto_virgula, "Erro Sintático (ponto e vírgula ausente)")
analyze_code(codigo_identificador_longo, "Erro Léxico (identificador muito longo)")
analyze_code(codigo_expressao_malformada, "Erro Sintático (expressão mal formada)")
analyze_code(codigo_comentarios, "Teste de Comentários")
analyze_code(codigo_precedencia, "Teste de Precedência e Parênteses")
analyze_code(codigo_diferente, "Teste operador '<>' (DIFERENTE)")
