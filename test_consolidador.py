import pandas as pd

from consolidador_planilhas import cpf_valido, padronizar, padronizar_area, padronizar_cpf, padronizar_data, separar


# ==== CPF ====

def test_cpf_valido():
    assert cpf_valido("19412772416")


def test_cpf_com_digito_errado():
    assert not cpf_valido("12345678900")


def test_cpf_com_todos_os_digitos_iguais():
    assert not cpf_valido("11111111111")


def test_cpf_sem_zero_inicial_e_recuperado():
    assert padronizar_cpf("5260181514") == "052.601.815-14"


# ==== Datas ====

def test_datas_em_formatos_diferentes_dao_o_mesmo_dia():
    assert padronizar_data("15/03/2022") == padronizar_data("2022-03-15")


def test_data_que_nao_existe():
    assert padronizar_data("31/02/2022") == ""


# ==== Áreas ====

def test_area_escrita_de_outro_jeito():
    assert padronizar_area("  T.I. ") == "Tecnologia"


def test_area_fora_do_cadastro():
    assert padronizar_area("Marketing") == ""


# ==== Duplicados ====

def test_cpf_repetido_vai_para_inconsistencias():
    dados = pd.DataFrame({
        "Filial": ["Sorocaba", "Sorocaba"],
        "Nome": ["Larissa Melo", "Larissa Melo"],
        "CPF": ["576.186.328-63", "576.186.328-63"],
        "Admissão": ["03/01/2024", "03/01/2024"],
        "Área": ["Comercial", "Comercial"],
    })

    base, inconsistencias = separar(dados, padronizar(dados))

    assert len(base) == 1
    assert list(inconsistencias["Motivo"]) == ["CPF duplicado"]


def test_registro_valido_entra_na_base_mesmo_com_duplicado_invalido():
    dados = pd.DataFrame({
        "Filial": ["Campinas", "Santos"],
        "Nome": ["ana paula souza", "ana paula souza"],
        "CPF": ["194.127.724-16", "19412772416"],
        "Admissão": ["31/02/2022", "15/03/2022"],
        "Área": ["RH", "rh"],
    })

    base, inconsistencias = separar(dados, padronizar(dados))

    assert list(base["Filial"]) == ["Santos"]
    assert list(inconsistencias["Motivo"]) == ["Data inválida"]
