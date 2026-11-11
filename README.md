# Automações de RH em Python

Aqui estão dois scripts que escrevi para automatizar tarefas comuns do dia a dia de RH: juntar planilhas que vêm de filiais diferentes e organizar documentos de colaboradores. São tarefas repetitivas, que tomam tempo quando feitas à mão e abrem espaço para erro de digitação.

Todos os dados são fictícios. Os próprios scripts criam os arquivos de exemplo na primeira vez que rodam, então dá para testar sem preparar nada.

## Consolidador de planilhas

Quando cada filial manda a sua planilha, elas quase nunca chegam iguais. Uma chama a coluna de "CPF" e outra de "documento". Uma escreve a data como 15/03/2022 e outra como 2022-03-15. A mesma área aparece como "RH", "rh" ou "recursos humanos".

O `consolidador_planilhas.py` junta as planilhas, coloca CPF, datas, nomes e áreas no mesmo padrão, confere se o CPF é válido pelos dígitos verificadores e remove pessoas repetidas. O CPF é lido como texto e completado com zeros à esquerda, porque o Excel costuma apagar o zero inicial quando trata o CPF como número. No final gera um Excel com três abas:

- a base consolidada e limpa;
- um resumo com a quantidade de colaboradores por filial e área;
- uma aba de inconsistências, com o motivo de cada problema.

A ideia da última aba é que nada seja descartado em silêncio. O que não pôde ser corrigido fica listado com os valores do jeito que vieram da filial, para alguém ajustar na origem, e a base que alimenta relatórios e indicadores fica confiável.

Com as planilhas de exemplo, o resultado é este:

```
Registros lidos: 15
Registros na base: 9
Inconsistências: 6
```

As seis inconsistências são uma data que não existe (31/02/2022), uma data em branco, um CPF com dígito verificador errado, uma área que não está no cadastro e duas pessoas repetidas, uma delas presente em duas filiais.

## Organizador de documentos

Atestados, holerites e contratos costumam chegar com nomes como "Atestado João Silva 12-03-2025 (1).pdf". O `organizador_documentos.py` identifica o tipo de documento pelo nome do arquivo, pega a data e o nome do colaborador e move o arquivo para uma estrutura padrão, como `Atestados/2025/Atestado_Joao_Silva_2025-03-12.pdf`.

Como mexer em documentos de colaboradores exige cuidado, ele roda por padrão em modo de simulação: mostra o que faria, mas não move nada. Para mover de verdade é preciso rodar com `--executar`. Cada ação fica registrada num arquivo de log com data e hora, o que ajuda a conferir o resultado e saber o que aconteceu com cada arquivo. O que ele não reconhece continua na pasta de entrada, sem ser tocado. Se dois arquivos fossem gerar o mesmo nome, o segundo recebe um número no final, e nenhum documento é sobrescrito.

É comum o mesmo documento chegar duas vezes, por e-mail e por mensagem. Por isso o organizador compara o conteúdo de cada arquivo com o dos documentos já arquivados. Uma cópia idêntica não é arquivada de novo: fica na pasta de entrada e aparece no log como duplicada, para alguém conferir e apagar. Nada é excluído automaticamente.

Um trecho do log com os arquivos de exemplo:

```
Início | modo SIMULAÇÃO | pasta documentos_entrada
AVISO | CONTRATO Pedro Lima.pdf | data não encontrada no nome, usada a data de modificação do arquivo (2026-11-10)
SIMULADO | CONTRATO Pedro Lima.pdf -> documentos_arquivados\Contratos\2026\Contrato_Pedro_Lima_2026-11-10.pdf
IGNORADO | foto_confraternizacao.jpg | tipo não identificado
SIMULADO | Atestado João Silva 12-03-2025.pdf -> documentos_arquivados\Atestados\2025\Atestado_Joao_Silva_2025-03-12.pdf
DUPLICADO | Atestado João Silva 12-03-2025 (1).pdf | mesmo conteúdo de Atestado_Joao_Silva_2025-03-12.pdf
Fim | 6 organizados | 1 duplicados | 1 ignorados
Nada foi movido. Para mover de verdade, rode com --executar
```

## Como usar

É preciso ter o Python 3.9 ou mais novo. No Windows, se o comando `python` não funcionar, use `py` no lugar. O organizador usa só a biblioteca padrão do Python. O consolidador usa pandas e openpyxl, e os testes usam pytest. Os três estão no `requirements.txt`:

```
pip install -r requirements.txt
```

Consolidador:

```
python consolidador_planilhas.py
```

Na primeira execução ele cria a pasta `filiais` com três planilhas de exemplo e gera o `consolidado_filiais.xlsx`. Para usar com outras planilhas, coloque-as na pasta `filiais` com o nome começando por `filial_` (por exemplo `filial_jundiai.xlsx`). Se uma planilha usar um nome de coluna ou de área diferente, basta acrescentá-lo nos dicionários `COLUNAS` e `AREAS`, no início do script.

Organizador:

```
python organizador_documentos.py
python organizador_documentos.py --executar
```

O primeiro comando só simula. O segundo move os arquivos. Os documentos ficam na pasta `documentos_entrada` (na primeira execução ela é criada com arquivos de exemplo), vão para `documentos_arquivados` e o registro fica em `organizador.log`.

## Testes

As regras mais importantes dos dois scripts têm testes automatizados com pytest, em `test_consolidador.py` e `test_organizador.py`. Eles conferem a validação do CPF, a recuperação do zero à esquerda, as datas em formatos diferentes, as áreas fora do cadastro, os CPFs repetidos, a identificação do tipo de documento, a leitura do nome e da data no nome do arquivo e a detecção de cópias pelo conteúdo.

Para rodar:

```
python -m pytest -v
```

O resultado esperado é `18 passed`. Se uma alteração no código quebrar alguma dessas regras, o teste correspondente falha e mostra o valor encontrado e o esperado.

## Limitações

O organizador decide o tipo de documento pelo nome do arquivo e não lê o conteúdo do PDF. Um arquivo chamado só "scan001.pdf", por exemplo, fica de fora. Quando o nome não traz data, ele usa a data de modificação do arquivo, que nem sempre é a data do documento. O consolidador mantém o primeiro registro válido quando encontra um CPF repetido, sem comparar qual é o mais recente. Esses pontos estão entre as próximas melhorias que quero fazer.
