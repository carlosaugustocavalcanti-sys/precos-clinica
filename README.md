# Tabela de preços — Royal Face Santos

Página de consulta: digita o produto ou procedimento e aparecem o preço máximo, o mínimo e o
de Black Friday.

Link: https://carlosaugustocavalcanti-sys.github.io/precos-clinica/

Dá para mandar o link já com a busca feita, por exemplo
`https://carlosaugustocavalcanti-sys.github.io/precos-clinica/?q=botox%20testa`
(com `&bf=1` mostra só o que tem preço de Black Friday).

## De onde vêm os preços

Das tabelas de preço do Clinicorp (Configurações → Procedimentos → Tabelas de preço):

| Tabela no Clinicorp | Vira na página |
|---|---|
| 1 - TABELA MAXIMA (NOVA) | Máximo ("Vl Sessão") e Mínimo ("Valor mínimo da Sessão") |
| BLACK FRIDAY 2026 | Black Friday ("Vl Sessão") e o mínimo dela, quando é diferente |
| 3 - TABELA HOME CARE | Produtos de revenda, só com o preço cheio |

Os nomes são juntados exatamente (sem diferenciar maiúsculas, acentos e travessões). Itens da Black
Friday com nome diferente da Tabela Máxima (combos, "FIO FILLER" x "FIO FILLER/MULTI-FILL" etc.)
aparecem como itens próprios, sem máximo e mínimo, para não juntar dois procedimentos por engano.

## Atualizar os preços

1. Exporte de novo as tabelas para `dados/Tabela-de-Precos-Clinicorp.xlsx` (abas `1 - Máxima`,
   `Black Friday 2026`, `Home Care`; colunas Procedimento, Especialidade, Preço máximo, Preço mínimo).
2. `python3 scripts/gerar_dados.py` (precisa de `openpyxl`).
3. Commit e push na `main`: o workflow `.github/workflows/pages.yml` publica a pasta `site/`.

Para ver no computador: `python3 -m http.server 4300 --directory site` e abra http://localhost:4300.
