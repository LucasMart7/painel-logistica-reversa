-- Itens em reversa que ainda não passaram pela triagem.
SELECT COUNT(*) AS total
FROM vw_itens_reversa
WHERE situacao = 'Não triado'
  [[AND modelo = {{modelo}}]]
  [[AND grupo = {{grupo}}]]
  [[AND situacao = {{situacao}}]]
