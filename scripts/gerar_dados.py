"""Gera a base fictícia usada pelo painel.

Produz:
  db/02_dados_ficticios.sql   carga inicial do Postgres (equipamentos, acessórios e triagem)
  dados/triagem_exemplo.csv   a mesma triagem no formato exportado da planilha

Os volumes e proporções são inventados. A semente é fixa para o resultado
ser reproduzível: rodar de novo gera exatamente os mesmos arquivos.
"""

import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SEMENTE = 2026
DIAS_DE_HISTORICO = 60

# modelo: (tipo, quantidade em reversa, quantidade fora da reversa, fração triada)
EQUIPAMENTOS = {
    "trk310": ("rastreador", 480, 900, 0.40),
    "trk220": ("rastreador", 210, 300, 0.85),
    "trk100": ("rastreador", 95, 400, 0.00),
    "cam410": ("camera", 650, 1200, 0.14),
    "cam370": ("camera", 160, 250, 0.00),
    "cam450": ("camera", 230, 700, 0.12),
}

# (geração, tipo, quantidade em reversa, quantidade fora da reversa)
LEITORES = [
    ("Vega", "leitor_rfid_senha", 420, 2500),
    ("Vega", "leitor_rfid", 330, 1100),
    ("Orion", "leitor_rfid_senha", 540, 900),
    ("Orion", "leitor_rfid", 1500, 2600),
]

POSSES_FORA_DA_REVERSA = ["cliente", "cliente", "cliente", "estoque", "tecnico"]

CAUSAS = {
    "Debugg": ["Falha de configuração", "Sem comunicação", "Firmware desatualizado"],
    "Dano fisico": ["Dano mecânico", "Oxidação", "Conector quebrado"],
    "Componente ausente": ["Componente periférico ausente", "Sem antena"],
}


def gerar_imei(rng, usados):
    while True:
        imei = "86" + "".join(rng.choice("0123456789") for _ in range(13))
        if imei not in usados:
            usados.add(imei)
            return imei


def data_de_entrada(rng, hoje):
    # Mais entradas recentes do que antigas, como numa fila real.
    dias_atras = min(int(rng.expovariate(1 / 18)), DIAS_DE_HISTORICO)
    hora = rng.randint(8, 18)
    return (hoje - timedelta(days=dias_atras)).replace(hour=hora, minute=rng.randint(0, 59))


def sorteia_status_triagem(rng, modelo):
    # O trk220 é o modelo problemático da história: quase tudo em debugg.
    if modelo == "trk220":
        return rng.choices(["Debugg", "Dano fisico", "Componente ausente"], [0.72, 0.2, 0.08])[0]
    return rng.choices(["Debugg", "Dano fisico", "Componente ausente"], [0.6, 0.37, 0.03])[0]


def gerar(hoje=None):
    rng = random.Random(SEMENTE)
    hoje = hoje or datetime.now(timezone.utc).replace(second=0, microsecond=0)
    imeis_usados = set()
    equipamentos, acessorios, triagem = [], [], []

    for modelo, (tipo, em_reversa, fora, fracao_triada) in EQUIPAMENTOS.items():
        for i in range(em_reversa + fora):
            na_reversa = i < em_reversa
            imei = gerar_imei(rng, imeis_usados)
            posse = "logistica_reversa" if na_reversa else rng.choice(POSSES_FORA_DA_REVERSA)
            quando = data_de_entrada(rng, hoje) if na_reversa else hoje - timedelta(days=rng.randint(61, 400))
            equipamentos.append((imei, modelo, tipo, posse, quando))
            if na_reversa and rng.random() < fracao_triada:
                status = sorteia_status_triagem(rng, modelo)
                triagem.append((imei, modelo.upper(), rng.choice(CAUSAS[status]), status, "Logística reversa"))

    # Ruídos que a planilha real também tinha: IMEIs repetidos com status
    # diferentes e aparelhos que a planilha diz estar na reversa, mas o sistema não.
    for linha in rng.sample(triagem, 8):
        triagem.append((linha[0], linha[1], "Dano mecânico", "Dano fisico", linha[4]))
    fora_da_reversa = [e for e in equipamentos if e[3] != "logistica_reversa"]
    for imei, modelo, *_ in rng.sample(fora_da_reversa, 25):
        triagem.append((imei, modelo.upper(), "Falha de configuração", "Debugg", "Logística reversa"))

    for geracao, tipo, em_reversa, fora in LEITORES:
        for i in range(em_reversa + fora):
            na_reversa = i < em_reversa
            if geracao == "Vega":
                serie, observacao = "20" + "".join(rng.choice("0123456789ABCDEF") for _ in range(18)), "vega"
            else:
                serie = str(rng.choice([23, 24, 25])) + "".join(rng.choice("0123456789") for _ in range(6))
                observacao = rng.choice([None] * 12 + ["lote 2024-B"])
            posse = "logistica_reversa" if na_reversa else rng.choice(POSSES_FORA_DA_REVERSA)
            quando = data_de_entrada(rng, hoje) if na_reversa else hoje - timedelta(days=rng.randint(61, 400))
            # O legado saiu de linha: nada dele entra na reversa nas últimas semanas.
            if geracao == "Orion" and na_reversa:
                quando = hoje - timedelta(days=rng.randint(30, 300))
            acessorios.append((serie, tipo, observacao, posse, quando))

    for i in range(1200):
        acessorios.append((f"BZ{i:06d}", "buzzer", None, rng.choice(POSSES_FORA_DA_REVERSA + ["logistica_reversa"]),
                           hoje - timedelta(days=rng.randint(1, 300))))

    return equipamentos, acessorios, triagem


def literal(valor):
    if valor is None:
        return "NULL"
    if isinstance(valor, datetime):
        return f"'{valor.isoformat()}'"
    return "'" + str(valor).replace("'", "''") + "'"


def inserts(tabela, colunas, linhas, lote=500):
    for inicio in range(0, len(linhas), lote):
        valores = ",\n".join("(" + ", ".join(literal(v) for v in linha) + ")" for linha in linhas[inicio:inicio + lote])
        yield f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES\n{valores};\n"


def main():
    equipamentos, acessorios, triagem = gerar()

    equipamentos_sql = [(imei, modelo, tipo, posse, quando, quando) for imei, modelo, tipo, posse, quando in equipamentos]
    acessorios_sql = [(serie, tipo, obs, posse, quando, quando) for serie, tipo, obs, posse, quando in acessorios]

    with open(RAIZ / "db" / "02_dados_ficticios.sql", "w", encoding="utf-8") as saida:
        saida.write("-- Gerado por scripts/gerar_dados.py. Dados 100% fictícios.\n\n")
        for bloco in inserts("equipamentos", ["imei", "modelo", "tipo", "posse", "criado_em", "atualizado_em"], equipamentos_sql):
            saida.write(bloco)
        for bloco in inserts("acessorios", ["numero_serie", "tipo", "observacao", "posse", "criado_em", "atualizado_em"], acessorios_sql):
            saida.write(bloco)
        for bloco in inserts("triagem", ["imei", "modelo", "causa", "status", "posse"], triagem):
            saida.write(bloco)

    with open(RAIZ / "dados" / "triagem_exemplo.csv", "w", encoding="utf-8", newline="") as saida:
        escritor = csv.writer(saida)
        escritor.writerow(["IMEI", "Modelo", "Causa", "Status", "Posse"])
        escritor.writerows(triagem)

    print(f"{len(equipamentos)} equipamentos, {len(acessorios)} acessórios, {len(triagem)} linhas de triagem")


if __name__ == "__main__":
    main()
