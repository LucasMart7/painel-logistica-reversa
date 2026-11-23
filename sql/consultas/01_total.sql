-- Total de itens em logística reversa.
SELECT COUNT(*) AS total
FROM vw_itens_reversa
WHERE TRUE
  [[AND modelo = {{modelo}}]]
  [[AND grupo = {{grupo}}]]
  [[AND situacao = {{situacao}}]]
