"""Gera site/precos.json a partir da planilha exportada do Clinicorp.

Uso: python3 scripts/gerar_dados.py [dados/Tabela-de-Precos-Clinicorp.xlsx]

Junta a aba "1 - Máxima" (preço máximo e mínimo) com a aba "Black Friday 2026"
pelo nome do procedimento, ignorando maiúsculas, acentos e espaços repetidos.
Itens que só existem na Black Friday (combos, nomes diferentes) entram sozinhos.
A aba "Home Care" entra como produto de revenda, só com o preço cheio.
A aba "Bonificado" fica de fora: é tudo R$ 0,00.
"""
import json
import sys
import unicodedata
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / 'dados' / 'Tabela-de-Precos-Clinicorp.xlsx'
DESTINO = RAIZ / 'site' / 'precos.json'

# Nomes que vêm com erro de digitação do Clinicorp.
CORRECOES = {
    '(ALLERGAN) BOTOX - TOXINA BOTULÍNICA SUDORESEBOTOX - TOXINA BOTULÍNICA SUDORESE':
        '(ALLERGAN) BOTOX - TOXINA BOTULÍNICA SUDORESE',
}


def chave(nome):
    s = nome.replace('–', '-').replace('—', '-')
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode()
    return ' '.join(s.upper().split())


def ler(aba):
    linhas = []
    for nome, esp, maximo, minimo in aba.iter_rows(min_row=2, max_col=4, values_only=True):
        if not nome:
            continue
        nome = CORRECOES.get(nome.strip(), nome.strip())
        linhas.append((nome, (esp or '').strip(), maximo or 0, minimo or 0))
    return linhas


wb = load_workbook(ORIGEM, read_only=True)
itens = {}
for nome, esp, maximo, minimo in ler(wb['1 - Máxima']):
    itens[chave(nome)] = {'n': nome, 'e': esp, 'max': maximo, 'min': minimo or None}

so_black = 0
for nome, esp, maximo, minimo in ler(wb['Black Friday 2026']):
    item = itens.get(chave(nome))
    if item is None:
        item = itens[chave(nome)] = {'n': nome, 'e': esp, 'max': None, 'min': None}
        so_black += 1
    item['bf'] = maximo
    if minimo and minimo != maximo:
        item['bfMin'] = minimo

for nome, esp, maximo, _ in ler(wb['Home Care']):
    itens.setdefault(chave(nome), {'n': nome.replace('[MERC]', '').strip(), 'e': 'HOME CARE',
                                   'max': maximo, 'min': None})

lista = sorted(itens.values(), key=lambda i: chave(i['n']))
DESTINO.write_text(json.dumps({
    'atualizado': date.today().isoformat(),
    'fonte': 'Clinicorp: tabelas "1 - Tabela Máxima (Nova)", "Black Friday 2026" e "3 - Tabela Home Care"',
    'itens': lista,
}, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

com_bf = sum(1 for i in lista if 'bf' in i)
print(f'{len(lista)} itens; {com_bf} com Black Friday ({so_black} só na Black Friday)')
