# RSA do zero — Script de criptografia (`rsa_criptografar.py`)

Implementação didática do RSA em Python, **sem nenhuma biblioteca ou função pronta de criptografia**. Todo o processo (testar primos, gerar chaves, elevar a potência com módulo, cifrar) está escrito no próprio arquivo. Requer Python 3.7 ou superior.

## Como executar

```bash
python3 rsa_criptografar.py
```

O script pede a mensagem (uma linha, terminada com Enter) e gera três arquivos **na pasta de onde o comando foi executado**:

| Arquivo | Conteúdo |
|---|---|
| `chave_publica.txt` | `expoente` (e) e `modulo` (n) |
| `chave_privada.txt` | `expoente` (d) e `modulo` (n) |
| `mensagem_criptografada.txt` | Um número por linha (um por bloco da mensagem) |

Para decifrar, use o `rsa_descriptografar.py` com `chave_privada.txt` e `mensagem_criptografada.txt`.

Se esses arquivos já existirem, o script **pergunta antes de sobrescrever**, porque apagar a chave privada antiga impede ler mensagens cifradas com ela. Só `s` ou `sim` continua; qualquer outra resposta cancela sem alterar nada.

**Código de saída:** `0` sucesso, `1` erro (mensagem em `stderr` começando com `Erro:`), `130` cancelado com Ctrl+C.

## O que é usado da linguagem

- `random`: apenas para sortear números candidatos a primo (não é um módulo de criptografia).
- `os.path.exists`: só para saber se os arquivos de saída já existem.
- `sys`: entrada/saída padrão e código de saída.
- `str.encode("utf-8")`: transforma o texto em bytes (é codificação de texto, não criptografia).
- `input`/`print`/`open`, `range`, `len`, operadores aritméticos.
- **Não** usa `pow(a, b, m)`, `hashlib`, `secrets`, `cryptography` nem equivalentes. A exponenciação modular e o inverso modular foram implementados à mão.

## Matemática por trás

1. Escolhe-se dois primos grandes e distintos, **p** e **q**.
2. **n = p · q** (o módulo, parte das duas chaves).
3. **φ(n) = (p − 1) · (q − 1)** (função totiente de Euler).
4. Escolhe-se **e** com 1 < e < φ(n) e mdc(e, φ(n)) = 1. Aqui, `e = 65537`, valor padrão da prática.
5. Calcula-se **d** tal que **e · d ≡ 1 (mod φ(n))**, o inverso modular de e.

- Chave pública: **(e, n)**
- Chave privada: **(d, n)**
- Cifrar: **c = m^e mod n**
- Decifrar: **m = c^d mod n**

**Por que funciona?** Como e·d = 1 + k·φ(n), então m^(e·d) = m · (m^φ(n))^k. Pelo teorema de Euler, m^φ(n) ≡ 1 (mod n), logo m^(e·d) ≡ m (mod n).

**Por que é seguro (em teoria)?** Para obter d é preciso conhecer φ(n), o que exige fatorar n em p e q. Com n de centenas de dígitos, isso é inviável computacionalmente.

### Exemplo pequeno (para a apresentação)

p = 61, q = 53 → n = 3233, φ = 3120, e = 17, d = 2753.
Mensagem m = 65 → c = 65¹⁷ mod 3233 = **2790**.
Decifrando: 2790²⁷⁵³ mod 3233 = **65**.

Este exemplo é só para entender a conta. Os scripts **não** o aceitam, porque exigem módulo de pelo menos 32 bits (veja "Tratamento de erros").

## Fluxo do programa (`main` → `executar`)

1. `validar_configuracao()` confere as constantes do topo do arquivo.
2. `confirmar_sobrescrita_se_necessario()` pergunta se podem ser sobrescritos arquivos de uma execução anterior.
3. `ler_mensagem_digitada()` lê a mensagem e já a valida (vazia, UTF-8, tamanho), **antes** de gastar tempo gerando chaves.
4. `gerar_chaves()` cria o par de chaves.
5. `criptografar_mensagem()` converte a mensagem em blocos numéricos e cifra cada um.
6. Salva as chaves e os blocos cifrados em arquivos e imprime um resumo.

`main()` envolve tudo em um `try`: se algo previsto der errado, imprime `Erro: ...` e devolve o código de saída, sem mostrar traceback.

## Constantes

| Constante | Significado |
|---|---|
| `TAMANHO_CHAVE_EM_BITS` | Tamanho de n em bits (1024). Deve ser inteiro, **par**, entre `MINIMO_DE_BITS_DA_CHAVE` e `MAXIMO_DE_BITS_DA_CHAVE` |
| `MINIMO_DE_BITS_DA_CHAVE` / `MAXIMO_DE_BITS_DA_CHAVE` | 32 e 4096. Abaixo de 32 bits não cabe um bloco útil; acima de 4096 a geração leva minutos |
| `EXPOENTE_PUBLICO` | Valor de e (65537). Deve ser inteiro, **ímpar** e ≥ 3 |
| `RODADAS_MILLER_RABIN` | Quantidade de testemunhas no teste de primalidade (40) |
| `PRIMOS_PEQUENOS` | Lista usada para descartar rapidamente candidatos divisíveis por primos pequenos |
| `PREFIXO_DE_BLOCO` | Byte `1` colocado na frente de cada bloco (explicado abaixo) |
| `TAMANHO_MAXIMO_DA_MENSAGEM_EM_BYTES` | Limite da mensagem: 1.000.000 de bytes |
| `TAMANHO_MAXIMO_DA_RESPOSTA_DE_CONFIRMACAO` | Limite de caracteres da resposta "s/N" (100) |
| `ARQUIVO_CHAVE_PUBLICA`, `ARQUIVO_CHAVE_PRIVADA`, `ARQUIVO_MENSAGEM_CRIPTOGRAFADA`, `ARQUIVOS_DE_SAIDA` | Nomes dos arquivos gerados e a lista deles |

## Funções

### Erro do programa

- **`ErroRSA`**: exceção própria (herda de `ValueError`). Toda situação prevista que impede o programa de continuar levanta um `ErroRSA` com uma mensagem em português. É ela que o `main` captura.

### Matemática básica

- **`exponenciacao_modular(base, expoente, modulo)`**: calcula `base^expoente mod modulo` pelo método *square-and-multiply*. Em vez de calcular a potência gigante e só depois tirar o módulo, percorre o expoente bit a bit: se o bit é 1, multiplica o resultado pela base; a cada passo eleva a base ao quadrado. Todas as multiplicações já são reduzidas pelo módulo, então os números nunca crescem demais. É o coração do RSA. Recusa módulo menor que 1 e expoente negativo. O resultado inicial é `1 % modulo` (e não `1`) para que o caso `modulo = 1` dê 0, como na matemática.
- **`maximo_divisor_comum(a, b)`**: algoritmo de Euclides, sobre os valores absolutos. Usado para garantir que `e` e `φ(n)` são coprimos.
- **`inverso_modular(numero, modulo)`**: algoritmo de Euclides estendido. Encontra `d` tal que `numero · d ≡ 1 (mod modulo)`. No fim do algoritmo, `resto_anterior` é o mdc; se ele não for 1, **não existe inverso** e a função levanta `ErroRSA` (antes, devolvia um número errado sem avisar).

### Geração de primos

- **`passa_no_teste_de_miller_rabin(candidato)`**: teste probabilístico de primalidade. Escreve `candidato − 1 = 2^s · t` (t ímpar). Para cada testemunha aleatória `a`, calcula `a^t mod candidato`. Se der 1 ou `candidato − 1`, passa na rodada. Senão, eleva ao quadrado até `s − 1` vezes procurando `candidato − 1`; se nunca aparecer, o número é composto com certeza. Um composto passa em uma rodada com probabilidade ≤ 1/4; com 40 rodadas, o erro é desprezível (≤ 4⁻⁴⁰).
- **`eh_primo(candidato)`**: devolve `False` para números menores que 2; depois tenta dividir por primos pequenos (descarta a maioria dos candidatos barato); os que sobram vão para o Miller-Rabin.
- **`gerar_numero_primo(tamanho_em_bits)`**: sorteia números com o tamanho desejado até achar um primo. Força o bit menos significativo a 1 (para ser ímpar) e os **dois bits mais altos** a 1, garantindo que p · q tenha exatamente o tamanho de chave pedido. Exige pelo menos 3 bits.

### Configuração e chaves

- **`eh_inteiro(valor)`**: `True` só para inteiros de verdade (em Python, `True` e `False` contam como `int`, e aqui não queremos isso).
- **`validar_configuracao()`**: confere `TAMANHO_CHAVE_EM_BITS` (inteiro, par, entre 32 e 4096) e `EXPOENTE_PUBLICO` (inteiro, ímpar, ≥ 3 e bem menor que φ(n)). Cada erro cita o nome da constante problemática.
- **`par_de_chaves_funciona(chave_publica, chave_privada)`**: teste de sanidade. Cifra e decifra três números de teste (2, n/3 e n − 2) e confere se voltam iguais.
- **`gerar_chaves()`**: valida a configuração, gera p e q (metade dos bits cada), rejeita p = q e rejeita o par se `mdc(e, φ) ≠ 1`. Calcula n, φ e d, confere o par com `par_de_chaves_funciona` e devolve `(chave_publica, chave_privada)`, cada uma como tupla `(expoente, modulo)`.

### Mensagem → números

O RSA só cifra **números menores que n**. Uma mensagem de texto é grande demais para virar um único número, então ela é dividida em blocos:

- **`converter_mensagem_para_bytes(mensagem)`**: recusa mensagem vazia, com caracteres que não existem em UTF-8 (por exemplo, "surrogates" soltos) ou acima do limite de tamanho; devolve os bytes UTF-8.
- **`bytes_para_numero(dados)`**: trata os bytes como dígitos de um número em base 256 (`numero = numero * 256 + byte`).
- **`tamanho_do_bloco_em_bytes(modulo)`**: quantos bytes de mensagem cabem em um bloco, garantindo que (prefixo + bloco) seja menor que n. Para n de 1024 bits, são 126 bytes. Recusa módulos tão pequenos que não cabe nem 1 byte.
- **`dividir_em_blocos(dados, tamanho_do_bloco)`**: fatia os bytes da mensagem; recusa tamanho de bloco menor que 1.
- **`criptografar_bloco(bloco, chave_publica)`**: coloca o prefixo `1` na frente do bloco, converte em número e aplica `c = m^e mod n`.
- **`criptografar_mensagem(mensagem, chave_publica)`**: valida e codifica o texto em UTF-8, divide em blocos e cifra cada um, devolvendo a lista de números cifrados.

**Por que o prefixo `1`?** Ao converter bytes em número, zeros à esquerda desaparecem (`00 41` e `41` viram o mesmo número). Com um byte `1` na frente, o bloco nunca começa com zero, e na decifragem basta descartar esse primeiro byte para recuperar o bloco exato. Além disso, o prefixo faz todo número `m` a ser cifrado ser ≥ 256, o que ajuda a garantir que `m^e` seja bem maior que `n` (sem nenhuma redução módulo n, a cifra poderia ser desfeita só tirando uma raiz inteira).

### Arquivos e terminal

- **`gravar_arquivo_de_texto(caminho, linhas)`**: grava uma linha por item. Se o sistema recusar (pasta sem permissão, disco cheio, já existe uma pasta com esse nome...), levanta `ErroRSA` com o motivo.
- **`salvar_chave(...)`** e **`salvar_mensagem_criptografada(...)`**: montam o conteúdo e chamam a função acima.
- **`configurar_terminal_para_utf8()`**: força entrada e saída em UTF-8. Sem isso, em terminais configurados em ASCII ou outra codificação (comum em alguns Windows e containers), acentos e emojis derrubariam o programa.
- **`remover_quebra_de_linha(linha)`**: tira o `\n` e o `\r` do final.
- **`ler_linha(pergunta, tamanho_maximo)`**: mostra a pergunta e lê **no máximo** `tamanho_maximo` caracteres. Isso impede que uma entrada gigante sem quebra de linha (por exemplo, um arquivo enorme redirecionado) consuma toda a memória. Levanta `ErroRSA` se a entrada acabar (Ctrl+D), se não for UTF-8 válido ou se passar do limite.
- **`ler_mensagem_digitada()`**: lê a mensagem e já a valida.
- **`confirmar_sobrescrita_se_necessario()`**: a pergunta `[s/N]` descrita no início.

## Tratamento de erros

Situações previstas viram `ErroRSA`; o `main` as imprime como `Erro: <mensagem>.` em `stderr` e termina com código 1. Qualquer outra exceção seria um bug do próprio programa e continuaria aparecendo como traceback (de propósito: esconder um bug real seria pior).

| Situação | Comportamento |
|---|---|
| Mensagem vazia (só Enter) | `Erro: a mensagem não pode ser vazia.` Nada é gravado |
| Mensagem só com espaços | Aceita (é uma mensagem válida) |
| Mensagem acima de 1.000.000 de bytes | Recusada, sem ler o resto da entrada |
| Bytes que não são UTF-8 na entrada | `Erro: o texto digitado não é UTF-8 válido.` |
| Entrada encerrada (Ctrl+D) | Erro claro, nada é gravado |
| Ctrl+C | `Erro: operação cancelada pelo usuário.` (código 130) |
| Arquivos de saída já existem | Pergunta `[s/N]`; só `s`/`sim` continua |
| Não consegue gravar um arquivo | Erro com o nome do arquivo e o motivo do sistema |
| Constante inválida no topo do arquivo | Erro citando a constante (ex.: `TAMANHO_CHAVE_EM_BITS deve ser par...`) |
| Terminal não-UTF-8 | Funciona, porque a entrada e a saída são reconfiguradas para UTF-8 |

## Bugs encontrados pela bateria de testes e como foram corrigidos

Antes das correções, **41 dos 65 testes falhavam** (149 casos individuais). Os principais:

| Problema encontrado | Efeito antes | Correção |
|---|---|---|
| `eh_primo(1)` | **Laço infinito** (e `eh_primo(-1)` dava `ValueError`) | `eh_primo` devolve `False` para números < 2 |
| `EXPOENTE_PUBLICO` par, zero ou enorme | `gerar_chaves` **travava para sempre** (mdc nunca dava 1) | `validar_configuracao` exige ímpar, ≥ 3 e menor que φ |
| `EXPOENTE_PUBLICO = 1` ou negativo | Aceito em silêncio. Com e = 1 o "criptografado" é igual ao texto original | Mesma validação |
| `TAMANHO_CHAVE_EM_BITS` = 0, negativo ou texto | `ValueError`/`TypeError` sem explicação | Validação com mensagem clara |
| `TAMANHO_CHAVE_EM_BITS` enorme (ex.: 1.000.000) | Travava | Limite máximo de 4096 bits |
| `TAMANHO_CHAVE_EM_BITS` ímpar (33, 1025) | Gerava chave de tamanho diferente do pedido | Exige valor par |
| `TAMANHO_CHAVE_EM_BITS` muito pequeno (8, 16) | Com 8 bits travava (só existe um primo possível, então p = q para sempre); com 16 gerava uma chave que não comportava nem 1 byte | Mínimo de 32 bits; `tamanho_do_bloco_em_bytes` também recusa módulos pequenos |
| `exponenciacao_modular(x, 0, 1)` | Devolvia 1 (o correto é 0) | `resultado = 1 % modulo` |
| `exponenciacao_modular` com módulo 0, módulo negativo ou expoente negativo | `ZeroDivisionError` ou resultado errado em silêncio | Recusa os argumentos inválidos |
| `inverso_modular` sem inverso | Devolvia um número errado em silêncio | Levanta `ErroRSA` |
| `maximo_divisor_comum` com negativos | Podia devolver mdc negativo | Usa valores absolutos |
| `gerar_numero_primo` com menos de 3 bits | `ValueError` obscuro | Mensagem clara |
| `dividir_em_blocos` com tamanho 0 ou negativo | `ValueError` obscuro (0) ou lista vazia em silêncio (negativo) | Recusa |
| Par de chaves inconsistente | Nunca era detectado | `par_de_chaves_funciona` |
| Mensagem vazia | Avisava, mas terminava com código 0 | Erro real, código 1 |
| Entrada encerrada, Ctrl+C, bytes não UTF-8, terminal ASCII | Traceback | Tratados |
| Falha ao gravar arquivo | Traceback | Erro claro com o motivo |
| Rodar de novo na mesma pasta | **Sobrescrevia a chave privada antiga sem avisar** | Pergunta antes |
| Entrada gigante sem quebra de linha | Estourava a memória | Leitura limitada |
| Caractere inválido em UTF-8 (ex.: `\udc80`) | `UnicodeEncodeError` | Erro claro |

## Bateria de testes (`testes_rsa.py`)

Um único arquivo testa os **dois** scripts e deve ficar na mesma pasta deles:

```bash
python3 testes_rsa.py
```

São 65 testes e levam cerca de 15 segundos. Para rodar só um grupo: `python3 testes_rsa.py TestMatematica`. Cada teste é descrito em português na saída. Requer Linux ou macOS (usa `SIGALRM` para detectar travamentos e `resource` para limitar memória).

O que a bateria tenta fazer para quebrar o script:

- **Matemática:** compara `exponenciacao_modular`, `inverso_modular` e `maximo_divisor_comum` com `pow()` e `math.gcd` em casos aleatórios e de borda; compara `eh_primo` com um crivo de Eratóstenes até 30000; testa números de Carmichael, pseudoprimos fortes, primos de Mersenne e compostos gigantes.
- **Chaves:** módulo com exatamente N bits, par que decifra o que cifra, chaves diferentes a cada execução, constantes inválidas (tipos errados, valores extremos).
- **Blocos e mensagens:** ida e volta com tamanhos em volta do limite de cada bloco (UTF-8 de 1 a 4 bytes, para cortar caracteres no meio), 13 tamanhos de chave, mensagens com NUL, emojis, zeros à esquerda, sequências de escape.
- **Linha de comando:** mensagem vazia, EOF, Ctrl+C, bytes inválidos, 2 MB de entrada, 450 MB sem quebra de linha com memória limitada, arquivos que já existem, pasta no lugar de arquivo, terminal só ASCII.

Os testes usam `pow()`, `math.gcd` e o crivo **apenas como gabarito** para conferir o código feito à mão. Os scripts não usam nada disso.

Resultado atual: **65 de 65 passam** (rodado 3 vezes seguidas, porque há sorteios).

## Limitações (importante citar na apresentação)

Este é um RSA **didático** ("textbook RSA"). Para uso real faltaria:

- **Padding (OAEP)**: sem ele o RSA é determinístico (mesma mensagem e mesma chave → mesmo texto cifrado) e vulnerável a vários ataques.
- **Gerador aleatório criptográfico**: o `random` do Python é previsível; em produção usa-se uma fonte segura do sistema operacional.
- **Tamanho de chave**: o padrão de 1024 bits está abaixo do recomendado atualmente (2048 bits ou mais). Dá para mudar a constante até 4096, mas a geração fica mais lenta (cerca de 7 s para 4096 bits, num teste meu).
- **Proteção da chave privada**: aqui ela é salva em texto puro, e ambas as chaves são geradas no mesmo script por simplicidade. Num cenário real, quem recebe a mensagem gera o par de chaves e envia só a pública para quem vai cifrar.
- **Integridade**: nada garante que a mensagem cifrada não foi alterada, reordenada ou cortada (veja o README do descriptografar).
- **Ataques de tempo**: a exponenciação não é de tempo constante.
- **Mensagem de uma linha**: o `Enter` encerra a mensagem; o limite é de 1.000.000 de bytes.

## Possíveis perguntas do professor

- *Por que usar e = 65537?* É primo, é 2¹⁶ + 1, ou seja, só tem dois bits 1 no binário (`10000000000000001`), o que deixa a cifragem rápida, e é grande o bastante para evitar ataques de expoente pequeno (com e = 3, uma mensagem curta poderia ficar menor que n e ser decifrada só com uma raiz cúbica).
- *Por que não calcular `m**e % n` direto?* `m**e` teria milhares de dígitos; o square-and-multiply mantém tudo abaixo de n.
- *O Miller-Rabin garante que é primo?* Não, é probabilístico, mas a chance de erro com 40 rodadas é insignificante.
- *O que acontece se alguém descobrir p e q?* Calcula φ(n), depois d, e quebra o sistema. Por isso a segurança depende da dificuldade de fatorar n.
- *E se eu rodar o script duas vezes?* A segunda execução pergunta antes de sobrescrever, porque a chave privada antiga se perderia.
- *E se eu trocar `EXPOENTE_PUBLICO` por 4, ou `TAMANHO_CHAVE_EM_BITS` por 0?* O script recusa com uma mensagem apontando a constante. Antes, o expoente par fazia o programa travar para sempre.
- *Como vocês sabem que está certo?* Pela bateria de testes: 65 testes, comparando com `pow()`, `math.gcd` e um crivo, além de tentativas de quebrar o programa pela linha de comando.
