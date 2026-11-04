# Tabela de preços — Royal Face Santos

Página de consulta: digita o produto ou procedimento e aparecem o preço em 10x, no PIX e em
dinheiro. Na página, a coluna "Preço máximo" da planilha aparece como "Em 10x", a "ATE 10X" como
"PIX" e a "PIX" como "Dinheiro". O preço de Black Friday fica na planilha, mas não aparece na
página (os combos, que só têm esse preço, também não).

Link: https://carlosaugustocavalcanti-sys.github.io/precos-clinica/

Dá para mandar o link já com a busca feita, por exemplo
`https://carlosaugustocavalcanti-sys.github.io/precos-clinica/?q=botox%20testa`.

## De onde vêm os preços

`dados/precos.xlsx` é a planilha da clínica, com uma aba e estas colunas:

| Coluna | O que é |
|---|---|
| Preço máximo (R$) | "Vl Sessão" da "1 - TABELA MAXIMA (NOVA)" do Clinicorp |
| ATE 10X | Valor total em até 10x (fórmula: PIX + 12%, taxa na célula H1). Quando passa do preço máximo, a página mostra o preço máximo |
| PIX | "Valor mínimo da Sessão" da Tabela Máxima do Clinicorp |
| Preço Black Friday (R$) | Tabela "BLACK FRIDAY 2026" do Clinicorp |
| Observação | Nome usado na Black Friday quando é diferente, ou os dois preços do Harmonyca |

## Atualizar os preços

1. Edite a planilha no Excel (mesmas colunas, mesma ordem) e salve como `dados/precos.xlsx`.
2. `python3 scripts/gerar_dados.py` (precisa de `openpyxl`). O script para com erro se a planilha
   mudar de formato, se tiver item repetido ou item sem preço.
3. Commit e push na `main`: o workflow `.github/workflows/pages.yml` confere a página contra a
   planilha e publica a pasta `site/`.

Para ver no computador: `python3 -m http.server 4300 --directory site` e abra http://localhost:4300.
