-- Itens em reversa por modelo, incluindo modelos zerados.
WITH itens AS (
  SELECT modelo
  FROM vw_itens_reversa
  WHERE TRUE
    [[AND modelo = {{modelo}}]]
    [[AND grupo = {{grupo}}]]
    [[AND situacao = {{situacao}}]]
)
SELECT c.modelo AS "Modelo", c.grupo AS "Grupo", COUNT(i.modelo) AS "Quantidade"
FROM vw_catalogo_modelos c
LEFT JOIN itens i ON i.modelo = c.modelo
GROUP BY c.modelo, c.grupo, c.ordem
ORDER BY c.ordem
