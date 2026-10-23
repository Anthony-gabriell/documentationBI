"""
Camada de Domínio (Domain Layer)
---------------------------------
Contém apenas estruturas de dados puras (dataclasses) que representam as
entidades do modelo Power BI. Essa camada não conhece pbixray, pandas,
nem arquivos — apenas descreve "o que é" cada conceito do relatório.

Mantendo o domínio livre de dependências externas, é possível trocar a
biblioteca de leitura do .pbix (infraestrutura) ou o formato de saída
(apresentação) sem precisar alterar essas classes.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TabelaInfo:
    """Representa uma tabela do modelo semântico."""
    nome: str
    total_colunas: int = 0
    total_linhas: Optional[int] = None  # nem sempre é possível obter sem ler os dados


@dataclass
class ColunaInfo:
    """Representa uma coluna (comum, do schema) de uma tabela."""
    tabela: str
    nome_coluna: str
    tipo_dado: str


@dataclass
class ColunaCalculadaInfo:
    """Representa uma coluna calculada em DAX."""
    tabela: str
    nome_coluna: str
    expressao_dax: str


@dataclass
class TabelaCalculadaInfo:
    """Representa uma tabela inteira gerada via DAX (ex.: CALENDAR(), UNION())."""
    tabela: str
    expressao_dax: str


@dataclass
class MedidaInfo:
    """Representa uma medida (measure) DAX."""
    tabela: str
    nome: str
    expressao_dax: str
    pasta_exibicao: Optional[str] = None
    descricao: Optional[str] = None


@dataclass
class RelacionamentoInfo:
    """Representa um relacionamento entre duas tabelas do modelo."""
    tabela_origem: str
    coluna_origem: str
    tabela_destino: str
    coluna_destino: str
    ativo: bool
    cardinalidade: Optional[str] = None
    filtro_cruzado: Optional[str] = None


@dataclass
class PowerQueryInfo:
    """Representa uma query M (Power Query) associada a uma tabela."""
    tabela: str
    expressao_m: str


@dataclass
class ParametroMInfo:
    """Representa um parâmetro do Power Query (M)."""
    nome: str
    descricao: Optional[str]
    expressao: str


@dataclass
class FonteDadosInfo:
    """Representa uma fonte de dados/conexão declarada no relatório."""
    nome: str
    tipo: Optional[str] = None
    detalhes: Optional[str] = None


@dataclass
class MetadadosArquivo:
    """Informações gerais sobre o arquivo .pbix analisado."""
    nome_arquivo: str
    caminho_completo: str
    tamanho_bytes: int
    total_tabelas: int
    total_medidas: int
    total_colunas_calculadas: int
    total_relacionamentos: int
    total_fontes_dados: int


@dataclass
class DocumentoPBIX:
    """
    Agregado raiz: reúne tudo o que foi extraído de um arquivo .pbix.
    É este objeto que a camada de apresentação recebe para gerar o .txt.
    """
    metadados: MetadadosArquivo
    tabelas: List[TabelaInfo] = field(default_factory=list)
    colunas: List[ColunaInfo] = field(default_factory=list)
    relacionamentos: List[RelacionamentoInfo] = field(default_factory=list)
    fontes_dados: List[FonteDadosInfo] = field(default_factory=list)
    power_queries: List[PowerQueryInfo] = field(default_factory=list)
    parametros_m: List[ParametroMInfo] = field(default_factory=list)
    medidas: List[MedidaInfo] = field(default_factory=list)
    colunas_calculadas: List[ColunaCalculadaInfo] = field(default_factory=list)
    tabelas_calculadas: List[TabelaCalculadaInfo] = field(default_factory=list)
