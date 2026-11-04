"""Gera site/precos.json a partir da planilha dados/precos.xlsx.

Uso:
  python3 scripts/gerar_dados.py             gera site/precos.json
  python3 scripts/gerar_dados.py --conferir  só confere: falha se site/precos.json não bater
                                             com a planilha (usado no GitHub Actions)

A planilha tem uma aba com as colunas, nesta ordem:
  Procedimento | Especialidade | Preço máximo | ATE 10X | PIX | Preço Black Friday | Observação
"ATE 10X" costuma ser fórmula (PIX + 12%); vale o valor calculado que o Excel salvou no arquivo,
limitado ao preço máximo quando passa dele.
Combos têm só o preço Black Friday.

A seção Black Friday da página vem de dados/black-friday.json, digitado a partir da tabela impressa:
cada item tem nome (n), grupo, inclui, nota e os três preços: dinheiro, pix e parcela (valor de
cada uma das 10 parcelas).
"""
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / 'dados' / 'precos.xlsx'
BLACK_FRIDAY = RAIZ / 'dados' / 'black-friday.json'
DESTINO = RAIZ / 'site' / 'precos.json'
COLUNAS = ['Procedimento', 'Especialidade', 'Preço máximo (R$)', 'ATE 10X', 'PIX', 'Preço Black Friday (R$)', 'Observação']


def chave(nome):
    s = unicodedata.normalize('NFD', nome.replace('–', '-')).encode('ascii', 'ignore').decode()
    return ' '.join(s.upper().split())


def valor(v):
    return None if v is None or v == '' else round(float(v), 2)


def calcular_10x(formulas, valores):
    """Valores da coluna ATE 10X. Quando a planilha foi salva fora do Excel a fórmula vem sem o
    valor calculado; aí a fórmula padrão (=E2+E2*$H$1) é calculada aqui."""
    taxa = formulas['H1'].value
    saida = {}
    for f, v in zip(formulas['D'][1:], valores['D'][1:]):
        if v.value is None and isinstance(f.value, str):
            m = re.fullmatch(r'=E(\d+)\+E\1\*\$H\$1', f.value.replace(' ', ''))
            if not m:
                sys.exit(f'D{f.row}: fórmula diferente da padrão ({f.value}); abra e salve no Excel')
            pix = formulas[f'E{m.group(1)}'].value
            saida[f.row] = None if pix is None else pix + pix * taxa
        else:
            saida[f.row] = v.value
    return saida


def ler():
    formulas = load_workbook(ORIGEM).worksheets[0]
    aba = load_workbook(ORIGEM, data_only=True).worksheets[0]
    dez_calculado = calcular_10x(formulas, aba)
    linhas = aba.iter_rows(values_only=True)
    cabecalho = [str(c).strip() if c is not None else '' for c in next(linhas)][:len(COLUNAS)]
    if cabecalho != COLUNAS:
        sys.exit(f'A planilha mudou de formato. Esperado {COLUNAS}, veio {cabecalho}')
    itens, erros = [], []
    for n, linha in enumerate(linhas, start=2):
        nome, esp, maximo, dez, pix, bf, obs = (list(linha) + [None] * 7)[:7]
        dez = dez_calculado[n]
        if not nome:
            continue
        # Sem PIX (combos) a fórmula do 10x dá zero: não há preço parcelado.
        item = {'n': str(nome).strip(), 'e': (esp or '').strip(), 'max': valor(maximo),
                'x10': valor(dez) if pix is not None else None, 'pix': valor(pix)}
        # Regra da clínica: o parcelado nunca passa do preço máximo.
        if item['x10'] is not None and item['max'] is not None and item['x10'] > item['max']:
            item['x10'] = item['max']
        if valor(bf) is not None:
            item['bf'] = valor(bf)
        if obs:
            item['obs'] = str(obs).strip()
        if item['max'] is None and 'bf' not in item:
            erros.append(f'linha {n}: {nome} sem preço máximo e sem Black Friday')
        if pix is not None and dez is None:
            erros.append(f'linha {n}: {nome} tem PIX mas a coluna ATE 10X está vazia')
        itens.append(item)
    repetidos = {i['n'] for i in itens if sum(chave(j['n']) == chave(i['n']) for j in itens) > 1}
    if repetidos:
        erros.append(f'itens repetidos: {sorted(repetidos)}')
    if erros:
        sys.exit('Problemas na planilha:\n  ' + '\n  '.join(erros))
    return sorted(itens, key=lambda i: chave(i['n']))


def ler_black_friday():
    dados = json.loads(BLACK_FRIDAY.read_text(encoding='utf-8'))
    saida, erros = [], []
    for k, i in enumerate(dados['itens'], start=1):
        nome = str(i.get('n') or '').strip()
        if not nome:
            erros.append(f'item {k} sem nome')
            continue
        item = {'n': nome}
        for campo in ('grupo', 'nota'):
            if i.get(campo):
                item[campo] = str(i[campo]).strip()
        if i.get('inclui'):
            item['inclui'] = [str(x).strip() for x in i['inclui']]
        for campo in ('dinheiro', 'pix', 'parcela'):
            v = i.get(campo)
            if not isinstance(v, (int, float)) or v <= 0:
                erros.append(f'{nome}: preço "{campo}" vazio ou inválido ({v!r})')
            else:
                item[campo] = round(float(v), 2)
        saida.append(item)
    repetidos = {i['n'] for i in saida if sum(chave(j['n']) == chave(i['n']) for j in saida) > 1}
    if repetidos:
        erros.append(f'itens repetidos: {sorted(repetidos)}')
    if erros:
        sys.exit('Problemas em dados/black-friday.json:\n  ' + '\n  '.join(erros))
    return {'fonte': dados['fonte'], 'itens': saida}


if __name__ == '__main__':
    itens = ler()
    bf = ler_black_friday()
    if '--conferir' in sys.argv:
        publicado = json.loads(DESTINO.read_text(encoding='utf-8'))
        if publicado['itens'] != itens:
            sys.exit('site/precos.json não bate com dados/precos.xlsx: rode python3 scripts/gerar_dados.py')
        if publicado.get('blackFriday') != bf:
            sys.exit('site/precos.json não bate com dados/black-friday.json: rode python3 scripts/gerar_dados.py')
        print(f'Todos os {len(itens)} itens batem com a planilha e os {len(bf["itens"])} da Black Friday também.')
    else:
        DESTINO.write_text(json.dumps({
            'atualizado': date.today().isoformat(),
            'fonte': 'Planilha de preços da clínica (base: tabelas do Clinicorp)',
            'itens': itens,
            'blackFriday': bf,
        }, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        print(f'{len(itens)} itens na tabela; {len(bf["itens"])} na seção Black Friday')
