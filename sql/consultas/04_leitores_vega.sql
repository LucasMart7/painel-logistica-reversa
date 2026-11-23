-- Itens em reversa do grupo Leitores Vega.
SELECT COUNT(*) AS total
FROM vw_itens_reversa
WHERE grupo = 'Leitores Vega'
  [[AND modelo = {{modelo}}]]
  [[AND grupo = {{grupo}}]]
  [[AND situacao = {{situacao}}]]
