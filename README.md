# PBIX Documentador

Gera automaticamente a documentação técnica de relatórios Power BI (`.pbix`)
em arquivos `.txt`, para uso na documentação do **SBIS**.

Para cada arquivo `.pbix` encontrado na pasta informada, é gerado um `.txt`
(`documentacao_<nome_do_relatorio>.txt`) dividido nas seguintes seções:

1. Informações Gerais
2. Fontes de Dados
3. Tabelas Utilizadas (com colunas e tipos)
4. Modelagem de Dados (relacionamentos)
5. Transformações Power Query (M)
6. Medidas DAX
7. Colunas Calculadas
8. Tabelas Calculadas (geradas via DAX)

## Arquitetura

O projeto segue **arquitetura em camadas**, cada uma com uma única
responsabilidade:

```
pbix_documentador/
├── main.py                              # Ponto de entrada (CLI)
├── requirements.txt
├── output/                              # .txt gerados (padrão)
└── src/
    ├── domain/
    │   └── models.py                    # Entidades puras (dataclasses)
    ├── infrastructure/
    │   └── pbix_reader.py               # Único ponto que fala com a lib pbixray
    ├── application/
    │   ├── extraction_service.py        # Converte dados crus -> domínio
    │   └── documentation_service.py     # Orquestra: varre pasta, extrai, gera .txt
    └── presentation/
        └── txt_report_generator.py      # Formata o domínio -> .txt
```

**Fluxo de dependências:** `main.py → application → (domain + infrastructure + presentation)`.
`domain` não depende de nada; é o centro da arquitetura.

Essa separação permite, por exemplo, trocar a lib de leitura (infraestrutura)
ou gerar um `.md`/`.docx` no lugar do `.txt` (apresentação) sem tocar nas
outras camadas.

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

```bash
# Via argumento
python main.py --pasta "C:\Relatorios\SBIS" --saida "C:\Documentacao"

# Ou de forma interativa (o programa pergunta o caminho)
python main.py
```

O programa varre a pasta informada, identifica todos os `.pbix` e gera um
`.txt` de documentação para cada um na pasta de saída (`output/` por padrão).

## Biblioteca utilizada

O projeto usa [`pbixray`](https://github.com/Hugoberry/pbixray), uma
biblioteca Python que lê diretamente o binário do `.pbix` (tabelas,
schema, relacionamentos, Power Query/M, medidas e colunas DAX) sem
precisar do Power BI Desktop instalado.

## Observações importantes

- **Modelos live/DirectQuery "thin"** (sem modelo embutido, conectados a um
  dataset do Power BI Service) não possuem dados para extrair localmente —
  o `pbixray` lança uma exceção nesses casos e o item é listado como `[ERRO]`
  no resumo final, sem travar o processamento dos demais arquivos.
- Todas as leituras de propriedades do modelo são feitas de forma defensiva
  (`src/infrastructure/pbix_reader.py`): se uma propriedade não existir
  naquela versão da lib ou naquele modelo específico, a seção correspondente
  do `.txt` aparece como "nenhum item encontrado" em vez de quebrar a execução.
