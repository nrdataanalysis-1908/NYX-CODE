# Especificação da linguagem NYX

Versão da especificação: 0.7
Estado: alfa — frontend próprio e interpretador tree-walk.

## 1. Identidade e objetivo

NYX significa Numerical Yield eXchange. É uma linguagem de programação independente, concebida para computação científica, engenharia de dados, automação e interoperabilidade.

A implementação atual possui lexer, parser recursivo descendente, AST e interpretador próprios. Python é a tecnologia hospedeira do protótipo; não define a sintaxe nem a semântica da linguagem.

## 2. Código-fonte

- Extensão: `.nyx`; codificação UTF-8 com ou sem BOM.
- Comentários de linha começam com `#`.
- Strings usam aspas duplas e não podem atravessar linhas.
- Escapes: `\\n`, `\\t`, `\\"` e `\\\\`.
- Instruções simples terminam com `;`, quebra de linha, `}` ou EOF, conforme o contexto.
- Blocos são delimitados por `{` e `}`.

## 3. Tipos e valores

| Tipo | Exemplos |
|---|---|
| Integer | `0`, `42` |
| Float | `3.14` |
| String | `"NYX"` |
| Boolean | `true`, `false` |
| Null | `null` |

Inteiros usam precisão arbitrária na implementação hospedeira. Float utiliza ponto flutuante binário de dupla precisão.

## 4. Variáveis e saída

```nyx
let samples = 120
let ratio = 0.875
let title = "NYX"
samples = samples + 1
print(title)
print(samples * ratio)
```

`let nome = expressão` declara no escopo atual. Não se admite redeclaração no mesmo escopo. A atribuição atualiza a declaração visível mais próxima. `print(expressão)` envia o valor ao mecanismo de saída.

## 5. Expressões e operadores

Precedência crescente: `or`; `and`; `== !=`; comparações; `+ -`; `* / %`; unários `not + -`; chamadas e primários.

- Aritmética e comparação exigem operandos numéricos.
- `and`, `or` e `not` exigem Boolean; `and` e `or` usam curto-circuito.
- Igualdade compara tipo e valor.
- Divisão e módulo por zero geram erro.
- `!` isolado não é aceito; use `not`.

## 6. Controle de fluxo

```nyx
if (temperature > 30) {
    print("high")
} else {
    print("normal")
}

let index = 0
while (index < 3) {
    print(index)
    index = index + 1
}
```

Condições precisam resultar em Boolean. Cada bloco cria escopo local; identificadores são resolvidos do escopo mais interno para o mais externo.

## 7. Funções

Funções são declaradas com `fn`, recebem parâmetros posicionais e podem devolver um valor com `return`.

```nyx
fn calcular_media(a, b) {
    return (a + b) / 2
}

let resultado = calcular_media(10, 20)
print(resultado)
```

Funções podem não receber parâmetros. Uma função que termina sem executar `return` devolve `null`. `return` sem expressão também devolve `null`. A quantidade de argumentos deve corresponder à quantidade de parâmetros.

A resolução de nomes é léxica: uma função conserva acesso aos escopos existentes quando foi declarada. Chamadas criam um escopo de parâmetros isolado. Recursividade e chamadas entre funções são suportadas.

Exemplo recursivo:

```nyx
fn factorial(n) {
    if (n <= 1) {
        return 1
    }
    return n * factorial(n - 1)
}

print(factorial(6))
```

Não há ainda parâmetros nomeados, valores padrão, sobrecarga, funções anônimas, closures mutáveis especificadas como recurso de primeira classe ou funções nativas definidas pelo usuário.

## 8. Coleções e listas

A NYX possui o tipo nativo mutável `List`. Listas podem ser vazias, heterogêneas e aninhadas.

```nyx
let samples = [12, 18, 24]
let matrix = [[1, 2], [3, 4]]
let mixed = ["NYX", 0.6, true, null]

print(samples[0])
samples[1] = 20
append(samples, 30)
print(len(samples))
print(matrix[1][0])
```

- Os índices são inteiros e começam em zero.
- Índices negativos, fracionários, booleanos ou fora dos limites geram erro de execução.
- A leitura usa `lista[indice]`; a atribuição usa `lista[indice] = valor`.
- `len(lista)` devolve a quantidade de elementos.
- `append(lista, valor)` acrescenta um elemento ao final e devolve `null`.
- Listas são mutáveis e atribuídas por referência: duas variáveis que recebem a mesma lista observam as mesmas alterações.
- Passar uma lista a uma função preserva essa identidade compartilhada.
- A igualdade entre listas é estrutural e recursiva; valores escalares continuam exigindo igualdade de tipo e valor.
- Listas ainda não possuem slicing, remoção, ordenação, compreensão, operações vetorizadas.

## 9. Iteração e agregações numéricas

O comando `for` percorre os elementos de uma lista, na ordem em que aparecem:

```nyx
let measurements = [18.2, 19.1, 20.4]

for (let measurement in measurements) {
    print(measurement)
}

print(sum(measurements))
print(mean(measurements))
print(min(measurements))
print(max(measurements))
```

A expressão iterável é avaliada uma única vez e deve resultar em `List`. A iteração percorre, na ordem original, um retrato dos elementos existentes no início do laço; acréscimos posteriores à lista não ampliam a iteração em andamento. A variável declarada por `let` existe somente no escopo do laço; cada execução do bloco do laço conserva seu próprio escopo interno. Listas vazias não executam o corpo.

As funções nativas de agregação recebem exatamente uma lista:
- `sum(lista)`: soma os elementos; para lista vazia, devolve `0`.
- `mean(lista)`: média aritmética; exige lista não vazia e devolve `Float`.
- `min(lista)` e `max(lista)`: menor e maior elemento; exigem lista não vazia.
- Todas exigem elementos exclusivamente `Integer` ou `Float`; `Boolean` não é aceito como número.
- Valores não numéricos e argumentos que não sejam listas geram erro de execução com localização.

Ainda não existem `break`, `continue`, iteração sobre outros tipos de coleção ou iteradores definidos pelo usuário.

## 10. Gramática (EBNF)

```ebnf
program          = { statement } , EOF ;
statement        = function_decl | declaration | assignment | print_stmt
                 | expression_stmt | return_stmt | if_stmt | while_stmt | for_stmt | block ;
function_decl    = "fn" , identifier , "(" , [ parameters ] , ")" , block ;
parameters       = identifier , { "," , identifier } ;
arguments        = expression , { "," , expression } ;
declaration      = "let" , identifier , "=" , expression , terminator ;
assignment       = ( identifier | indexed_target ) , "=" , expression , terminator ;
indexed_target   = identifier , { "[" , expression , "]" } ;
expression_stmt  = call , terminator ;
print_stmt       = "print" , "(" , expression , ")" , terminator ;
return_stmt      = "return" , [ expression ] , terminator ;
if_stmt          = "if" , "(" , expression , ")" , block , [ "else" , block ] ;
while_stmt       = "while" , "(" , expression , ")" , block ;
for_stmt         = "for" , "(" , "let" , identifier , "in" , expression , ")" , block ;
block            = "{" , { statement } , "}" ;
terminator       = ";" | line_terminator | "}" | EOF ;
expression       = logical_or ;
logical_or       = logical_and , { "or" , logical_and } ;
logical_and      = equality , { "and" , equality } ;
equality         = comparison , { ( "==" | "!=" ) , comparison } ;
comparison       = term , { ( "<" | "<=" | ">" | ">=" ) , term } ;
term             = factor , { ( "+" | "-" ) , factor } ;
factor           = unary , { ( "*" | "/" | "%" ) , unary } ;
unary            = ( "not" | "+" | "-" ) , unary | call ;
call             = primary , { "(" , [ arguments ] , ")" | "[" , expression , "]" } ;
primary          = number | string | "true" | "false" | "null"
                 | identifier | list_literal | "(" , expression , ")" ;
list_literal     = "[" , [ expression , { "," , expression } , [ "," ] ] , "]" ;
```

`line_terminator` é uma condição do parser baseada nas posições de linha dos tokens, não um token léxico independente.

## 11. Pipeline e diagnósticos

O pipeline atual é: código-fonte → lexer → tokens → parser → AST → interpretador tree-walk. Erros léxicos, sintáticos e de execução identificam linha e coluna no formato `[NYX:Lx:Cy]`. O primeiro erro interrompe a execução.

## 12. Limitações explícitas

Ainda não implementados: módulos/imports, sistema de tipos estático, inferência, genéricos, classes/traits, `break`, `continue`, slicing e operações avançadas de coleções, exceções da linguagem, análise semântica estática, IR, compilador, bytecode/VM, concorrência, paralelismo, gerenciamento próprio de memória, bibliotecas científicas, engine tabular e integrações nativas de IA.

Esses itens são planejamento, não capacidades atuais.

## 13. Evolução

A sintaxe, a semântica e os testes de conformidade pertencem à NYX e devem permanecer independentes da tecnologia hospedeira. A evolução separará linguagem, runtime, bibliotecas científicas e integrações externas.
