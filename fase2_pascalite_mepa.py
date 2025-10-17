import sys
import ply.lex as lex
import ply.yacc as yacc

# ==================================================================
# Tokens / Palavras Reservadas (Adaptado para PascalLite Simplificado)
# ==================================================================
# Nota: Os tokens BOOLEAN, TRUE, FALSE e operadores lógicos foram removidos
# para seguir a simplificação do enunciado: "somente variáveis e expressões do tipo inteiro"

reserved = {
    'program': 'PROGRAM',
    'var': 'VAR',
    'integer': 'INTEGER',
    'begin': 'BEGIN',
    'end': 'END',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
    'read': 'READ',
    'write': 'WRITE'
}

tokens = [
    'IDENTIFICADOR', 'NUMERO',
    'ATRIBUICAO', 'MAIOR', 'MENOR', 'IGUAL', 'DIFERENTE', 'MAIORIGUAL', 'MENORIGUAL',
    'SOMA', 'SUB', 'MUL', 'DIVISAO',
    'DOISPONTOS', 'PONTOEVIRGULA', 'VIRGULA', 'PONTO',
    'ABREPAREN', 'FECHAPAREN'
] + list(reserved.values())

# Regexs para tokens simples
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

# Identificador / número
def t_IDENTIFICADOR(t):
    r'[A-Za-z_][A-Za-z0-9_]*'
    t.type = reserved.get(t.value.lower(), 'IDENTIFICADOR')
    return t

def t_NUMERO(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

t_ignore = ' \t'

# Comentários e newline
def t_comment_multiline(t):
    r'\(\*[\s\S]*?\*\)'
    t.lexer.lineno += t.value.count('\n')

def t_comment_braces(t):
    r'\{[^}]*\}'
    t.lexer.lineno += t.value.count('\n')

def t_comment_line(t):
    r'//.*'
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Erro Léxico: caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

# ==================================================================
# Tabela de Símbolos e Utilitários Semânticos
# ==================================================================
tabela_simbolos = {}
proximo_endereco = 0
rotulo_contador = 0

def insere_tabela_simbolos(nome, tipo):
    global proximo_endereco
    if nome in tabela_simbolos:
        # Erro semântico: Variável já declarada
        raise SystemExit(f"Erro semântico: variável '{nome}' já declarada.")
    tabela_simbolos[nome] = {"tipo": tipo, "endereco": proximo_endereco}
    proximo_endereco += 1

def busca_tabela_simbolos(nome):
    if nome not in tabela_simbolos:
        # Erro semântico: Variável não declarada
        raise SystemExit(f"Erro semântico: variável '{nome}' não declarada.")
    return tabela_simbolos[nome]["endereco"]

def proximo_rotulo():
    global rotulo_contador
    rotulo_contador += 1
    return f"L{rotulo_contador}"

# ==================================================================
# Precedência e Gramática (com Geração MEPA)
# ==================================================================

precedence = (
    ('left', 'SOMA', 'SUB'),
    ('left', 'MUL', 'DIVISAO')
)

def p_programa(p):
    'programa : PROGRAM IDENTIFICADOR PONTOEVIRGULA declaracoes bloco_final'
    # Geração do código de inicialização e finalização MEPA
    print("INPP")
    # Usa o tamanho da tabela para AMEM
    print(f"AMEM {len(tabela_simbolos)}")
    # O código do bloco foi gerado antes de 'PONTO' ser consumido
    print("PARA")

def p_declaracoes(p):
    'declaracoes : VAR lista_declaracoes'
    pass # As ações semânticas já foram executadas em p_declaracao

def p_lista_declaracoes(p):
    '''lista_declaracoes : declaracao PONTOEVIRGULA lista_declaracoes
                         | declaracao PONTOEVIRGULA'''
    pass

def p_declaracao(p):
    'declaracao : lista_ident DOISPONTOS INTEGER'
    # Insere cada identificador na tabela de símbolos
    for ident in p[1]:
        insere_tabela_simbolos(ident, 'integer')

def p_lista_ident(p):
    '''lista_ident : IDENTIFICADOR
                   | IDENTIFICADOR VIRGULA lista_ident'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

# Bloco usado internamente (comando composto): NÃO consome PONTOEVIRGULA
def p_bloco(p):
    'bloco : BEGIN lista_comandos END' 
    p[0] = p[2]

# Bloco final do programa: consome o PONTO final
def p_bloco_final(p):
    'bloco_final : BEGIN lista_comandos END PONTO'
    pass # As ações semânticas foram geradas em lista_comandos

def p_lista_comandos(p):
    '''lista_comandos : comando PONTOEVIRGULA lista_comandos
                      | comando
                      | comando PONTOEVIRGULA''' # Permite ';' no último comando antes do END
    pass

def p_comando(p):
    '''comando : atribuicao
               | comando_if
               | comando_while
               | comando_read
               | comando_write
               | bloco'''
    pass

def p_atribuicao(p):
    'atribuicao : IDENTIFICADOR ATRIBUICAO expressao'
    endereco = busca_tabela_simbolos(p[1]) # Verifica se o identificador foi declarado
    # Expressão já gerou código (empilhou o valor)
    print(f"ARMZ {endereco}")

def p_comando_read(p):
    'comando_read : READ ABREPAREN IDENTIFICADOR FECHAPAREN'
    end = busca_tabela_simbolos(p[3]) # Verifica se o identificador foi declarado
    print("LEIT")
    print(f"ARMZ {end}")

def p_comando_write(p):
    'comando_write : WRITE ABREPAREN IDENTIFICADOR FECHAPAREN'
    end = busca_tabela_simbolos(p[3]) # Verifica se o identificador foi declarado
    print(f"CRVL {end}")
    print("IMPR")

def p_comando_if(p):
    '''comando_if : IF expressao THEN comando
                  | IF expressao THEN comando ELSE comando'''
    
    if len(p) == 5:
        # IF sem ELSE
        L1 = proximo_rotulo()
        # Gera o salto condicional
        print(f"DSVF {L1}")
        # Código do comando verdadeiro já gerado ao chamar p[4]
        print(f"{L1}:")  # Rótulo marca fim do bloco IF
    else:
        # IF com ELSE
        L1 = proximo_rotulo()
        L2 = proximo_rotulo()
        # Salta para o bloco falso se condição for falsa
        print(f"DSVF {L1}")
        # Código do comando verdadeiro p[4] já gerado
        print(f"DSVS {L2}")
        # Rótulo do início do bloco falso
        print(f"{L1}:")
        # Código do comando falso p[6] já gerado
        print(f"{L2}:")  # Fim do IF

def p_comando_while(p):
    'comando_while : WHILE expressao DO comando'
    
    L1 = proximo_rotulo()  # início do loop
    L2 = proximo_rotulo()  # saída do loop
    
    print(f"{L1}:")       # marca o início do while
    # A condição já gerou CRVL/CRCT + comparação
    print(f"DSVF {L2}")
    # Corpo do loop (p[4]) já gerou seu código MEPA
    print(f"DSVS {L1}")   # volta para início do while
    print(f"{L2}:")       # marca saída do loop

# expressao -> chama expressao_relacional
def p_expressao(p):
    'expressao : expressao_relacional'
    pass

def p_expressao_relacional(p):
    '''expressao_relacional : expressao_simples
                            | expressao_simples MENOR expressao_simples
                            | expressao_simples MENORIGUAL expressao_simples
                            | expressao_simples MAIOR expressao_simples
                            | expressao_simples MAIORIGUAL expressao_simples
                            | expressao_simples IGUAL expressao_simples
                            | expressao_simples DIFERENTE expressao_simples'''
    if len(p) == 4:
        # Comparações imprimem a instrução MEPA correspondente
        if p[2] == '<':
            print("CMME")
        elif p[2] == '<=':
            print("CMEG")
        elif p[2] == '>':
            print("CMMA")
        elif p[2] == '>=':
            print("CMAG")
        elif p[2] == '=':
            print("CMIG")
        elif p[2] == '<>':
            print("CMDG")

def p_expressao_simples(p):
    '''expressao_simples : termo
                         | expressao_simples SOMA termo
                         | expressao_simples SUB termo'''
    if len(p) == 4:
        if p[2] == '+':
            print("SOMA")
        else:
            print("SUBT")

def p_termo(p):
    '''termo : fator
             | termo MUL fator
             | termo DIVISAO fator'''
    if len(p) == 4:
        if p[2] == '*':
            print("MULT")
        else:
            print("DIVI")

def p_fator(p):
    '''fator : IDENTIFICADOR
             | NUMERO
             | ABREPAREN expressao FECHAPAREN'''
    if len(p) == 2:
        if isinstance(p[1], int):
            print(f"CRCT {p[1]}") # Constante (número)
        else:
            end = busca_tabela_simbolos(p[1]) # Variável (identificador)
            print(f"CRVL {end}")
    else:
        # (expressao) - a expressão já gerou o código de empilhamento
        pass

def p_error(p):
    if p:
        # Se for um erro sintático, lança exceção para finalizar a execução
        # Adicionando o número da linha para melhor rastreio
        raise SystemExit(f"Erro sintático em '{p.value}' na linha {p.lineno}")
    else:
        raise SystemExit("Erro sintático no final do arquivo")

# -------------------------
# Construção do lexer e parser
# -------------------------
lexer = lex.lex()
# Ignora avisos de conflitos S/R que não impedem a análise
parser = yacc.yacc(errorlog=yacc.NullLogger())

# -------------------------
# Programa de teste
# -------------------------
programa_teste = """
program exemplo1;
var fat, num, cont: integer;
begin
    read(num);
    fat := 1;
    cont := 2;
    while cont <= num do
    begin
        fat := fat * cont;
        cont := cont + 1; 
    end;
    write(fat);
end.
"""

if __name__ == '__main__':
    # Reinicia o estado para garantir a saída correta
    tabela_simbolos.clear()
    proximo_endereco = 0
    rotulo_contador = 0

    print("--- Saída MEPA Gerada ---")
    try:
        parser.parse(programa_teste, lexer=lexer)
        print("--- Análise Concluída com Sucesso ---")
    except SystemExit as e:
        print(f"\nERRO: {e}")
        sys.exit(1)