import os
import random
import sys

TAMANHO_CHAVE_EM_BITS = 1024
MINIMO_DE_BITS_DA_CHAVE = 32
MAXIMO_DE_BITS_DA_CHAVE = 4096
EXPOENTE_PUBLICO = 65537
RODADAS_MILLER_RABIN = 40
PRIMOS_PEQUENOS = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
PREFIXO_DE_BLOCO = 1
TAMANHO_MAXIMO_DA_MENSAGEM_EM_BYTES = 1_000_000
TAMANHO_MAXIMO_DA_RESPOSTA_DE_CONFIRMACAO = 100

ARQUIVO_CHAVE_PUBLICA = "chave_publica.txt"
ARQUIVO_CHAVE_PRIVADA = "chave_privada.txt"
ARQUIVO_MENSAGEM_CRIPTOGRAFADA = "mensagem_criptografada.txt"
ARQUIVOS_DE_SAIDA = [ARQUIVO_CHAVE_PUBLICA, ARQUIVO_CHAVE_PRIVADA, ARQUIVO_MENSAGEM_CRIPTOGRAFADA]


class ErroRSA(ValueError):
    pass


def exponenciacao_modular(base, expoente, modulo):
    if modulo < 1 or expoente < 0:
        raise ErroRSA("a exponenciação modular exige módulo positivo e expoente não negativo")
    resultado = 1 % modulo
    base = base % modulo
    while expoente > 0:
        if expoente % 2 == 1:
            resultado = (resultado * base) % modulo
        expoente = expoente // 2
        base = (base * base) % modulo
    return resultado


def maximo_divisor_comum(a, b):
    a, b = abs(a), abs(b)
    while b != 0:
        a, b = b, a % b
    return a


def inverso_modular(numero, modulo):
    if modulo < 2:
        raise ErroRSA("o módulo do inverso modular deve ser maior que 1")
    resto_anterior, resto_atual = modulo, numero % modulo
    coeficiente_anterior, coeficiente_atual = 0, 1
    while resto_atual != 0:
        quociente = resto_anterior // resto_atual
        resto_anterior, resto_atual = resto_atual, resto_anterior - quociente * resto_atual
        coeficiente_anterior, coeficiente_atual = coeficiente_atual, coeficiente_anterior - quociente * coeficiente_atual
    if resto_anterior != 1:
        raise ErroRSA("o número não tem inverso modular, pois não é coprimo com o módulo")
    return coeficiente_anterior % modulo


def passa_no_teste_de_miller_rabin(candidato):
    expoente_impar = candidato - 1
    quantidade_de_fatores_dois = 0
    while expoente_impar % 2 == 0:
        expoente_impar = expoente_impar // 2
        quantidade_de_fatores_dois += 1

    for _ in range(RODADAS_MILLER_RABIN):
        testemunha = random.randrange(2, candidato - 1)
        valor = exponenciacao_modular(testemunha, expoente_impar, candidato)
        if valor == 1 or valor == candidato - 1:
            continue
        for _ in range(quantidade_de_fatores_dois - 1):
            valor = (valor * valor) % candidato
            if valor == candidato - 1:
                break
        else:
            return False
    return True


def eh_primo(candidato):
    if candidato < 2:
        return False
    for primo_pequeno in PRIMOS_PEQUENOS:
        if candidato == primo_pequeno:
            return True
        if candidato % primo_pequeno == 0:
            return False
    return passa_no_teste_de_miller_rabin(candidato)


def gerar_numero_primo(tamanho_em_bits):
    if tamanho_em_bits < 3:
        raise ErroRSA("um número primo precisa ter pelo menos 3 bits")
    while True:
        candidato = random.getrandbits(tamanho_em_bits)
        dois_bits_mais_altos = (1 << (tamanho_em_bits - 1)) | (1 << (tamanho_em_bits - 2))
        candidato = candidato | dois_bits_mais_altos | 1
        if eh_primo(candidato):
            return candidato


def eh_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def validar_configuracao():
    if not eh_inteiro(TAMANHO_CHAVE_EM_BITS):
        raise ErroRSA("TAMANHO_CHAVE_EM_BITS deve ser um número inteiro")
    if not MINIMO_DE_BITS_DA_CHAVE <= TAMANHO_CHAVE_EM_BITS <= MAXIMO_DE_BITS_DA_CHAVE:
        raise ErroRSA(f"TAMANHO_CHAVE_EM_BITS deve estar entre {MINIMO_DE_BITS_DA_CHAVE} e {MAXIMO_DE_BITS_DA_CHAVE}")
    if TAMANHO_CHAVE_EM_BITS % 2 != 0:
        raise ErroRSA("TAMANHO_CHAVE_EM_BITS deve ser par, pois cada primo usa metade dos bits")
    if not eh_inteiro(EXPOENTE_PUBLICO):
        raise ErroRSA("EXPOENTE_PUBLICO deve ser um número inteiro")
    if EXPOENTE_PUBLICO < 3 or EXPOENTE_PUBLICO % 2 == 0:
        raise ErroRSA("EXPOENTE_PUBLICO deve ser ímpar e maior ou igual a 3")
    if EXPOENTE_PUBLICO.bit_length() > TAMANHO_CHAVE_EM_BITS - 3:
        raise ErroRSA("EXPOENTE_PUBLICO é grande demais para o tamanho da chave")


def par_de_chaves_funciona(chave_publica, chave_privada):
    expoente_publico, modulo = chave_publica
    expoente_privado, _ = chave_privada
    for numero_de_teste in (2, modulo // 3, modulo - 2):
        numero_cifrado = exponenciacao_modular(numero_de_teste, expoente_publico, modulo)
        if exponenciacao_modular(numero_cifrado, expoente_privado, modulo) != numero_de_teste:
            return False
    return True


def gerar_chaves():
    validar_configuracao()
    tamanho_de_cada_primo = TAMANHO_CHAVE_EM_BITS // 2
    while True:
        primo_p = gerar_numero_primo(tamanho_de_cada_primo)
        primo_q = gerar_numero_primo(tamanho_de_cada_primo)
        if primo_p == primo_q:
            continue
        totiente = (primo_p - 1) * (primo_q - 1)
        if maximo_divisor_comum(EXPOENTE_PUBLICO, totiente) == 1:
            break

    modulo = primo_p * primo_q
    expoente_privado = inverso_modular(EXPOENTE_PUBLICO, totiente)

    chave_publica = (EXPOENTE_PUBLICO, modulo)
    chave_privada = (expoente_privado, modulo)
    if not par_de_chaves_funciona(chave_publica, chave_privada):
        raise ErroRSA("falha interna: o par de chaves gerado não decifra o que cifra")
    return chave_publica, chave_privada


def bytes_para_numero(dados):
    numero = 0
    for byte in dados:
        numero = numero * 256 + byte
    return numero


def tamanho_do_bloco_em_bytes(modulo):
    tamanho = (modulo.bit_length() - 1) // 8 - 1
    if tamanho < 1:
        raise ErroRSA("o módulo é pequeno demais para dividir a mensagem em blocos")
    return tamanho


def dividir_em_blocos(dados, tamanho_do_bloco):
    if tamanho_do_bloco < 1:
        raise ErroRSA("o tamanho do bloco deve ser de pelo menos 1 byte")
    return [dados[inicio:inicio + tamanho_do_bloco] for inicio in range(0, len(dados), tamanho_do_bloco)]


def converter_mensagem_para_bytes(mensagem):
    if mensagem == "":
        raise ErroRSA("a mensagem não pode ser vazia")
    try:
        mensagem_em_bytes = mensagem.encode("utf-8")
    except UnicodeEncodeError:
        raise ErroRSA("a mensagem tem caracteres inválidos que não podem ser convertidos para UTF-8")
    if len(mensagem_em_bytes) > TAMANHO_MAXIMO_DA_MENSAGEM_EM_BYTES:
        raise ErroRSA(f"a mensagem tem {len(mensagem_em_bytes)} bytes, e o máximo permitido é {TAMANHO_MAXIMO_DA_MENSAGEM_EM_BYTES}")
    return mensagem_em_bytes


def criptografar_bloco(bloco, chave_publica):
    expoente_publico, modulo = chave_publica
    bloco_com_prefixo = bytes([PREFIXO_DE_BLOCO]) + bloco
    numero_do_bloco = bytes_para_numero(bloco_com_prefixo)
    return exponenciacao_modular(numero_do_bloco, expoente_publico, modulo)


def criptografar_mensagem(mensagem, chave_publica):
    _, modulo = chave_publica
    mensagem_em_bytes = converter_mensagem_para_bytes(mensagem)
    blocos = dividir_em_blocos(mensagem_em_bytes, tamanho_do_bloco_em_bytes(modulo))
    return [criptografar_bloco(bloco, chave_publica) for bloco in blocos]


def gravar_arquivo_de_texto(caminho, linhas):
    try:
        with open(caminho, "w", encoding="utf-8", newline="\n") as arquivo:
            for linha in linhas:
                arquivo.write(f"{linha}\n")
    except OSError as erro:
        raise ErroRSA(f"não foi possível gravar o arquivo {caminho!r} ({erro.strerror or erro})")


def salvar_chave(caminho, expoente, modulo):
    gravar_arquivo_de_texto(caminho, [f"expoente={expoente}", f"modulo={modulo}"])


def salvar_mensagem_criptografada(caminho, blocos_criptografados):
    gravar_arquivo_de_texto(caminho, blocos_criptografados)


def configurar_terminal_para_utf8():
    for fluxo, tratamento_de_erros in ((sys.stdin, "strict"), (sys.stdout, "strict"), (sys.stderr, "backslashreplace")):
        try:
            fluxo.reconfigure(encoding="utf-8", errors=tratamento_de_erros)
        except (AttributeError, ValueError, OSError):
            pass


def remover_quebra_de_linha(linha):
    if linha.endswith("\n"):
        linha = linha[:-1]
    if linha.endswith("\r"):
        linha = linha[:-1]
    return linha


def ler_linha(pergunta, tamanho_maximo):
    print(pergunta, end="", flush=True)
    try:
        linha = sys.stdin.readline(tamanho_maximo + 1)
    except UnicodeDecodeError:
        raise ErroRSA("o texto digitado não é UTF-8 válido")
    if linha == "":
        raise ErroRSA("a entrada foi encerrada antes de a pergunta ser respondida")
    if len(linha) > tamanho_maximo and not linha.endswith("\n"):
        raise ErroRSA(f"o texto digitado passa do limite de {tamanho_maximo} caracteres")
    return remover_quebra_de_linha(linha)


def ler_mensagem_digitada():
    mensagem = ler_linha("Digite a mensagem a ser criptografada: ", TAMANHO_MAXIMO_DA_MENSAGEM_EM_BYTES)
    converter_mensagem_para_bytes(mensagem)
    return mensagem


def confirmar_sobrescrita_se_necessario():
    arquivos_existentes = [caminho for caminho in ARQUIVOS_DE_SAIDA if os.path.exists(caminho)]
    if not arquivos_existentes:
        return
    print("Já existem arquivos de uma execução anterior: " + ", ".join(arquivos_existentes))
    print("Sobrescrevê-los apaga a chave privada antiga, e as mensagens cifradas com ela não poderão mais ser lidas.")
    resposta = ler_linha("Deseja sobrescrever? [s/N]: ", TAMANHO_MAXIMO_DA_RESPOSTA_DE_CONFIRMACAO)
    if resposta.strip().lower() not in ("s", "sim"):
        raise ErroRSA("operação cancelada, nenhum arquivo foi alterado")


def executar():
    validar_configuracao()
    confirmar_sobrescrita_se_necessario()
    mensagem = ler_mensagem_digitada()

    print(f"Gerando chaves RSA de {TAMANHO_CHAVE_EM_BITS} bits...")
    chave_publica, chave_privada = gerar_chaves()

    blocos_criptografados = criptografar_mensagem(mensagem, chave_publica)

    salvar_chave(ARQUIVO_CHAVE_PUBLICA, *chave_publica)
    salvar_chave(ARQUIVO_CHAVE_PRIVADA, *chave_privada)
    salvar_mensagem_criptografada(ARQUIVO_MENSAGEM_CRIPTOGRAFADA, blocos_criptografados)

    print(f"Mensagem dividida em {len(blocos_criptografados)} bloco(s) e criptografada.")
    print(f"Chave pública salva em: {ARQUIVO_CHAVE_PUBLICA}")
    print(f"Chave privada salva em: {ARQUIVO_CHAVE_PRIVADA}")
    print(f"Mensagem criptografada salva em: {ARQUIVO_MENSAGEM_CRIPTOGRAFADA}")


def main():
    configurar_terminal_para_utf8()
    try:
        executar()
    except ErroRSA as erro:
        print(f"Erro: {erro}.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nErro: operação cancelada pelo usuário.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
