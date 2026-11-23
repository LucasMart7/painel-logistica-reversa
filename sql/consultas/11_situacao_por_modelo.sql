-- Situação de triagem por modelo (barra empilhada).
-- Leitores ficam de fora: a planilha de triagem só cobre rastreadores e câmeras.
WITH itens AS (
  SELECT modelo, situacao
  FROM vw_itens_reversa
  WHERE grupo IN ('Rastreadores', 'Câmeras')
    [[AND modelo = {{modelo}}]]
    [[AND grupo = {{grupo}}]]
    [[AND situacao = {{situacao}}]]
)
SELECT c.modelo AS "Modelo", s.situacao AS "Situação", COUNT(i.modelo) AS "Quantidade"
FROM vw_catalogo_modelos c
CROSS JOIN (VALUES ('Não triado', 1), ('Debugg', 2), ('Danificado', 3)) AS s(situacao, ordem)
LEFT JOIN itens i ON i.modelo = c.modelo AND i.situacao = s.situacao
WHERE c.grupo IN ('Rastreadores', 'Câmeras')
GROUP BY c.modelo, c.ordem, s.situacao, s.ordem
ORDER BY c.ordem, s.ordem
