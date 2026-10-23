"""
Camada de Aplicação (Application Layer) — Extração
-----------------------------------------------------
Orquestra a leitura (infraestrutura) e converte os DataFrames "crus" em
objetos de domínio bem tipados. É aqui que fica a regra de "como mapear"
cada coluna do pbixray para o nosso modelo — a única camada que conhece
tanto o domínio quanto o formato de saída do pbixray.
"""

import os
import pandas as pd

from src.domain.models import (
    ColunaCalculadaInfo,
    ColunaInfo,
    DocumentoPBIX,
    FonteDadosInfo,
    MedidaInfo,
    MetadadosArquivo,
    ParametroMInfo,
    PowerQueryInfo,
    RelacionamentoInfo,
    TabelaCalculadaInfo,
    TabelaInfo,
)
from src.infrastructure.pbix_reader import PBIXReader


class ExtractionService:
    """Converte um arquivo .pbix em um DocumentoPBIX totalmente preenchido."""

    def extrair(self, caminho_arquivo: str) -> DocumentoPBIX:
        with PBIXReader(caminho_arquivo) as leitor:
            tabelas = self._extrair_tabelas(leitor)
            colunas = self._extrair_colunas(leitor)
            relacionamentos = self._extrair_relacionamentos(leitor)
            fontes_dados = self._extrair_fontes_dados(leitor)
            power_queries = self._extrair_power_queries(leitor)
            parametros_m = self._extrair_parametros_m(leitor)
            medidas = self._extrair_medidas(leitor)
            colunas_calculadas = self._extrair_colunas_calculadas(leitor)
            tabelas_calculadas = self._extrair_tabelas_calculadas(leitor)

            metadados = MetadadosArquivo(
                nome_arquivo=os.path.basename(caminho_arquivo),
                caminho_completo=os.path.abspath(caminho_arquivo),
                tamanho_bytes=leitor.tamanho_bytes(),
                total_tabelas=len(tabelas),
                total_medidas=len(medidas),
                total_colunas_calculadas=len(colunas_calculadas),
                total_relacionamentos=len(relacionamentos),
                total_fontes_dados=len(fontes_dados),
            )

            return DocumentoPBIX(
                metadados=metadados,
                tabelas=tabelas,
                colunas=colunas,
                relacionamentos=relacionamentos,
                fontes_dados=fontes_dados,
                power_queries=power_queries,
                parametros_m=parametros_m,
                medidas=medidas,
                colunas_calculadas=colunas_calculadas,
                tabelas_calculadas=tabelas_calculadas,
            )

    # --- extratores individuais -----------------------------------------
    def _extrair_tabelas(self, leitor: PBIXReader):
        nomes = leitor.obter_tabelas()
        schema = leitor.obter_schema()
        contagem_colunas = {}
        if not schema.empty and "TableName" in schema.columns:
            contagem_colunas = schema.groupby("TableName").size().to_dict()

        return [
            TabelaInfo(nome=nome, total_colunas=int(contagem_colunas.get(nome, 0)))
            for nome in nomes
        ]

    def _extrair_colunas(self, leitor: PBIXReader):
        schema = leitor.obter_schema()
        if schema.empty:
            return []
        return [
            ColunaInfo(
                tabela=str(linha.get("TableName", "")),
                nome_coluna=str(linha.get("ColumnName", "")),
                tipo_dado=str(linha.get("PandasDataType", "")),
            )
            for linha in schema.to_dict(orient="records")
        ]

    def _extrair_relacionamentos(self, leitor: PBIXReader):
        df = leitor.obter_relacionamentos()
        if df.empty:
            return []
        resultado = []
        for linha in df.to_dict(orient="records"):
            resultado.append(
                RelacionamentoInfo(
                    tabela_origem=str(linha.get("FromTableName", "")),
                    coluna_origem=str(linha.get("FromColumnName", "")),
                    tabela_destino=str(linha.get("ToTableName", "")),
                    coluna_destino=str(linha.get("ToColumnName", "")),
                    ativo=bool(linha.get("IsActive", True)),
                    cardinalidade=str(linha.get("Cardinality", "") or ""),
                    filtro_cruzado=str(linha.get("CrossFilteringBehavior", "") or ""),
                )
            )
        return resultado

    def _extrair_fontes_dados(self, leitor: PBIXReader):
        resultado = []

        # 1) Manifesto de conexões do relatório (connections)
        for conexao in leitor.obter_conexoes():
            if isinstance(conexao, dict):
                resultado.append(
                    FonteDadosInfo(
                        nome=str(conexao.get("Name") or conexao.get("name") or "Conexão sem nome"),
                        tipo=str(conexao.get("Type") or conexao.get("type") or ""),
                        detalhes=str(conexao),
                    )
                )

        # 2) Fallback: TMSCHEMA_DATASOURCES (modelos de importação)
        if not resultado:
            df = leitor.obter_datasources_tmschema()
            if not df.empty:
                for linha in df.to_dict(orient="records"):
                    nome = str(linha.get("Name", "Fonte de dados"))
                    resultado.append(
                        FonteDadosInfo(
                            nome=nome,
                            tipo=str(linha.get("Type", "")),
                            detalhes=str(linha.get("ConnectionString", "")),
                        )
                    )

        return resultado

    def _extrair_power_queries(self, leitor: PBIXReader):
        df = leitor.obter_power_query()
        if df.empty:
            return []
        return [
            PowerQueryInfo(
                tabela=str(linha.get("TableName", "")),
                expressao_m=str(linha.get("Expression", "")),
            )
            for linha in df.to_dict(orient="records")
        ]

    def _extrair_parametros_m(self, leitor: PBIXReader):
        df = leitor.obter_m_parameters()
        if df.empty:
            return []
        return [
            ParametroMInfo(
                nome=str(linha.get("ParameterName", "")),
                descricao=str(linha.get("Description", "") or ""),
                expressao=str(linha.get("Expression", "")),
            )
            for linha in df.to_dict(orient="records")
        ]

    def _extrair_medidas(self, leitor: PBIXReader):
        df = leitor.obter_medidas_dax()
        if df.empty:
            return []
        return [
            MedidaInfo(
                tabela=str(linha.get("TableName", "")),
                nome=str(linha.get("Name", "")),
                expressao_dax=str(linha.get("Expression", "")),
                pasta_exibicao=str(linha.get("DisplayFolder", "") or ""),
                descricao=str(linha.get("Description", "") or ""),
            )
            for linha in df.to_dict(orient="records")
        ]

    def _extrair_colunas_calculadas(self, leitor: PBIXReader):
        df = leitor.obter_colunas_calculadas()
        if df.empty:
            return []
        return [
            ColunaCalculadaInfo(
                tabela=str(linha.get("TableName", "")),
                nome_coluna=str(linha.get("ColumnName", "")),
                expressao_dax=str(linha.get("Expression", "")),
            )
            for linha in df.to_dict(orient="records")
        ]

    def _extrair_tabelas_calculadas(self, leitor: PBIXReader):
        df = leitor.obter_tabelas_calculadas()
        if df.empty:
            return []
        return [
            TabelaCalculadaInfo(
                tabela=str(linha.get("TableName", "")),
                expressao_dax=str(linha.get("Expression", "")),
            )
            for linha in df.to_dict(orient="records")
        ]
