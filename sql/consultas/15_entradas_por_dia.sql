-- Entradas em reversa por dia e grupo nos últimos 14 dias, com os dias sem entrada.
WITH itens AS (
  SELECT grupo, (entrou_em AT TIME ZONE 'America/Sao_Paulo')::date AS dia
  FROM vw_itens_reversa
  WHERE TRUE
    [[AND modelo = {{modelo}}]]
    [[AND grupo = {{grupo}}]]
    [[AND situacao = {{situacao}}]]
),
dias AS (
  SELECT generate_series((now() AT TIME ZONE 'America/Sao_Paulo')::date - 13,
                         (now() AT TIME ZONE 'America/Sao_Paulo')::date,
                         interval '1 day')::date AS dia
),
grupos AS (SELECT DISTINCT grupo FROM vw_catalogo_modelos)
SELECT to_char(d.dia, 'DD/MM') AS "Dia", g.grupo AS "Grupo", NULLIF(COUNT(i.dia), 0) AS "Quantidade"
FROM dias d
CROSS JOIN grupos g
LEFT JOIN itens i ON i.dia = d.dia AND i.grupo = g.grupo
GROUP BY d.dia, g.grupo
ORDER BY d.dia, g.grupo
