import sys

ARQUIVO_CHAVE_PRIVADA_PADRAO = "chave_privada.txt"
ARQUIVO_MENSAGEM_CRIPTOGRAFADA_PADRAO = "mensagem_criptografada.txt"
PREFIXO_DE_BLOCO = 1
MINIMO_DE_BITS_DO_MODULO = 32
MAXIMO_DE_BITS_DO_MODULO = 4096
MAXIMO_DE_DIGITOS_POR_NUMERO = 1300
TAMANHO_MAXIMO_DO_ARQUIVO_DE_CHAVE_EM_BYTES = 10_000
TAMANHO_MAXIMO_DO_ARQUIVO_DA_MENSAGEM_EM_BYTES = 50_000_000
TAMANHO_MAXIMO_DE_UM_CAMINHO = 1000


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


def numero_para_bytes(numero):
    if numero < 0:
        raise ErroRSA("não é possível converter um número negativo em bytes")
    lista_de_bytes = []
    while numero > 0:
        lista_de_bytes.append(numero % 256)
        numero = numero // 256
    lista_de_bytes.reverse()
    return bytes(lista_de_bytes)


def tamanho_do_bloco_em_bytes(modulo):
    return (modulo.bit_length() - 1) // 8 - 1


def bloco_tem_formato_valido(bloco_com_prefixo, modulo):
    tamanho_maximo = tamanho_do_bloco_em_bytes(modulo) + 1
    return 2 <= len(bloco_com_prefixo) <= tamanho_maximo and bloco_com_prefixo[0] == PREFIXO_DE_BLOCO


def converter_para_inteiro(texto, descricao):
    texto = texto.strip()
    if texto == "" or not (texto.isascii() and texto.isdigit()):
        raise ErroRSA(f"{descricao} deve conter apenas um número inteiro não negativo, mas contém {texto[:30]!r}")
    if len(texto) > MAXIMO_DE_DIGITOS_POR_NUMERO:
        raise ErroRSA(f"{descricao} tem mais de {MAXIMO_DE_DIGITOS_POR_NUMERO} dígitos")
    return int(texto)


def ler_texto_do_arquivo(caminho, descricao, tamanho_maximo_em_bytes):
    try:
        with open(caminho, "r", encoding="utf-8-sig") as arquivo:
            conteudo = arquivo.read(tamanho_maximo_em_bytes + 1)
    except FileNotFoundError:
        raise ErroRSA(f"o arquivo da {descricao} não foi encontrado: {caminho!r}")
    except IsADirectoryError:
        raise ErroRSA(f"{caminho!r} é uma pasta, e não o arquivo da {descricao}")
    except PermissionError:
        raise ErroRSA(f"sem permissão para ler o arquivo da {descricao}: {caminho!r}")
    except UnicodeDecodeError:
        raise ErroRSA(f"o arquivo {caminho!r} não é um texto UTF-8 válido, então não pode ser a {descricao}")
    except ValueError:
        raise ErroRSA(f"o caminho informado para a {descricao} é inválido")
    except OSError as erro:
        raise ErroRSA(f"não foi possível ler o arquivo da {descricao} ({erro.strerror or erro})")
    if len(conteudo) > tamanho_maximo_em_bytes:
        raise ErroRSA(f"o arquivo {caminho!r} é grande demais para ser a {descricao}")
    return conteudo.splitlines()


def validar_chave(expoente, modulo):
    quantidade_de_bits = modulo.bit_length()
    if not MINIMO_DE_BITS_DO_MODULO <= quantidade_de_bits <= MAXIMO_DE_BITS_DO_MODULO:
        raise ErroRSA(f"o módulo da chave tem {quantidade_de_bits} bits, e este programa aceita de {MINIMO_DE_BITS_DO_MODULO} a {MAXIMO_DE_BITS_DO_MODULO}")
    if modulo % 2 == 0:
        raise ErroRSA("o módulo da chave é par, então não pode ser o produto de dois primos ímpares")
    if not 2 <= expoente < modulo:
        raise ErroRSA("o expoente da chave está fora do intervalo válido (de 2 até o módulo menos 1)")


def ler_chave(caminho):
    linhas = ler_texto_do_arquivo(caminho, "chave privada", TAMANHO_MAXIMO_DO_ARQUIVO_DE_CHAVE_EM_BYTES)
    valores = {}
    for numero_da_linha, linha in enumerate(linhas, start=1):
        if linha.strip() == "":
            continue
        nome, separador, texto_do_valor = linha.partition("=")
        nome = nome.strip()
        if separador == "" or nome not in ("expoente", "modulo"):
            raise ErroRSA(f"a linha {numero_da_linha} da chave deve ser 'expoente=...' ou 'modulo=...'")
        if nome in valores:
            raise ErroRSA(f"o campo '{nome}' aparece mais de uma vez na chave")
        valores[nome] = converter_para_inteiro(texto_do_valor, f"o valor de '{nome}' na chave")
    for nome in ("expoente", "modulo"):
        if nome not in valores:
            raise ErroRSA(f"o campo '{nome}' não foi encontrado na chave")
    validar_chave(valores["expoente"], valores["modulo"])
    return valores["expoente"], valores["modulo"]


def ler_mensagem_criptografada(caminho):
    linhas = ler_texto_do_arquivo(caminho, "mensagem criptografada", TAMANHO_MAXIMO_DO_ARQUIVO_DA_MENSAGEM_EM_BYTES)
    blocos = []
    for numero_da_linha, linha in enumerate(linhas, start=1):
        if linha.strip() == "":
            continue
        blocos.append(converter_para_inteiro(linha, f"a linha {numero_da_linha} da mensagem criptografada"))
    if not blocos:
        raise ErroRSA("o arquivo da mensagem criptografada não tem nenhum bloco")
    return blocos


def descriptografar_bloco(bloco_criptografado, chave_privada):
    expoente_privado, modulo = chave_privada
    if not 0 <= bloco_criptografado < modulo:
        raise ErroRSA("o número do bloco é maior ou igual ao módulo da chave, então a chave não corresponde a esta mensagem")
    numero_do_bloco = exponenciacao_modular(bloco_criptografado, expoente_privado, modulo)
    bloco_com_prefixo = numero_para_bytes(numero_do_bloco)
    if not bloco_tem_formato_valido(bloco_com_prefixo, modulo):
        raise ErroRSA("o bloco não pôde ser decifrado: a chave privada não corresponde à mensagem, ou o arquivo foi alterado")
    return bloco_com_prefixo[1:]


def converter_bytes_para_texto(mensagem_em_bytes):
    try:
        return mensagem_em_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ErroRSA("o resultado não é um texto UTF-8 válido: faltam blocos, eles estão fora de ordem ou a chave está incorreta")


def descriptografar_mensagem(blocos_criptografados, chave_privada):
    if not blocos_criptografados:
        raise ErroRSA("a mensagem criptografada não tem nenhum bloco")
    partes_da_mensagem = []
    for posicao, bloco_criptografado in enumerate(blocos_criptografados, start=1):
        try:
            partes_da_mensagem.append(descriptografar_bloco(bloco_criptografado, chave_privada))
        except ErroRSA as erro:
            raise ErroRSA(f"bloco {posicao}: {erro}")
    return converter_bytes_para_texto(b"".join(partes_da_mensagem))


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


def perguntar_caminho(descricao, caminho_padrao):
    resposta = ler_linha(f"{descricao} [{caminho_padrao}]: ", TAMANHO_MAXIMO_DE_UM_CAMINHO).strip()
    if len(resposta) >= 2 and resposta[0] == resposta[-1] and resposta[0] in "\"'":
        resposta = resposta[1:-1]
    return resposta if resposta != "" else caminho_padrao


def executar():
    caminho_da_chave = perguntar_caminho("Arquivo da chave privada", ARQUIVO_CHAVE_PRIVADA_PADRAO)
    caminho_da_mensagem = perguntar_caminho("Arquivo da mensagem criptografada", ARQUIVO_MENSAGEM_CRIPTOGRAFADA_PADRAO)

    chave_privada = ler_chave(caminho_da_chave)
    blocos_criptografados = ler_mensagem_criptografada(caminho_da_mensagem)

    mensagem = descriptografar_mensagem(blocos_criptografados, chave_privada)
    print(f"Mensagem descriptografada: {mensagem}")


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
