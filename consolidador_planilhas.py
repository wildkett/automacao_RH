import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl.utils import get_column_letter


# ==== Configurações ====

PASTA_BASE = Path(__file__).parent
PASTA_FILIAIS = PASTA_BASE / "filiais"
ARQUIVO_SAIDA = PASTA_BASE / "consolidado_filiais.xlsx"

COLUNAS = {
    "nome": "Nome",
    "colaborador": "Nome",
    "cpf": "CPF",
    "documento": "CPF",
    "data admissão": "Admissão",
    "admissao": "Admissão",
    "dt_admissao": "Admissão",
    "área": "Área",
    "area": "Área",
    "setor": "Área",
}

AREAS = {
    "rh": "Recursos Humanos",
    "recursos humanos": "Recursos Humanos",
    "ti": "Tecnologia",
    "t.i.": "Tecnologia",
    "tecnologia": "Tecnologia",
    "fin": "Financeiro",
    "financeiro": "Financeiro",
    "vendas": "Comercial",
    "comercial": "Comercial",
    "log": "Logística",
    "logistica": "Logística",
    "logística": "Logística",
}

FORMATOS_DATA = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"]


# ==== Planilhas fictícias ====

def criar_planilhas_ficticias():
    if PASTA_FILIAIS.exists():
        return

    PASTA_FILIAIS.mkdir()

    campinas = pd.DataFrame({
        "Nome": ["ana paula souza", "Bruno  Lima", "carla mendes", "Diego Ramos", "Elisa Torres"],
        "CPF": ["194.127.724-16", "29712417182", "5260181514", "419.357.392-39", "123.456.789-00"],
        "Data Admissão": ["15/03/2022", "2021-07-01", "01.02.2023", "31/02/2022", "10/10/2020"],
        "Área": ["RH", "ti", "Financeiro", "Vendas", "Logística"],
    })

    santos = pd.DataFrame({
        "colaborador": ["FERNANDA ALVES", "Gustavo Pereira", "ana paula souza", "Helena Castro", "Igor Nunes"],
        "cpf": ["593 246 292 20", "148.976.886-63", "19412772416", "543.425.986-63", "852.297.363-64"],
        "admissao": ["05-08-2019", "2020-11-23", "15/03/2022", "", "12/12/2021"],
        "setor": ["recursos humanos", "T.I.", "rh", "comercial", "Marketing"],
    })

    sorocaba = pd.DataFrame({
        "NOME": ["julia rocha", "Kleber Dias", "Larissa Melo", "Larissa Melo", "Marcos Vieira"],
        "DOCUMENTO": ["871.296.668-11", "82258215803", "576.186.328-63", "576.186.328-63", "145.347.782-95"],
        "DT_ADMISSAO": ["2018-04-09", "20/06/2023", "03/01/2024", "03/01/2024", "2022-09-30"],
        "AREA": ["LOG", "fin", "Comercial", "Comercial", "Tecnologia"],
    })

    campinas.to_excel(PASTA_FILIAIS / "filial_campinas.xlsx", index=False)
    santos.to_excel(PASTA_FILIAIS / "filial_santos.xlsx", index=False)
    sorocaba.to_excel(PASTA_FILIAIS / "filial_sorocaba.xlsx", index=False)


# ==== Leitura ====

def ler_planilhas():
    tabelas = []

    for arquivo in sorted(PASTA_FILIAIS.glob("filial_*.xlsx")):
        tabela = pd.read_excel(arquivo, dtype=str).fillna("")
        tabela = tabela.rename(columns=lambda coluna: COLUNAS.get(coluna.strip().lower(), coluna))

        faltando = sorted(set(COLUNAS.values()) - set(tabela.columns))
        if faltando:
            sys.exit(
                f"Erro na planilha {arquivo.name}: coluna não encontrada: {', '.join(faltando)}.\n"
                f"Acrescente o nome usado nessa planilha no dicionário COLUNAS."
            )

        tabela["Filial"] = arquivo.stem.replace("filial_", "").title()
        tabelas.append(tabela)

    return pd.concat(tabelas, ignore_index=True)


# ==== Padronização ====

def padronizar_nome(valor):
    return " ".join(valor.split()).title()


def cpf_valido(numeros):
    if len(numeros) != 11 or numeros == numeros[0] * 11:
        return False

    for posicao in (9, 10):
        soma = sum(int(numeros[i]) * (posicao + 1 - i) for i in range(posicao))
        if soma * 10 % 11 % 10 != int(numeros[posicao]):
            return False

    return True


def padronizar_cpf(valor):
    numeros = "".join(caractere for caractere in valor if caractere.isdigit()).zfill(11)

    if not cpf_valido(numeros):
        return ""

    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"


def padronizar_data(valor):
    for formato in FORMATOS_DATA:
        try:
            return datetime.strptime(valor.strip(), formato).date()
        except ValueError:
            pass

    return ""


def padronizar_area(valor):
    return AREAS.get(valor.strip().lower(), "")


def padronizar(dados):
    return pd.DataFrame({
        "Filial": dados["Filial"],
        "Nome": dados["Nome"].apply(padronizar_nome),
        "CPF": dados["CPF"].apply(padronizar_cpf),
        "Admissão": dados["Admissão"].apply(padronizar_data),
        "Área": dados["Área"].apply(padronizar_area),
    })


# ==== Validação ====

def listar_problemas(linha):
    problemas = []

    if linha["CPF"] == "":
        problemas.append("CPF inválido")
    if linha["Admissão"] == "":
        problemas.append("Data inválida")
    if linha["Área"] == "":
        problemas.append("Área desconhecida")

    return ", ".join(problemas)


def separar(dados, padronizado):
    motivos = padronizado.apply(listar_problemas, axis=1)
    validos = padronizado[motivos == ""]
    duplicados = validos.index[validos.duplicated(subset="CPF")]
    motivos[duplicados] = "CPF duplicado"

    base = padronizado[motivos == ""]

    inconsistencias = dados[motivos != ""].copy()
    inconsistencias["Motivo"] = motivos[motivos != ""]
    inconsistencias = inconsistencias[["Filial", "Nome", "CPF", "Admissão", "Área", "Motivo"]]

    return base, inconsistencias


# ==== Resumo ====

def montar_resumo(base):
    return pd.crosstab(base["Filial"], base["Área"], margins=True, margins_name="Total")


# ==== Exportação ====

def ajustar_colunas(planilha):
    for numero, coluna in enumerate(planilha.columns, start=1):
        maior = max(len(str(celula.value or "")) for celula in coluna)
        planilha.column_dimensions[get_column_letter(numero)].width = maior + 2


def salvar_excel(base, resumo, inconsistencias):
    with pd.ExcelWriter(ARQUIVO_SAIDA) as arquivo:
        base.to_excel(arquivo, sheet_name="Base", index=False)
        resumo.to_excel(arquivo, sheet_name="Resumo")
        inconsistencias.to_excel(arquivo, sheet_name="Inconsistências", index=False)

        for celula in arquivo.sheets["Base"]["D"][1:]:
            celula.number_format = "DD/MM/YYYY"

        for planilha in arquivo.sheets.values():
            ajustar_colunas(planilha)


# ==== Execução ====

def main():
    criar_planilhas_ficticias()

    dados = ler_planilhas()
    padronizado = padronizar(dados)
    base, inconsistencias = separar(dados, padronizado)
    resumo = montar_resumo(base)
    salvar_excel(base, resumo, inconsistencias)

    print(f"Registros lidos: {len(dados)}")
    print(f"Registros na base: {len(base)}")
    print(f"Inconsistências: {len(inconsistencias)}")
    print(f"Arquivo gerado: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()
