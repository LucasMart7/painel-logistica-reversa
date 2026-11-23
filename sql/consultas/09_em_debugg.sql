-- Equipamentos em debugg (problema de firmware ou configuração).
SELECT COUNT(*) AS total
FROM vw_itens_reversa
WHERE situacao = 'Debugg'
  [[AND modelo = {{modelo}}]]
  [[AND grupo = {{grupo}}]]
  [[AND situacao = {{situacao}}]]
