"""Cria o painel no Metabase a partir dos arquivos do repositório.

Lê metabase/painel.json e as consultas em sql/consultas/, e pela API do Metabase:
  1. cria (ou reaproveita) a coleção do painel;
  2. cria um card por consulta, com as variáveis {{grupo}}, {{modelo}} e {{situacao}};
  3. cria o dashboard, posiciona os cards e liga os três filtros a cada card.

Rodar de novo arquiva a versão anterior do dashboard e dos cards e cria tudo do zero,
então o que está no Git é sempre a fonte da verdade.

Uso:
  MB_URL=http://localhost:3000 MB_USUARIO=voce@exemplo.com MB_SENHA=... \
  python scripts/provisionar_metabase.py
"""

import json
import os
import re
import sys
import uuid
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
NOME_DO_BANCO = os.getenv("MB_BANCO", "Painel de Logística Reversa")
VARIAVEL = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class Metabase:
    def __init__(self, url, usuario, senha):
        self.url = url.rstrip("/")
        self.sessao = requests.Session()
        token = self._chamar("post", "/api/session", json={"username": usuario, "password": senha})["id"]
        self.sessao.headers["X-Metabase-Session"] = token

    def _chamar(self, metodo, caminho, **kwargs):
        resposta = self.sessao.request(metodo, self.url + caminho, timeout=60, **kwargs)
        if not resposta.ok:
            sys.exit(f"Erro {resposta.status_code} em {metodo.upper()} {caminho}: {resposta.text[:300]}")
        return resposta.json() if resposta.content else None

    def get(self, caminho):
        return self._chamar("get", caminho)

    def post(self, caminho, corpo):
        return self._chamar("post", caminho, json=corpo)

    def put(self, caminho, corpo):
        return self._chamar("put", caminho, json=corpo)


def achar_banco(mb):
    bancos = mb.get("/api/database")
    bancos = bancos.get("data", bancos)
    for banco in bancos:
        if banco["name"] == NOME_DO_BANCO:
            return banco["id"]
    # Primeira execução: cadastra o Postgres do docker-compose no Metabase.
    criado = mb.post("/api/database", {
        "engine": "postgres",
        "name": NOME_DO_BANCO,
        "details": {
            "host": os.getenv("BANCO_HOST", "postgres"),
            "port": int(os.getenv("BANCO_PORTA", "5432")),
            "dbname": os.getenv("BANCO_NOME", "painel"),
            "user": os.getenv("BANCO_USUARIO", "painel"),
            "password": os.getenv("BANCO_SENHA", "painel"),
        },
    })
    print(f'banco "{NOME_DO_BANCO}" cadastrado no Metabase')
    return criado["id"]


def preparar_colecao(mb, nome):
    for colecao in mb.get("/api/collection"):
        if colecao.get("name") == nome and not colecao.get("archived"):
            return colecao["id"]
    return mb.post("/api/collection", {"name": nome, "color": "#509EE3"})["id"]


def arquivar_versao_anterior(mb, colecao_id, nome_dashboard):
    itens = mb.get(f"/api/collection/{colecao_id}/items")
    itens = itens.get("data", itens)
    for item in itens:
        if item["model"] == "dashboard" and item["name"] == nome_dashboard:
            mb.put(f"/api/dashboard/{item['id']}", {"archived": True})
        elif item["model"] == "card":
            mb.put(f"/api/card/{item['id']}", {"archived": True})


def variaveis_da_consulta(sql, filtros):
    nomes = {f["slug"]: f["nome"] for f in filtros}
    usadas = dict.fromkeys(VARIAVEL.findall(sql))
    return {n: {"id": str(uuid.uuid4()), "name": n, "display-name": nomes.get(n, n), "type": "text"} for n in usadas}


def configuracao_visual(card, cores):
    visual = dict(card.get("visual", {}))
    if visual.pop("cores_por_serie", False):
        visual["series_settings"] = {serie: {"color": cor} for serie, cor in cores.items()}
    return visual


def criar_card(mb, card, banco_id, colecao_id, painel):
    sql = (RAIZ / "sql" / "consultas" / card["arquivo"]).read_text(encoding="utf-8")
    variaveis = variaveis_da_consulta(sql, painel["filtros"])
    descricao = sql.splitlines()[0].lstrip("- ").strip()
    criado = mb.post("/api/card", {
        "name": card["nome"],
        "description": descricao,
        "display": card["tipo"],
        "collection_id": colecao_id,
        "visualization_settings": configuracao_visual(card, painel["cores"]),
        "dataset_query": {"type": "native", "database": banco_id,
                          "native": {"query": sql, "template-tags": variaveis}},
    })
    return criado["id"], variaveis


def criar_dashboard(mb, painel, colecao_id, cards_criados):
    dashboard = mb.post("/api/dashboard", {
        "name": painel["nome"], "description": painel["descricao"], "collection_id": colecao_id,
    })

    parametros = [{
        "id": f"filtro_{f['slug']}", "name": f["nome"], "slug": f["slug"],
        "type": "string/=", "sectionId": "string", "isMultiSelect": False,
        "values_query_type": "list", "values_source_type": "static-list",
        "values_source_config": {"values": f["valores"]},
    } for f in painel["filtros"]]

    dashcards = []
    for indice, card in enumerate(painel["cards"]):
        linha, coluna, largura, altura = card["pos"]
        base = {"id": -(indice + 1), "row": linha, "col": coluna, "size_x": largura, "size_y": altura, "series": []}
        if "titulo" in card:
            dashcards.append({**base, "card_id": None, "parameter_mappings": [], "visualization_settings": {
                "virtual_card": {"name": None, "display": "heading", "visualization_settings": {},
                                 "dataset_query": {}, "archived": False},
                "text": card["titulo"]}})
            continue
        card_id, variaveis = cards_criados[card["arquivo"]]
        ligacoes = [{"parameter_id": f"filtro_{nome}", "card_id": card_id,
                     "target": ["variable", ["template-tag", nome]]} for nome in variaveis]
        dashcards.append({**base, "card_id": card_id, "parameter_mappings": ligacoes, "visualization_settings": {}})

    mb.put(f"/api/dashboard/{dashboard['id']}", {"parameters": parametros, "dashcards": dashcards})
    return dashboard["id"]


def main():
    url = os.getenv("MB_URL", "http://localhost:3000")
    usuario, senha = os.getenv("MB_USUARIO"), os.getenv("MB_SENHA")
    if not (usuario and senha):
        sys.exit("Defina MB_USUARIO e MB_SENHA com o login de administrador do Metabase.")

    painel = json.loads((RAIZ / "metabase" / "painel.json").read_text(encoding="utf-8"))
    mb = Metabase(url, usuario, senha)
    banco_id = achar_banco(mb)
    colecao_id = preparar_colecao(mb, painel["colecao"])
    arquivar_versao_anterior(mb, colecao_id, painel["nome"])

    cards_criados = {}
    for card in painel["cards"]:
        if "arquivo" in card:
            cards_criados[card["arquivo"]] = criar_card(mb, card, banco_id, colecao_id, painel)
            print(f"card criado: {card['nome']}")

    dashboard_id = criar_dashboard(mb, painel, colecao_id, cards_criados)
    print(f"\nPainel pronto: {url}/dashboard/{dashboard_id}")


if __name__ == "__main__":
    main()
