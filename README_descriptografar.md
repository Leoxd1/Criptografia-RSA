# RSA do zero — Script de descriptografia (`rsa_descriptografar.py`)

Segunda metade do projeto: recebe a **chave privada** e a **mensagem criptografada** produzidas pelo `rsa_criptografar.py` e recupera o texto original. Assim como no outro script, **nenhuma função pronta de criptografia** é utilizada. Requer Python 3.7 ou superior.

## Como executar

```bash
python3 rsa_descriptografar.py
```

O script pergunta dois caminhos (Enter aceita o padrão entre colchetes):

```
Arquivo da chave privada [chave_privada.txt]:
Arquivo da mensagem criptografada [mensagem_criptografada.txt]:
```

e imprime a mensagem descriptografada. Os caminhos podem ter espaços e podem vir entre aspas (como quando se arrasta o arquivo para o terminal).

**Código de saída:** `0` sucesso, `1` erro (mensagem em `stderr` começando com `Erro:`), `130` cancelado com Ctrl+C. Nenhuma mensagem é impressa quando há erro.

### Formato dos arquivos de entrada

`chave_privada.txt`:
```
expoente=<d>
modulo=<n>
```

`mensagem_criptografada.txt`: um número inteiro por linha, cada um sendo um bloco cifrado.

Os arquivos são lidos em UTF-8. São tolerados: marca BOM do Windows, quebras de linha CRLF, espaços em volta do `=` e dos números, linhas em branco e os dois campos da chave em qualquer ordem.

## O que é usado da linguagem

- `bytes.decode("utf-8")`: converte bytes em texto (decodificação, não criptografia).
- `sys`: entrada/saída padrão e código de saída.
- `input`/`print`, `open`, operadores aritméticos.
- **Não** usa `pow(a, b, m)` nem qualquer biblioteca de criptografia. O único módulo importado é `sys`.

## Matemática por trás

Com a chave privada **(d, n)**, cada bloco cifrado **c** é decifrado por:

**m = c^d mod n**

Isso recupera a mensagem original porque, na geração das chaves, `e · d ≡ 1 (mod φ(n))`. Assim:

c^d = (m^e)^d = m^(e·d) = m^(1 + k·φ(n)) ≡ m (mod n)

pelo teorema de Euler (m^φ(n) ≡ 1 mod n).

Continuando o exemplo pequeno do outro README: n = 3233, d = 2753, c = 2790 → 2790²⁷⁵³ mod 3233 = **65**, a mensagem original. (Esse módulo é pequeno demais para os scripts, que exigem pelo menos 32 bits. Ele serve só para entender a conta.)

## Como o script percebe que algo está errado

O RSA em si **não avisa** quando a chave está errada: `c^d mod n` com a chave errada simplesmente dá outro número. Por isso o script verifica a estrutura de cada bloco decifrado. O bloco original tem a forma `prefixo 1` + de 1 a N bytes de mensagem (N = `tamanho_do_bloco_em_bytes(n)`). Então, depois de decifrar, ele confere:

1. O número do bloco cifrado é menor que n (e não negativo).
2. O primeiro byte decifrado é o prefixo `1`.
3. O tamanho está entre 2 bytes e N + 1 bytes.
4. No final, os bytes de todos os blocos juntos formam um texto UTF-8 válido.

Com a chave errada ou um bloco adulterado, o resultado é um número "aleatório" do tamanho de n, que quase nunca cumpre as regras 2 e 3 (a chance é da ordem de 1 em 65 mil por bloco) e, mesmo que cumpra, ainda precisa passar na regra 4. Nos testes, 200 mensagens decifradas com uma chave de outro par e 200 blocos adulterados foram **todos** detectados.

## Fluxo do programa (`main` → `executar`)

1. `perguntar_caminho()` lê os dois caminhos.
2. `ler_chave()` lê e valida `(d, n)`; `ler_mensagem_criptografada()` lê e valida a lista de blocos cifrados.
3. `descriptografar_mensagem()` decifra e verifica cada bloco, junta os bytes e decodifica o texto.
4. Imprime a mensagem.

`main()` envolve tudo em um `try`: se algo previsto der errado, imprime `Erro: ...` e devolve o código de saída, sem traceback.

## Constantes

| Constante | Significado |
|---|---|
| `ARQUIVO_CHAVE_PRIVADA_PADRAO`, `ARQUIVO_MENSAGEM_CRIPTOGRAFADA_PADRAO` | Nomes sugeridos nas perguntas |
| `PREFIXO_DE_BLOCO` | Byte `1` que o outro script coloca na frente de cada bloco |
| `MINIMO_DE_BITS_DO_MODULO`, `MAXIMO_DE_BITS_DO_MODULO` | 32 e 4096: tamanhos de módulo aceitos |
| `MAXIMO_DE_DIGITOS_POR_NUMERO` | 1300 dígitos (um módulo de 4096 bits tem 1234) |
| `TAMANHO_MAXIMO_DO_ARQUIVO_DE_CHAVE_EM_BYTES` | 10.000 bytes |
| `TAMANHO_MAXIMO_DO_ARQUIVO_DA_MENSAGEM_EM_BYTES` | 50.000.000 de bytes |
| `TAMANHO_MAXIMO_DE_UM_CAMINHO` | 1000 caracteres |

Os limites de tamanho existem para que um arquivo infinito ou gigante (como `/dev/zero`) seja recusado em vez de consumir toda a memória: o arquivo é lido só até o limite + 1 caractere.

## Funções

### Erro do programa

- **`ErroRSA`**: exceção própria (herda de `ValueError`). Toda situação prevista que impede o programa de continuar levanta um `ErroRSA` com uma mensagem em português. É ela que o `main` captura.

### Matemática e conversão

- **`exponenciacao_modular(base, expoente, modulo)`**: calcula `base^expoente mod modulo` pelo método *square-and-multiply*. Percorre o expoente bit a bit: se o bit é 1, multiplica o resultado pela base; a cada passo eleva a base ao quadrado. Como tudo é reduzido pelo módulo a cada multiplicação, os números nunca ficam gigantescos. É a mesma função do script de criptografia, aqui usada com o expoente privado `d`. Recusa módulo menor que 1 e expoente negativo.
- **`numero_para_bytes(numero)`**: operação inversa da conversão feita na cifragem. Extrai os "dígitos" do número em base 256 (resto da divisão por 256, depois divisão inteira por 256, repetidamente) e inverte a lista, obtendo os bytes na ordem correta. O número 0 vira `b""`; número negativo é recusado.
- **`tamanho_do_bloco_em_bytes(modulo)`**: mesma conta do outro script (para n de 1024 bits, 126 bytes).
- **`bloco_tem_formato_valido(bloco_com_prefixo, modulo)`**: aplica as regras 2 e 3 da seção anterior.
- **`converter_bytes_para_texto(mensagem_em_bytes)`**: decodifica UTF-8; se falhar, levanta `ErroRSA` explicando as causas prováveis (blocos faltando, fora de ordem ou chave incorreta).

### Leitura dos arquivos

- **`converter_para_inteiro(texto, descricao)`**: aceita **somente** dígitos de 0 a 9 (sem sinal, sem `_`, sem ponto, sem hexadecimal, sem dígitos de outros alfabetos, que o `int()` do Python aceitaria) e no máximo 1300 dígitos. Em caso de erro, diz o que esperava e o que encontrou.
- **`ler_texto_do_arquivo(caminho, descricao, tamanho_maximo_em_bytes)`**: abre o arquivo em UTF-8 (aceitando BOM), lê no máximo o limite + 1 e devolve as linhas. Cada problema vira uma mensagem própria: arquivo inexistente, é uma pasta, sem permissão, não é UTF-8, caminho inválido (por exemplo, com byte nulo), grande demais.
- **`validar_chave(expoente, modulo)`**: o módulo deve ter entre 32 e 4096 bits, ser ímpar (produto de dois primos ímpares) e o expoente deve estar entre 2 e n − 1.
- **`ler_chave(caminho)`**: lê as linhas `nome=valor`, aceitando só `expoente` e `modulo`, sem repetição e sem faltar nenhum, e valida com `validar_chave`.
- **`ler_mensagem_criptografada(caminho)`**: lê um inteiro por linha, ignorando linhas em branco; a mensagem precisa ter pelo menos um bloco. O erro cita o número da linha problemática.

### Descriptografia

- **`descriptografar_bloco(bloco_criptografado, chave_privada)`**: confere `0 ≤ c < n`, aplica `m = c^d mod n`, converte o número em bytes, confere o formato (regras 2 e 3) e **descarta o primeiro byte**. Esse byte é o prefixo `1` que o script de criptografia adicionou para preservar zeros à esquerda; o que sobra é o bloco original exato.
- **`descriptografar_mensagem(blocos_criptografados, chave_privada)`**: decifra todos os blocos, junta os bytes e decodifica o texto. Se um bloco falhar, o erro diz qual (`bloco 3: ...`).

### Terminal

- **`configurar_terminal_para_utf8()`**, **`remover_quebra_de_linha(linha)`**, **`ler_linha(pergunta, tamanho_maximo)`**: iguais às do outro script. Garantem UTF-8 na entrada e na saída (acentos e emojis funcionam mesmo em terminais ASCII) e limitam o tamanho do que é lido.
- **`perguntar_caminho(descricao, caminho_padrao)`**: pergunta um caminho, tira aspas simples ou duplas em volta e usa o padrão se a resposta for vazia.

## Tratamento de erros

| Situação | Mensagem (resumo) |
|---|---|
| Arquivo inexistente | `o arquivo da chave privada não foi encontrado: 'x.txt'` |
| Caminho é uma pasta | `'x' é uma pasta, e não o arquivo da ...` |
| Arquivo binário / não UTF-8 | `... não é um texto UTF-8 válido ...` |
| `/dev/zero` ou arquivo gigante | `... é grande demais para ser a ...` |
| Chave vazia, sem `=`, campo repetido, desconhecido ou faltando | Diz qual linha ou campo |
| Valor não numérico, negativo, decimal, hexadecimal, com `_` | `o valor de 'expoente' na chave deve conter apenas um número inteiro não negativo, mas contém ...` |
| Módulo par, de 1 bit, de menos de 32 bits (exemplos de livro) ou de mais de 4096 | Diz o tamanho encontrado e o aceito |
| Expoente 0, 1 ou maior que o módulo | `o expoente da chave está fora do intervalo válido ...` |
| Mensagem sem nenhum bloco | `o arquivo da mensagem criptografada não tem nenhum bloco` |
| Linha da mensagem com letras, sinal, decimal, número gigante | Diz o número da linha |
| Bloco ≥ módulo (ou 0, ou 1) | `bloco N: ...` a chave não corresponde à mensagem |
| Chave errada, chave pública no lugar da privada ou bloco adulterado | `bloco N: o bloco não pôde ser decifrado: a chave privada não corresponde à mensagem, ou o arquivo foi alterado` |
| Bytes decifrados que não são UTF-8 | `o resultado não é um texto UTF-8 válido: faltam blocos, ...` |
| Entrada encerrada (Ctrl+D) | `a entrada foi encerrada antes de a pergunta ser respondida` |
| Ctrl+C | `Erro: operação cancelada pelo usuário.` (código 130) |

Exemplo:

```
Arquivo da chave privada [chave_privada.txt]: outra.txt
Arquivo da mensagem criptografada [mensagem_criptografada.txt]:
Erro: o arquivo da chave privada não foi encontrado: 'outra.txt'.
```

## Bugs encontrados pela bateria de testes e como foram corrigidos

Antes das correções, **41 dos 65 testes falhavam** (149 casos individuais). Os principais, do lado da descriptografia:

| Problema encontrado | Efeito antes | Correção |
|---|---|---|
| Chave errada, chave pública no lugar da privada ou bloco adulterado | `UnicodeDecodeError` (traceback), ou texto sem sentido | Verificação do formato de cada bloco decifrado |
| Blocos `0`, `1`, negativos ou ≥ módulo | Resultado vazio **sem aviso** | Validação do intervalo e do formato |
| Chave com módulo 1, expoente 0 ou negativo | Terminava com sucesso e mensagem vazia ou errada | `validar_chave` |
| Arquivo inexistente, pasta, vazio, binário, sem `=`, com campo faltando, valor não numérico | Traceback (`FileNotFoundError`, `KeyError`, `ValueError`...) | Mensagens claras |
| Chave com BOM, espaços em volta do `=` ou linhas em branco | Falhava (`KeyError`, `ValueError`) | Leitura tolerante |
| Mensagem com BOM | `ValueError` | Leitura com `utf-8-sig` |
| Valores como `12_34`, `+5`, dígitos de outros alfabetos | Aceitos de forma inconsistente pelo `int()` | `converter_para_inteiro` só aceita 0–9 |
| Arquivo de mensagem vazio | Imprimia `Mensagem descriptografada: ` com código 0 | Erro |
| Caminho entre aspas | `FileNotFoundError` | Aspas removidas |
| `/dev/zero`, caminho com byte nulo ou com nome gigante | Traceback / consumo de memória | Leitura limitada e erro claro |
| Entrada encerrada, Ctrl+C | Traceback | Tratados |
| Terminal ASCII com acentos/emojis | `UnicodeEncodeError` | Saída reconfigurada para UTF-8 |
| `exponenciacao_modular` com módulo 0, negativo ou expoente negativo; `(x, 0, 1)` | `ZeroDivisionError` ou resultado errado em silêncio | Validação |
| `numero_para_bytes` com número negativo | Devolvia `b""` em silêncio | Erro |

## Bateria de testes (`testes_rsa.py`)

O mesmo arquivo testa os dois scripts e deve ficar na mesma pasta deles:

```bash
python3 testes_rsa.py
```

São 65 testes, cerca de 15 segundos, descritos em português na saída. Para rodar só um grupo: `python3 testes_rsa.py TestDescriptografarNaLinhaDeComando`. Requer Linux ou macOS (usa `SIGALRM` e `resource`).

Do lado da descriptografia, ele tenta quebrar o script com:

- **Chaves inválidas (22 variações):** vazia, sem `=`, campos faltando ou repetidos, valores negativos, decimais, hexadecimais, gigantes, módulo par/1/0/pequeno, expoente 0/1/maior que o módulo, arquivo binário.
- **Mensagens inválidas (17 variações):** vazia, texto, letras no meio do número, dois números por linha, negativos, `12_34`, dígitos de outros alfabetos, números gigantes, blocos 0, 1, iguais ou maiores que o módulo.
- **Chave errada, chave pública no lugar da privada, bloco adulterado, bytes decifrados que não são UTF-8.** Em nível de função, 200 mensagens com a chave de outro par e 200 adulterações de blocos: nenhuma pode passar sem erro.
- **Caminhos estranhos:** inexistente, pasta, aspas, espaços, byte nulo, nome com 400 caracteres, `/dev/zero`, `/dev/urandom`.
- **Terminal:** entrada encerrada, Ctrl+C, terminal só ASCII e locale C.
- **Ida e volta pela linha de comando** (criptografar e depois descriptografar) com acentos, emojis, caracteres de controle e 100 KB de texto.

Os testes usam `pow()` e `math.gcd` **apenas como gabarito**; os scripts não usam nada disso.

Resultado atual: **65 de 65 passam** (rodado 3 vezes seguidas).

## Limitações

- Decifra apenas mensagens geradas pelo `rsa_criptografar.py` (mesmo formato de blocos e prefixo). Por isso o exemplo de livro (n = 3233) é recusado.
- **Sem garantia de integridade:** o RSA "de livro" não tem assinatura nem código de autenticação. Se as linhas do arquivo da mensagem forem **trocadas de ordem** ou o **final for cortado**, cada bloco continua decifrando corretamente, então o texto sai embaralhado ou incompleto **sem erro**, a menos que o corte caia no meio de um caractere de vários bytes (aí o erro de UTF-8 aparece). Os testes documentam esse comportamento como limitação conhecida (não pode dar traceback, mas também não é detectado). Em sistemas reais isso é resolvido com assinaturas ou MAC.
- A chave privada é lida de um arquivo em texto puro; em um cenário real ela ficaria protegida (criptografada com senha, em um cofre de chaves ou hardware seguro).
- A exponenciação não é de tempo constante, então não resiste a ataques de canal lateral.
- Velocidade: cerca de 5 ms por bloco com chave de 1024 bits, ou seja, uma mensagem de 1 MB (o máximo da criptografia) leva em torno de 40 segundos para ser decifrada.

## Relação com o script de criptografia

Os dois scripts precisam concordar em três coisas:

| Combinação | Onde está |
|---|---|
| Formato dos arquivos de chave e mensagem | `salvar_chave` / `ler_chave`, `salvar_mensagem_criptografada` / `ler_mensagem_criptografada` |
| Prefixo `1` no início de cada bloco | `criptografar_bloco` / `descriptografar_bloco` |
| Conversão bytes ↔ número em base 256 e tamanho do bloco | `bytes_para_numero` / `numero_para_bytes`, `tamanho_do_bloco_em_bytes` |

As funções repetidas nos dois arquivos (`ErroRSA`, `exponenciacao_modular`, `ler_linha` etc.) são cópias de propósito: cada script funciona sozinho, sem importar o outro.

## Possíveis perguntas do professor

- *Por que descartar o primeiro byte depois de decifrar?* Porque é o prefixo `1` adicionado na cifragem para não perder zeros à esquerda.
- *Por que a decifragem é mais lenta que a cifragem?* Porque o expoente privado `d` tem ~1024 bits, enquanto o público `e = 65537` tem só 17 bits; o número de multiplicações do square-and-multiply cresce com o tamanho do expoente.
- *O que acontece se um bloco cifrado for alterado?* O resultado da decifragem é um número aleatório, que quase sempre falha na verificação do formato do bloco; o script acusa `bloco N: o bloco não pôde ser decifrado...` e não imprime nada.
- *E se usarem a chave de outro par?* O mesmo erro. O RSA em si não detecta chave errada; é a verificação do prefixo, do tamanho e do UTF-8 que detecta.
- *Dá para o script ser enganado?* Reordenar ou remover blocos inteiros não é detectado (limitação do RSA sem assinatura, descrita acima). Alterar o conteúdo de um bloco, trocar a chave, usar arquivos corrompidos ou entradas absurdas (arquivos gigantes, binários, caminhos estranhos) resulta em erro claro.
- *Por que ler o arquivo só até um limite?* Para que um arquivo infinito, como `/dev/zero`, não consuma toda a memória do computador.
