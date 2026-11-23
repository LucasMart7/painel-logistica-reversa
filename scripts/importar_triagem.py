"""Importa a planilha de triagem (exportada em CSV) para a tabela `triagem`.

Na versão original deste painel a triagem era copiada à mão para dentro de uma
consulta, e ficava desatualizada assim que a planilha mudava. Este script
substitui a cópia manual: a planilha continua sendo a fonte, e a tabela é
recarregada inteira a cada execução, dentro de uma transação.

O script também aponta as inconsistências que valem correção na origem:
IMEIs repetidos e IMEIs que a planilha dá como em reversa mas o sistema não.

Uso:
  python scripts/importar_triagem.py dados/triagem_exemplo.csv
"""

import csv
import sys
from collections import Counter

from testar_consultas import conectar

COLUNAS = {"imei": "IMEI", "modelo": "Modelo", "causa": "Causa", "status": "Status", "posse": "Posse"}
STATUS_CONHECIDOS = {"Debugg", "Dano fisico", "Componente ausente", "Configurado", "Baixa"}


def ler_planilha(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        faltando = set(COLUNAS.values()) - set(leitor.fieldnames or [])
        if faltando:
            sys.exit(f"Colunas ausentes no CSV: {', '.join(sorted(faltando))}")
        linhas = []
        for numero, linha in enumerate(leitor, start=2):
            imei = (linha["IMEI"] or "").strip()
            if not imei.isdigit() or len(imei) != 15:
                print(f"linha {numero}: IMEI inválido ({imei!r}), ignorada")
                continue
            status = linha["Status"].strip()
            if status not in STATUS_CONHECIDOS:
                print(f"linha {numero}: status desconhecido ({status!r}), importada mesmo assim")
            linhas.append(tuple(linha[c].strip() or None for c in COLUNAS.values()))
    return linhas


def main():
    if len(sys.argv) != 2:
        sys.exit("Uso: python scripts/importar_triagem.py caminho/da/planilha.csv")
    linhas = ler_planilha(sys.argv[1])

    with conectar() as conexao, conexao.cursor() as cursor:
        cursor.execute("TRUNCATE triagem")
        cursor.executemany("INSERT INTO triagem (imei, modelo, causa, status, posse) VALUES (%s, %s, %s, %s, %s)", linhas)

        cursor.execute("""
            SELECT COUNT(DISTINCT t.imei)
            FROM triagem t
            LEFT JOIN equipamentos e ON e.imei = t.imei AND e.excluido_em IS NULL
            WHERE e.posse IS DISTINCT FROM 'logistica_reversa'
        """)
        fora_da_reversa = cursor.fetchone()[0]

    repetidos = sum(1 for qtd in Counter(l[0] for l in linhas).values() if qtd > 1)
    print(f"{len(linhas)} linhas importadas")
    print(f"{repetidos} IMEIs repetidos na planilha (o painel usa o status mais grave)")
    print(f"{fora_da_reversa} IMEIs da planilha que o sistema não dá como em reversa")


if __name__ == "__main__":
    main()
