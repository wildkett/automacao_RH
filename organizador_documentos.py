import hashlib
import logging
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path


# ==== Configurações ====

PASTA_BASE = Path(__file__).parent
PASTA_ENTRADA = PASTA_BASE / "documentos_entrada"
PASTA_ARQUIVO = PASTA_BASE / "documentos_arquivados"
ARQUIVO_LOG = PASTA_BASE / "organizador.log"

SIMULACAO = "--executar" not in sys.argv

TIPOS = {
    "atestado": "Atestado",
    "holerite": "Holerite",
    "contracheque": "Holerite",
    "contrato": "Contrato",
}

PADROES_DATA = [
    (r"(\d{4})[-_.](\d{2})[-_.](\d{2})", "{0}-{1}-{2}"),
    (r"(\d{2})[-_.](\d{2})[-_.](\d{4})", "{2}-{1}-{0}"),
    (r"(\d{4})[-_.](\d{2})", "{0}-{1}"),
    (r"(\d{2})[-_.](\d{4})", "{1}-{0}"),
]


# ==== Arquivos fictícios ====

def criar_arquivos_ficticios():
    if PASTA_ENTRADA.exists():
        return

    PASTA_ENTRADA.mkdir()

    nomes = [
        "Atestado João Silva 12-03-2025.pdf",
        "Atestado João Silva 12-03-2025 (1).pdf",
        "atestado_maria_souza_2025-04-02.pdf",
        "holerite_maria_souza_2025_02.pdf",
        "Contracheque Pedro Lima 03-2025.PDF",
        "CONTRATO Pedro Lima.pdf",
        "contrato_ana_costa_15.01.2024.docx",
        "foto_confraternizacao.jpg",
    ]

    for nome in nomes:
        original = nome.replace(" (1)", "")
        (PASTA_ENTRADA / nome).write_text(f"documento fictício: {original}", encoding="utf-8")


# ==== Log ====

def configurar_log():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
        handlers=[
            logging.FileHandler(ARQUIVO_LOG, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


# ==== Leitura do nome ====

def normalizar(texto):
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower()


def identificar_tipo(texto):
    for palavra, tipo in TIPOS.items():
        if palavra in texto:
            return tipo

    return None


def extrair_data(texto, arquivo):
    for padrao, formato in PADROES_DATA:
        encontrado = re.search(padrao, texto)
        if encontrado:
            return formato.format(*encontrado.groups())

    data = datetime.fromtimestamp(arquivo.stat().st_mtime).strftime("%Y-%m-%d")
    logging.info(f"AVISO | {arquivo.name} | data não encontrada no nome, usada a data de modificação do arquivo ({data})")
    return data


def extrair_nome(texto):
    palavras = re.sub(r"[^a-z ]", " ", texto).split()
    nome = [palavra.title() for palavra in palavras if palavra not in TIPOS]
    return "_".join(nome) or "Sem_Nome"


# ==== Destino ====

def montar_destino(arquivo, tipo, nome, data):
    pasta = PASTA_ARQUIVO / f"{tipo}s" / data[:4]
    return pasta / f"{tipo}_{nome}_{data}{arquivo.suffix.lower()}"


def caminho_livre(destino, usados):
    candidato = destino
    contador = 2

    while candidato.exists() or candidato in usados:
        candidato = destino.with_stem(f"{destino.stem}_{contador}")
        contador += 1

    return candidato


# ==== Duplicados ====

def calcular_hash(arquivo):
    return hashlib.sha256(arquivo.read_bytes()).hexdigest()


def mapear_arquivados():
    if not PASTA_ARQUIVO.exists():
        return {}

    return {calcular_hash(arquivo): arquivo.name for arquivo in PASTA_ARQUIVO.rglob("*") if arquivo.is_file()}


# ==== Organização ====

def ordem_de_leitura(arquivo):
    return len(arquivo.name), arquivo.name


def organizar():
    modo = "SIMULAÇÃO" if SIMULACAO else "EXECUÇÃO"
    logging.info(f"Início | modo {modo} | pasta {PASTA_ENTRADA.name}")

    usados = set()
    conteudos = mapear_arquivados()
    organizados = 0
    duplicados = 0
    ignorados = 0

    for arquivo in sorted(PASTA_ENTRADA.iterdir(), key=ordem_de_leitura):
        if not arquivo.is_file():
            continue

        texto = normalizar(arquivo.stem)
        tipo = identificar_tipo(texto)

        if tipo is None:
            logging.info(f"IGNORADO | {arquivo.name} | tipo não identificado")
            ignorados += 1
            continue

        conteudo = calcular_hash(arquivo)
        if conteudo in conteudos:
            logging.info(f"DUPLICADO | {arquivo.name} | mesmo conteúdo de {conteudos[conteudo]}")
            duplicados += 1
            continue

        data = extrair_data(texto, arquivo)
        nome = extrair_nome(texto)
        destino = caminho_livre(montar_destino(arquivo, tipo, nome, data), usados)
        usados.add(destino)
        conteudos[conteudo] = destino.name

        if not SIMULACAO:
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(arquivo, destino)

        acao = "SIMULADO" if SIMULACAO else "MOVIDO"
        logging.info(f"{acao} | {arquivo.name} -> {destino.relative_to(PASTA_BASE)}")
        organizados += 1

    logging.info(f"Fim | {organizados} organizados | {duplicados} duplicados | {ignorados} ignorados")

    if SIMULACAO:
        logging.info("Nada foi movido. Para mover de verdade, rode com --executar")


# ==== Execução ====

def main():
    criar_arquivos_ficticios()
    configurar_log()
    organizar()


if __name__ == "__main__":
    main()
