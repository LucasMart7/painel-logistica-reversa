-- Itens em reversa do grupo Leitores Orion.
SELECT COUNT(*) AS total
FROM vw_itens_reversa
WHERE grupo = 'Leitores Orion'
  [[AND modelo = {{modelo}}]]
  [[AND grupo = {{grupo}}]]
  [[AND situacao = {{situacao}}]]
