"""
Camada de Apresentação (Presentation Layer)
----------------------------------------------
Transforma um DocumentoPBIX (domínio) em um arquivo .txt único, porém
dividido em seções bem delimitadas — exatamente como pedido: informações
gerais, fontes de dados, tabelas, modelagem (relacionamentos),
transformações Power Query, medidas DAX e colunas calculadas.

Esta camada não sabe nada sobre pbixray nem sobre como os dados foram
extraídos — ela só sabe formatar o que recebe.
"""

from datetime import datetime

from src.domain.models import DocumentoPBIX

LARGURA_SEPARADOR = 100


class TxtReportGenerator:
    """Gera a documentação textual de um DocumentoPBIX."""

    def gerar(self, documento: DocumentoPBIX) -> str:
        secoes = [
            self._cabecalho(documento),
            self._secao_informacoes_gerais(documento),
            self._secao_fontes_dados(documento),
            self._secao_tabelas(documento),
            self._secao_modelagem_dados(documento),
            self._secao_power_query(documento),
            self._secao_medidas_dax(documento),
            self._secao_colunas_calculadas(documento),
            self._secao_tabelas_calculadas(documento),
            self._rodape(),
        ]
        return "\n\n".join(secoes)

    def salvar(self, documento: DocumentoPBIX, caminho_saida: str) -> str:
        conteudo = self.gerar(documento)
        with open(caminho_saida, "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
        return caminho_saida

    # --- helpers de formatação -----------------------------------------
    @staticmethod
    def _titulo_secao(titulo: str) -> str:
        linha = "=" * LARGURA_SEPARADOR
        return f"{linha}\n{titulo.upper()}\n{linha}"

    @staticmethod
    def _sem_dados(mensagem: str = "Nenhum item encontrado neste modelo.") -> str:
        return f"  ({mensagem})"

    # --- seções ------------------------------------------------------------
    def _cabecalho(self, doc: DocumentoPBIX) -> str:
        return (
            f"DOCUMENTAÇÃO TÉCNICA DE RELATÓRIO POWER BI — SBIS\n"
            f"Arquivo: {doc.metadados.nome_arquivo}\n"
            f"Gerado automaticamente em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )

    def _secao_informacoes_gerais(self, doc: DocumentoPBIX) -> str:
        m = doc.metadados
        tamanho_mb = m.tamanho_bytes / (1024 * 1024)
        linhas = [
            self._titulo_secao("1. Informações Gerais"),
            f"  Nome do arquivo ..................: {m.nome_arquivo}",
            f"  Caminho completo .................: {m.caminho_completo}",
            f"  Tamanho do modelo ................: {m.tamanho_bytes:,} bytes (~{tamanho_mb:.2f} MB)",
            f"  Total de tabelas .................: {m.total_tabelas}",
            f"  Total de medidas DAX .............: {m.total_medidas}",
            f"  Total de colunas calculadas ......: {m.total_colunas_calculadas}",
            f"  Total de relacionamentos .........: {m.total_relacionamentos}",
            f"  Total de fontes de dados .........: {m.total_fontes_dados}",
        ]
        return "\n".join(linhas)

    def _secao_fontes_dados(self, doc: DocumentoPBIX) -> str:
        linhas = [self._titulo_secao("2. Fontes de Dados")]
        if not doc.fontes_dados:
            linhas.append(self._sem_dados("Nenhuma fonte de dados identificada (verifique se o modelo é DirectQuery/live)."))
        else:
            for fonte in doc.fontes_dados:
                linhas.append(f"  - Nome ......: {fonte.nome}")
                linhas.append(f"    Tipo ......: {fonte.tipo or 'não informado'}")
                if fonte.detalhes:
                    linhas.append(f"    Detalhes ..: {fonte.detalhes}")
                linhas.append("")
        return "\n".join(linhas).rstrip()

    def _secao_tabelas(self, doc: DocumentoPBIX) -> str:
        linhas = [self._titulo_secao("3. Tabelas Utilizadas")]
        if not doc.tabelas:
            linhas.append(self._sem_dados())
            return "\n".join(linhas)

        colunas_por_tabela = {}
        for coluna in doc.colunas:
            colunas_por_tabela.setdefault(coluna.tabela, []).append(coluna)

        for tabela in doc.tabelas:
            linhas.append(f"  Tabela: {tabela.nome}  ({tabela.total_colunas} coluna(s))")
            colunas = colunas_por_tabela.get(tabela.nome, [])
            if colunas:
                for col in colunas:
                    linhas.append(f"      - {col.nome_coluna} ({col.tipo_dado})")
            else:
                linhas.append("      (schema de colunas não disponível)")
            linhas.append("")
        return "\n".join(linhas).rstrip()

    def _secao_modelagem_dados(self, doc: DocumentoPBIX) -> str:
        linhas = [self._titulo_secao("4. Modelagem de Dados (Relacionamentos)")]
        if not doc.relacionamentos:
            linhas.append(self._sem_dados())
            return "\n".join(linhas)

        for rel in doc.relacionamentos:
            status = "Ativo" if rel.ativo else "Inativo"
            linhas.append(
                f"  {rel.tabela_origem}.{rel.coluna_origem}  --->  "
                f"{rel.tabela_destino}.{rel.coluna_destino}"
            )
            linhas.append(
                f"      Status: {status} | Cardinalidade: {rel.cardinalidade or 'n/d'} "
                f"| Filtro cruzado: {rel.filtro_cruzado or 'n/d'}"
            )
            linhas.append("")
        return "\n".join(linhas).rstrip()

    def _secao_power_query(self, doc: DocumentoPBIX) -> str:
        linhas = [self._titulo_secao("5. Transformações Power Query (M)")]

        if doc.parametros_m:
            linhas.append("  Parâmetros M:")
            for p in doc.parametros_m:
                linhas.append(f"    - {p.nome}: {p.expressao}  ({p.descricao or 'sem descrição'})")
            linhas.append("")

        if not doc.power_queries:
            linhas.append(self._sem_dados("Nenhuma query M encontrada (modelo pode ser DirectQuery nativo)."))
            return "\n".join(linhas)

        for pq in doc.power_queries:
            linhas.append(f"  Tabela: {pq.tabela}")
            linhas.append("  Código M:")
            for linha_m in pq.expressao_m.splitlines():
                linhas.append(f"      {linha_m}")
            linhas.append("")
        return "\n".join(linhas).rstrip()

    def _secao_medidas_dax(self, doc: DocumentoPBIX) -> str:
        linhas = [self._titulo_secao("6. Medidas DAX")]
        if not doc.medidas:
            linhas.append(self._sem_dados())
            return "\n".join(linhas)

        for medida in doc.medidas:
            linhas.append(f"  Medida: {medida.nome}  (Tabela: {medida.tabela})")
            if medida.pasta_exibicao:
                linhas.append(f"      Pasta de exibição: {medida.pasta_exibicao}")
            if medida.descricao:
                linhas.append(f"      Descrição: {medida.descricao}")
            linhas.append("      Expressão DAX:")
            for linha_dax in medida.expressao_dax.splitlines():
                linhas.append(f"          {linha_dax}")
            linhas.append("")
        return "\n".join(linhas).rstrip()

    def _secao_colunas_calculadas(self, doc: DocumentoPBIX) -> str:
        linhas = [self._titulo_secao("7. Colunas Calculadas")]
        if not doc.colunas_calculadas:
            linhas.append(self._sem_dados())
            return "\n".join(linhas)

        for col in doc.colunas_calculadas:
            linhas.append(f"  Coluna: {col.nome_coluna}  (Tabela: {col.tabela})")
            linhas.append("      Expressão DAX:")
            for linha_dax in col.expressao_dax.splitlines():
                linhas.append(f"          {linha_dax}")
            linhas.append("")
        return "\n".join(linhas).rstrip()

    def _secao_tabelas_calculadas(self, doc: DocumentoPBIX) -> str:
        linhas = [self._titulo_secao("8. Tabelas Calculadas (geradas via DAX)")]
        if not doc.tabelas_calculadas:
            linhas.append(self._sem_dados())
            return "\n".join(linhas)

        for tab in doc.tabelas_calculadas:
            linhas.append(f"  Tabela: {tab.tabela}")
            linhas.append("      Expressão DAX:")
            for linha_dax in tab.expressao_dax.splitlines():
                linhas.append(f"          {linha_dax}")
            linhas.append("")
        return "\n".join(linhas).rstrip()

    def _rodape(self) -> str:
        linha = "=" * LARGURA_SEPARADOR
        return f"{linha}\nFIM DA DOCUMENTAÇÃO\n{linha}"
