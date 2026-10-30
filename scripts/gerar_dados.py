"""Gera site/precos.json a partir da planilha dados/precos.xlsx.

Uso:
  python3 scripts/gerar_dados.py             gera site/precos.json
  python3 scripts/gerar_dados.py --conferir  só confere: falha se site/precos.json não bater
                                             com a planilha (usado no GitHub Actions)

A planilha tem uma aba com as colunas, nesta ordem:
  Procedimento | Especialidade | Preço máximo | ATE 10X | PIX | Preço Black Friday | Observação
"ATE 10X" costuma ser fórmula (PIX + 12%); vale o valor calculado que o Excel salvou no arquivo.
Combos têm só o preço Black Friday.
"""
import json
import sys
import unicodedata
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / 'dados' / 'precos.xlsx'
DESTINO = RAIZ / 'site' / 'precos.json'
COLUNAS = ['Procedimento', 'Especialidade', 'Preço máximo (R$)', 'ATE 10X', 'PIX', 'Preço Black Friday (R$)', 'Observação']


def chave(nome):
    s = unicodedata.normalize('NFD', nome.replace('–', '-')).encode('ascii', 'ignore').decode()
    return ' '.join(s.upper().split())


def valor(v):
    return None if v is None or v == '' else round(float(v), 2)


def ler():
    aba = load_workbook(ORIGEM, data_only=True, read_only=True).worksheets[0]
    linhas = aba.iter_rows(values_only=True)
    cabecalho = [str(c).strip() if c is not None else '' for c in next(linhas)][:len(COLUNAS)]
    if cabecalho != COLUNAS:
        sys.exit(f'A planilha mudou de formato. Esperado {COLUNAS}, veio {cabecalho}')
    itens, erros = [], []
    for n, linha in enumerate(linhas, start=2):
        nome, esp, maximo, dez, pix, bf, obs = (list(linha) + [None] * 7)[:7]
        if not nome:
            continue
        # Sem PIX (combos) a fórmula do 10x dá zero: não há preço parcelado.
        item = {'n': str(nome).strip(), 'e': (esp or '').strip(), 'max': valor(maximo),
                'x10': valor(dez) if pix is not None else None, 'pix': valor(pix)}
        if valor(bf) is not None:
            item['bf'] = valor(bf)
        if obs:
            item['obs'] = str(obs).strip()
        if item['max'] is None and 'bf' not in item:
            erros.append(f'linha {n}: {nome} sem preço máximo e sem Black Friday')
        if pix is not None and dez is None:
            erros.append(f'linha {n}: {nome} tem PIX mas a coluna ATE 10X está vazia (abra e salve no Excel)')
        itens.append(item)
    repetidos = {i['n'] for i in itens if sum(chave(j['n']) == chave(i['n']) for j in itens) > 1}
    if repetidos:
        erros.append(f'itens repetidos: {sorted(repetidos)}')
    if erros:
        sys.exit('Problemas na planilha:\n  ' + '\n  '.join(erros))
    return sorted(itens, key=lambda i: chave(i['n']))


if __name__ == '__main__':
    itens = ler()
    if '--conferir' in sys.argv:
        publicado = json.loads(DESTINO.read_text(encoding='utf-8'))
        if publicado['itens'] != itens:
            sys.exit('site/precos.json não bate com dados/precos.xlsx: rode python3 scripts/gerar_dados.py')
        print(f'Todos os {len(itens)} itens batem com a planilha.')
    else:
        DESTINO.write_text(json.dumps({
            'atualizado': date.today().isoformat(),
            'fonte': 'Planilha de preços da clínica (base: tabelas do Clinicorp)',
            'itens': itens,
        }, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        print(f'{len(itens)} itens; {sum("bf" in i for i in itens)} com Black Friday')
