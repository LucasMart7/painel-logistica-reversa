-- Participação de cada grupo no total em reversa.
SELECT grupo AS "Grupo", COUNT(*) AS "Quantidade"
FROM vw_itens_reversa
WHERE TRUE
  [[AND modelo = {{modelo}}]]
  [[AND grupo = {{grupo}}]]
  [[AND situacao = {{situacao}}]]
GROUP BY grupo
ORDER BY 2 DESC
