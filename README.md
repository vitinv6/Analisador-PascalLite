# Analisador Léxico e Sintático para a Linguagem PascalLite

![Python](https://img.shields.io/badge/Python-3.x-blue.svg) ![PLY](https://img.shields.io/badge/Framework-PLY-green.svg)

## 📖 Sobre o Projeto

Este repositório contém a implementação da primeira fase de um compilador — **análise léxica e sintática** — para uma linguagem educacional chamada **PascalLite**. O projeto foi desenvolvido como parte da disciplina de Compiladores e tem como objetivo aplicar os conceitos teóricos de reconhecimento de linguagens de programação.

O programa, escrito em Python com o auxílio da biblioteca PLY (Python Lex-Yacc), é capaz de:
1.  Ler um código-fonte escrito em PascalLite.
2.  Realizar a **análise léxica** para converter o texto em uma sequência de *tokens* (átomos).
3.  Executar a **análise sintática** para validar se a estrutura do programa está de acordo com a gramática formal da linguagem.
4.  Reportar erros léxicos (caracteres inválidos) e sintáticos (estrutura incorreta), indicando a linha do problema.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3
* **Biblioteca:** [PLY (Python Lex-Yacc)](https://www.dabeaz.com/ply/ply.html) - Uma biblioteca popular em Python para a criação de analisadores léxicos e sintáticos.

---

## ✨ Funcionalidades Implementadas

O analisador implementa todas as regras especificadas para a linguagem PascalLite, incluindo:

* **Análise Léxica:**
    * Reconhecimento de palavras-chave (`program`, `var`, `if`, `while`, etc.).
    * Validação de identificadores (iniciando com letra ou `_`, com tamanho máximo de 20 caracteres).
    * Reconhecimento de números inteiros.
    * Identificação de operadores aritméticos, relacionais e lógicos.
    * Suporte a três tipos de comentários: `// (linha)`, `(* ... *) (bloco)` e `{ ... } (bloco)`, que são corretamente ignorados.

* **Análise Sintática:**
    * Validação da estrutura completa de um programa, incluindo cabeçalho, bloco de declaração de variáveis (`var`) e bloco de comandos (`begin...end.`).
    * Reconhecimento de comandos de atribuição, `if-then-else`, `while-do`, `read` e `write`.
    * Análise de expressões aritméticas e lógicas com tratamento de precedência de operadores.

---

## 🚀 Como Executar

Para testar o analisador, siga os passos abaixo:

1.  **Pré-requisitos:**
    * Certifique-se de ter o Python 3 instalado.
    * Instale a biblioteca PLY:
        ```bash
        pip install ply
        ```

2.  **Clone o repositório:**
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO]
    cd [NOME_DA_PASTA_DO_REPOSITORIO]
    ```

3.  **Execute o script:**
    ```bash
    python pascal_lite_analyzer.py
    ```

O script principal (`pascal_lite_analyzer.py`) já contém três exemplos de código embutidos: um sintaticamente correto, um com erro sintático e um com erro léxico. A saída no terminal mostrará o resultado da análise para cada um deles.

---
O script principal (pascal_lite_analyzer.py) já contém três exemplos de código embutidos: um sintaticamente correto, um com erro sintático e um com erro léxico. A saída no terminal mostrará o resultado da análise para cada um deles.
