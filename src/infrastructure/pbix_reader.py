"""
Camada de Infraestrutura (Infrastructure Layer)
-------------------------------------------------
Responsável única e exclusivamente por falar com o "mundo externo": aqui,
a biblioteca `pbixray`, que sabe ler o binário do arquivo .pbix.

Nenhuma outra camada do projeto importa `pbixray` diretamente — só esta
classe. Isso significa que, se um dia a biblioteca mudar de nome, trocar
de API ou precisarmos usar outra (ex.: pbi-tools), só este arquivo muda.

A classe devolve dados "crus" (DataFrames do pandas, dicts, valores
simples) — a conversão para os modelos de domínio acontece na camada de
aplicação (application/extraction_service.py).
"""

import os
from typing import Optional

import pandas as pd

try:
    from pbixray import PBIXRay
except ImportError as exc:  # pragma: no cover - mensagem amigável se faltar instalar
    raise ImportError(
        "A biblioteca 'pbixray' não está instalada. "
        "Rode: pip install -r requirements.txt"
    ) from exc


class PBIXReader:
    """Encapsula o acesso ao arquivo .pbix via PBIXRay."""

    def __init__(self, caminho_arquivo: str):
        if not os.path.isfile(caminho_arquivo):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        if not caminho_arquivo.lower().endswith(".pbix"):
            raise ValueError(f"O arquivo informado não é um .pbix: {caminho_arquivo}")

        self.caminho_arquivo = caminho_arquivo
        self._model: Optional[PBIXRay] = None

    # --- ciclo de vida -----------------------------------------------
    def abrir(self) -> "PBIXReader":
        """Carrega o modelo em memória. Deve ser chamado antes dos getters."""
        self._model = PBIXRay(self.caminho_arquivo)
        return self

    def fechar(self) -> None:
        """Libera recursos (importante quando on_disk=True é usado em arquivos grandes)."""
        if self._model is not None and hasattr(self._model, "close"):
            self._model.close()
        self._model = None

    def __enter__(self) -> "PBIXReader":
        return self.abrir()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.fechar()

    @property
    def model(self) -> "PBIXRay":
        if self._model is None:
            raise RuntimeError("O modelo ainda não foi carregado. Chame abrir() primeiro.")
        return self._model

    # --- acesso aos dados crus do modelo ------------------------------
    def tamanho_bytes(self) -> int:
        try:
            return int(self.model.size)
        except Exception:
            return os.path.getsize(self.caminho_arquivo)

    def obter_tabelas(self):
        """Lista simples com o nome de cada tabela do modelo."""
        return list(self.model.tables)

    def obter_schema(self) -> pd.DataFrame:
        """DataFrame: TableName, ColumnName, PandasDataType."""
        return self._df_seguro("schema")

    def obter_relacionamentos(self) -> pd.DataFrame:
        """DataFrame: FromTableName, FromColumnName, ToTableName, ToColumnName, IsActive, Cardinality..."""
        return self._df_seguro("relationships")

    def obter_power_query(self) -> pd.DataFrame:
        """DataFrame: TableName, Expression (código M de transformação)."""
        return self._df_seguro("power_query")

    def obter_m_parameters(self) -> pd.DataFrame:
        """DataFrame: ParameterName, Description, Expression, ModifiedTime."""
        return self._df_seguro("m_parameters")

    def obter_medidas_dax(self) -> pd.DataFrame:
        """DataFrame: TableName, Name, Expression, DisplayFolder, Description."""
        return self._df_seguro("dax_measures")

    def obter_colunas_calculadas(self) -> pd.DataFrame:
        """DataFrame: TableName, ColumnName, Expression."""
        return self._df_seguro("dax_columns")

    def obter_tabelas_calculadas(self) -> pd.DataFrame:
        """DataFrame: TableName, Expression (tabelas 100% geradas via DAX)."""
        return self._df_seguro("dax_tables")

    def obter_estatisticas(self) -> pd.DataFrame:
        """DataFrame: TableName, ColumnName, Cardinality, Dictionary, HashIndex, DataSize."""
        return self._df_seguro("statistics")

    def obter_metadados_modelo(self):
        """Metadados gerais de configuração do Power BI usados na criação do modelo."""
        return self._df_seguro("metadata")

    def obter_conexoes(self) -> list:
        """Lista de dicts com as conexões/fontes declaradas no relatório (Connections manifest)."""
        try:
            conexoes = self.model.connections
            return list(conexoes) if conexoes else []
        except Exception:
            return []

    def obter_datasources_tmschema(self) -> pd.DataFrame:
        """Fallback: datasources via endpoint TMSCHEMA_DATASOURCES (modelos import)."""
        return self._df_seguro("tmschema_datasources")

    # --- utilitário interno --------------------------------------------
    def _df_seguro(self, nome_propriedade: str) -> pd.DataFrame:
        """
        Acessa uma propriedade do modelo pbixray de forma defensiva: nem toda
        versão da biblioteca expõe todas as propriedades, e nem todo modelo
        possui determinado recurso (ex.: nem todo .pbix tem tabelas calculadas).
        Em caso de erro, devolve um DataFrame vazio em vez de quebrar a execução.
        """
        try:
            valor = getattr(self.model, nome_propriedade)
            if valor is None:
                return pd.DataFrame()
            return valor
        except Exception:
            return pd.DataFrame()
