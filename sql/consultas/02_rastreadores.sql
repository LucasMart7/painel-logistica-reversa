-- Itens em reversa do grupo Rastreadores.
SELECT COUNT(*) AS total
FROM vw_itens_reversa
WHERE grupo = 'Rastreadores'
  [[AND modelo = {{modelo}}]]
  [[AND grupo = {{grupo}}]]
  [[AND situacao = {{situacao}}]]
