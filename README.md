# 🧠 Compilador Educacional — MicroC e PascalLite (Analisadores Léxico, Sintático e Geração MEPA)

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![PLY](https://img.shields.io/badge/Framework-PLY-green.svg)
![Status](https://img.shields.io/badge/Status-Concluído-success.svg)

---

## 📖 Sobre o Projeto

Este repositório reúne duas fases de um **compilador educacional** desenvolvido em Python, com base na biblioteca **PLY (Python Lex-Yacc)**.  
O objetivo do projeto é aplicar os conceitos teóricos da disciplina **Compiladores**, explorando as etapas de **análise léxica**, **análise sintática** e **geração de código intermediário (MEPA)**.

As fases foram desenvolvidas para linguagens simplificadas de ensino:

- **Fase 1:** Implementa um analisador léxico e sintático completo para a linguagem **MicroC**, uma versão reduzida e didática de C.  
- **Fase 2:** Gera **código MEPA** a partir de programas escritos em **PascalLite**, uma versão simplificada da linguagem Pascal.

---

## 🧩 Estrutura do Repositório

| Arquivo | Descrição |
|----------|------------|
| `fase1_pascalite_parser.py` | Implementa o analisador **léxico e sintático para MicroC**, incluindo a geração da árvore sintática e detecção de erros. |
| `fase2_pascalite_mepa.py` | Implementa o analisador **léxico, sintático e gerador de código MEPA** para PascalLite. Inclui manipulação de tabela de símbolos e geração de rótulos. |

---

## 🧠 Fase 1 — Analisador MicroC

A **fase 1** realiza:
1. **Análise Léxica:** reconhece tokens, palavras reservadas, identificadores, números e operadores da linguagem MicroC.
2. **Análise Sintática:** valida a estrutura do código conforme a gramática da linguagem.
3. **Geração de Árvore Sintática:** mostra a hierarquia dos elementos reconhecidos.
4. **Tratamento de Erros:** identifica erros léxicos (caracteres inválidos) e sintáticos (estrutura incorreta), indicando a linha de ocorrência.

### 📋 Principais Funcionalidades
- Suporte a comandos `if`, `else`, `while`, `read`, `write`.
- Suporte a expressões aritméticas e lógicas com operadores `+`, `-`, `*`, `/`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `&&`, `||`, `!`.
- Identificação de identificadores com limite de 20 caracteres.
- Comentários de linha (`//`) e bloco (`/* ... */`).

### 🚀 Como Executar
```bash
pip install ply
python fase1_pascalite_parser.py
