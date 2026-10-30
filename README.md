# Tabela de preços — Royal Face Santos

Página de consulta: digita o produto ou procedimento e aparecem o preço máximo, o mínimo e o
de Black Friday.

Link: https://carlosaugustocavalcanti-sys.github.io/precos-clinica/

Dá para mandar o link já com a busca feita, por exemplo
`https://carlosaugustocavalcanti-sys.github.io/precos-clinica/?q=botox%20testa`
(com `&bf=1` mostra só o que tem preço de Black Friday).

## De onde vêm os preços

`dados/clinicorp.json` é a leitura, linha a linha, das tabelas de preço do Clinicorp
(Configurações → Procedimentos → Tabelas de preço), com a data e hora da leitura em `lidoEm`.

| Tabela no Clinicorp | Vira na página |
|---|---|
| 1 - TABELA MAXIMA (NOVA) | Máximo ("Vl Sessão") e Mínimo ("Valor mínimo da Sessão") |
| BLACK FRIDAY 2026 | Black Friday ("Vl Sessão") e o mínimo dela, quando é diferente |
| 3 - TABELA HOME CARE | Produtos de revenda, só com o preço cheio |

Cada linha da Black Friday é ligada ao item da Tabela Máxima de mesmo nome. Quando o nome é diferente
(ex.: "SCULPTRA - BIOESTIMULADOR FACIAL / CORPORAL", "03 FIOS FILLER", "HARMONYCA (1 seringa)"), a
ligação está escrita em `LIGACOES` dentro de `scripts/gerar_dados.py`, e a página mostra o nome usado
na Black Friday embaixo do item. Só os 10 combos existem apenas na Black Friday.

## Atualizar os preços

1. Leia de novo as tabelas no Clinicorp e grave em `dados/clinicorp.json` (mesmo formato).
2. `python3 scripts/gerar_dados.py`. O script para com erro se alguma linha da Black Friday ficar
   sem item ou se algum preço da página não bater com o Clinicorp.
3. Commit e push na `main`: o workflow `.github/workflows/pages.yml` roda a mesma conferência e
   publica a pasta `site/`.

Para ver no computador: `python3 -m http.server 4300 --directory site` e abra http://localhost:4300.
