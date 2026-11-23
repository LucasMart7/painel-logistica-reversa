"""Roda todas as consultas do painel direto no Postgres, sem o Metabase.

Imita a forma como o Metabase trata as variáveis: um bloco [[ ... ]] some
quando a variável dele não tem valor e fica, com o valor no lugar, quando tem.
Serve para validar o SQL antes de publicar e para conferir que os totais batem.

Uso:
  python scripts/testar_consultas.py
  python scripts/testar_consultas.py --filtro grupo=Rastreadores --filtro situacao=Danificado
"""

import argparse
import os
import re
from pathlib import Path

import psycopg2

PASTA_CONSULTAS = Path(__file__).resolve().parent.parent / "sql" / "consultas"
BLOCO_OPCIONAL = re.compile(r"\[\[(.*?)\]\]", re.S)
VARIAVEL = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def renderizar(sql, filtros):
    def trata_bloco(trecho):
        nomes = VARIAVEL.findall(trecho.group(1))
        return trecho.group(1) if all(n in filtros for n in nomes) else ""

    sql = BLOCO_OPCIONAL.sub(trata_bloco, sql)
    return VARIAVEL.sub(lambda m: "'" + filtros[m.group(1)].replace("'", "''") + "'", sql)


def conectar():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "painel"),
        user=os.getenv("PGUSER", "painel"),
        password=os.getenv("PGPASSWORD", "painel"),
    )


def checar_totais(cursor, filtros):
    """Os cards de grupo e de situação precisam somar o total."""
    def escalar(nome):
        cursor.execute(renderizar((PASTA_CONSULTAS / nome).read_text(encoding="utf-8"), filtros))
        return cursor.fetchone()[0]

    total = escalar("01_total.sql")
    grupos = sum(escalar(n) for n in ["02_rastreadores.sql", "03_cameras.sql", "04_leitores_vega.sql", "05_leitores_orion.sql"])
    situacoes = sum(escalar(n) for n in ["08_danificados.sql", "09_em_debugg.sql", "10_nao_triados.sql"])
    assert total == grupos == situacoes, f"totais não batem: total={total} grupos={grupos} situacoes={situacoes}"
    print(f"\nTotais conferem: {total} itens = soma dos grupos = soma das situações")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--filtro", action="append", default=[], help="nome=valor, ex.: grupo=Câmeras")
    args = parser.parse_args()
    filtros = dict(f.split("=", 1) for f in args.filtro)

    with conectar() as conexao, conexao.cursor() as cursor:
        for arquivo in sorted(PASTA_CONSULTAS.glob("*.sql")):
            cursor.execute(renderizar(arquivo.read_text(encoding="utf-8"), filtros))
            linhas = cursor.fetchall()
            amostra = linhas[0] if len(linhas) == 1 else f"{len(linhas)} linhas, primeira: {linhas[0] if linhas else '-'}"
            print(f"ok  {arquivo.name:32} {amostra}")
        checar_totais(cursor, filtros)


if __name__ == "__main__":
    main()
