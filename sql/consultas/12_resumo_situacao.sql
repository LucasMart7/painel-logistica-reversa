-- Resumo da triagem por modelo, com percentuais separados de dano e debugg.
WITH itens AS (
  SELECT modelo, situacao
  FROM vw_itens_reversa
  WHERE grupo IN ('Rastreadores', 'Câmeras')
    [[AND modelo = {{modelo}}]]
    [[AND grupo = {{grupo}}]]
    [[AND situacao = {{situacao}}]]
)
SELECT c.modelo                                                   AS "Modelo",
       COUNT(i.modelo)                                            AS "Na reversa",
       COUNT(i.modelo) FILTER (WHERE i.situacao = 'Danificado')   AS "Danificados",
       COUNT(i.modelo) FILTER (WHERE i.situacao = 'Debugg')       AS "Debugg",
       COUNT(i.modelo) FILTER (WHERE i.situacao = 'Não triado')   AS "Não triado",
       ROUND(100.0 * COUNT(i.modelo) FILTER (WHERE i.situacao = 'Danificado') / NULLIF(COUNT(i.modelo), 0), 1) AS "% danificado",
       ROUND(100.0 * COUNT(i.modelo) FILTER (WHERE i.situacao = 'Debugg')     / NULLIF(COUNT(i.modelo), 0), 1) AS "% em debugg"
FROM vw_catalogo_modelos c
LEFT JOIN itens i ON i.modelo = c.modelo
WHERE c.grupo IN ('Rastreadores', 'Câmeras')
GROUP BY c.modelo, c.ordem
ORDER BY c.ordem
