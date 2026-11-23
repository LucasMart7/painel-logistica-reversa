"""Exporta a visão do painel para a demo estática em docs/.

A demo (docs/index.html) é uma versão do painel que roda só no navegador,
sem Postgres nem Metabase, para quem quer ver o resultado sem subir nada.
Ela lê docs/dados.js, que este script gera a partir de vw_itens_reversa.

Uso:
  python scripts/gerar_demo.py
"""

import json
from datetime import datetime
from pathlib import Path

from testar_consultas import conectar

DESTINO = Path(__file__).resolve().parent.parent / "docs" / "dados.js"


def main():
    with conectar() as conexao, conexao.cursor() as cursor:
        cursor.execute("""
            SELECT modelo, grupo, situacao,
                   (now() AT TIME ZONE 'America/Sao_Paulo')::date
                     - (entrou_em AT TIME ZONE 'America/Sao_Paulo')::date AS dias_atras
            FROM vw_itens_reversa
        """)
        itens = cursor.fetchall()
        cursor.execute("SELECT modelo, grupo FROM vw_catalogo_modelos ORDER BY ordem")
        catalogo = cursor.fetchall()

    # Formato compacto: cada item vira [índice do modelo, índice da situação, dias atrás].
    modelos = [m for m, _ in catalogo]
    situacoes = ["Não triado", "Debugg", "Danificado"]
    dados = {
        "geradoEm": datetime.now().strftime("%d/%m/%Y"),
        "modelos": [{"modelo": m, "grupo": g} for m, g in catalogo],
        "situacoes": situacoes,
        "itens": [[modelos.index(m), situacoes.index(s), d] for m, _, s, d in itens],
    }
    DESTINO.write_text("window.DADOS = " + json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + ";\n",
                       encoding="utf-8")
    print(f"{len(itens)} itens exportados para {DESTINO.relative_to(DESTINO.parent.parent)}")


if __name__ == "__main__":
    main()
