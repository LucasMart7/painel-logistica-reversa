-- Equipamentos danificados (dano físico ou componente ausente) em reversa.
SELECT COUNT(*) AS total
FROM vw_itens_reversa
WHERE situacao = 'Danificado'
  [[AND modelo = {{modelo}}]]
  [[AND grupo = {{grupo}}]]
  [[AND situacao = {{situacao}}]]
