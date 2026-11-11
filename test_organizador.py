from pathlib import Path

from organizador_documentos import calcular_hash, extrair_data, extrair_nome, identificar_tipo, normalizar, ordem_de_leitura


# ==== Tipo ====

def test_contracheque_vira_holerite():
    assert identificar_tipo(normalizar("Contracheque Pedro Lima 03-2025")) == "Holerite"


def test_arquivo_que_nao_e_documento():
    assert identificar_tipo(normalizar("foto_confraternizacao")) is None


# ==== Nome e data ====

def test_nome_sem_acento_e_sem_numeros():
    assert extrair_nome(normalizar("Atestado João Silva 12-03-2025 (1)")) == "Joao_Silva"


def test_data_no_formato_brasileiro():
    assert extrair_data(normalizar("Atestado João Silva 12-03-2025"), None) == "2025-03-12"


def test_data_com_mes_e_ano():
    assert extrair_data(normalizar("holerite_maria_souza_2025_02"), None) == "2025-02"


# ==== Duplicados ====

def test_arquivos_com_mesmo_conteudo_tem_o_mesmo_hash(tmp_path):
    original = tmp_path / "atestado.pdf"
    copia = tmp_path / "atestado (1).pdf"
    original.write_text("mesmo conteúdo", encoding="utf-8")
    copia.write_text("mesmo conteúdo", encoding="utf-8")

    assert calcular_hash(original) == calcular_hash(copia)


def test_arquivos_com_conteudo_diferente_tem_hash_diferente(tmp_path):
    joao = tmp_path / "atestado_joao.pdf"
    maria = tmp_path / "atestado_maria.pdf"
    joao.write_text("atestado do João", encoding="utf-8")
    maria.write_text("atestado da Maria", encoding="utf-8")

    assert calcular_hash(joao) != calcular_hash(maria)


def test_original_e_lido_antes_da_copia():
    arquivos = [Path("Atestado João Silva 12-03-2025 (1).pdf"), Path("Atestado João Silva 12-03-2025.pdf")]

    assert sorted(arquivos, key=ordem_de_leitura)[0].name == "Atestado João Silva 12-03-2025.pdf"
