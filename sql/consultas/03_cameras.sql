-- Itens em reversa do grupo Câmeras.
SELECT COUNT(*) AS total
FROM vw_itens_reversa
WHERE grupo = 'Câmeras'
  [[AND modelo = {{modelo}}]]
  [[AND grupo = {{grupo}}]]
  [[AND situacao = {{situacao}}]]
