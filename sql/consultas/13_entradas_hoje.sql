-- Itens que entraram em reversa hoje (fuso de São Paulo).
SELECT COUNT(*) AS total
FROM vw_itens_reversa
WHERE (entrou_em AT TIME ZONE 'America/Sao_Paulo')::date = (now() AT TIME ZONE 'America/Sao_Paulo')::date
  [[AND modelo = {{modelo}}]]
  [[AND grupo = {{grupo}}]]
  [[AND situacao = {{situacao}}]]
