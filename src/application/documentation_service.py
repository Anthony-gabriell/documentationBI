"""
Camada de Aplicação (Application Layer) — Orquestração
-----------------------------------------------------------
Ponto único que o main.py chama. Decide "o quê fazer" (varrer a pasta,
extrair cada .pbix, gerar o .txt, tratar erros) usando os serviços das
outras camadas — sem conter regra de extração nem de formatação, que já
vivem em extraction_service.py e txt_report_generator.py respectivamente.
"""

import os
from dataclasses import dataclass
from typing import List

from src.application.extraction_service import ExtractionService
from src.presentation.txt_report_generator import TxtReportGenerator


@dataclass
class ResultadoProcessamento:
    arquivo_origem: str
    sucesso: bool
    caminho_txt_gerado: str = ""
    mensagem_erro: str = ""


class DocumentationService:
    """Orquestra a geração de documentação para um ou mais arquivos .pbix."""

    def __init__(self):
        self._extractor = ExtractionService()
        self._gerador_txt = TxtReportGenerator()

    def processar_arquivo(self, caminho_pbix: str, pasta_saida: str) -> ResultadoProcessamento:
        """Extrai e documenta um único arquivo .pbix."""
        try:
            os.makedirs(pasta_saida, exist_ok=True)
            documento = self._extractor.extrair(caminho_pbix)

            nome_base = os.path.splitext(os.path.basename(caminho_pbix))[0]
            caminho_txt = os.path.join(pasta_saida, f"documentacao_{nome_base}.txt")
            self._gerador_txt.salvar(documento, caminho_txt)

            return ResultadoProcessamento(
                arquivo_origem=caminho_pbix,
                sucesso=True,
                caminho_txt_gerado=caminho_txt,
            )
        except Exception as erro:
            return ResultadoProcessamento(
                arquivo_origem=caminho_pbix,
                sucesso=False,
                mensagem_erro=str(erro),
            )

    def processar_pasta(self, pasta_entrada: str, pasta_saida: str) -> List[ResultadoProcessamento]:
        """Varre uma pasta em busca de arquivos .pbix e documenta todos eles."""
        if not os.path.isdir(pasta_entrada):
            raise NotADirectoryError(f"Pasta não encontrada: {pasta_entrada}")

        arquivos_pbix = [
            os.path.join(pasta_entrada, nome)
            for nome in sorted(os.listdir(pasta_entrada))
            if nome.lower().endswith(".pbix")
        ]

        if not arquivos_pbix:
            return []

        return [self.processar_arquivo(arquivo, pasta_saida) for arquivo in arquivos_pbix]
