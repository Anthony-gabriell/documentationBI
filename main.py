"""
PBIX Documentador — Ponto de Entrada (CLI)
=============================================
Lê todos os arquivos .pbix de uma pasta informada e gera, para cada um,
um arquivo .txt de documentação técnica (fontes de dados, tabelas,
modelagem, Power Query, medidas DAX e colunas calculadas).

Uso:
    python main.py --pasta "C:\\Relatorios\\SBIS"
    python main.py --pasta "C:\\Relatorios\\SBIS" --saida "C:\\Documentacao"

    # Sem argumentos, o programa pergunta o caminho interativamente:
    python main.py
"""

import argparse
import os
import sys

from src.application.documentation_service import DocumentationService


def ler_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera documentação técnica (.txt) de arquivos Power BI (.pbix)."
    )
    parser.add_argument(
        "--pasta",
        "-p",
        dest="pasta_entrada",
        help="Pasta onde estão os arquivos .pbix a serem documentados.",
    )
    parser.add_argument(
        "--saida",
        "-s",
        dest="pasta_saida",
        default="output",
        help="Pasta onde os .txt de documentação serão salvos (padrão: ./output).",
    )
    return parser.parse_args()


def obter_pasta_entrada(args: argparse.Namespace) -> str:
    if args.pasta_entrada:
        return args.pasta_entrada
    # Modo interativo, caso o caminho não tenha sido passado via linha de comando
    pasta = input("Informe o caminho da pasta com os arquivos .pbix: ").strip().strip('"')
    return pasta


def main() -> int:
    args = ler_argumentos()
    pasta_entrada = obter_pasta_entrada(args)
    pasta_saida = args.pasta_saida

    if not pasta_entrada:
        print("Nenhuma pasta informada. Encerrando.")
        return 1

    servico = DocumentationService()

    print(f"\nVarrendo a pasta: {pasta_entrada}")
    try:
        resultados = servico.processar_pasta(pasta_entrada, pasta_saida)
    except NotADirectoryError as erro:
        print(f"Erro: {erro}")
        return 1

    if not resultados:
        print("Nenhum arquivo .pbix foi encontrado nessa pasta.")
        return 0

    print(f"\n{len(resultados)} arquivo(s) .pbix encontrado(s). Processando...\n")

    total_sucesso = 0
    for resultado in resultados:
        nome = os.path.basename(resultado.arquivo_origem)
        if resultado.sucesso:
            total_sucesso += 1
            print(f"  [OK]   {nome}  ->  {resultado.caminho_txt_gerado}")
        else:
            print(f"  [ERRO] {nome}  ->  {resultado.mensagem_erro}")

    print(f"\nConcluído: {total_sucesso}/{len(resultados)} documentação(ões) gerada(s) com sucesso.")
    print(f"Arquivos salvos em: {os.path.abspath(pasta_saida)}\n")

    return 0 if total_sucesso == len(resultados) else 2


if __name__ == "__main__":
    sys.exit(main())
