"""Gera site/precos.json a partir de dados/clinicorp.json (leitura das tabelas de preço do Clinicorp).

Uso:
  python3 scripts/gerar_dados.py             gera site/precos.json
  python3 scripts/gerar_dados.py --conferir  só confere: falha se site/precos.json não bater
                                             com dados/clinicorp.json (usado no GitHub Actions)

Regras:
- Máximo e mínimo vêm da "1 - TABELA MAXIMA (NOVA)" (colunas "Vl Sessão" e "Valor mínimo da Sessão").
- Black Friday vem da "BLACK FRIDAY 2026". Cada linha dela é ligada ao item da Tabela Máxima de
  mesmo nome (sem diferenciar maiúsculas, acentos e travessões) ou, quando o nome é diferente, pela
  lista LIGACOES abaixo. Uma linha pode valer para mais de um item ("FACIAL / CORPORAL").
- Os combos só existem na Black Friday e entram sozinhos.
- "3 - TABELA HOME CARE" entra como produto de revenda (o Clinicorp não tem mínimo para eles).
- "2 - TABELA BONIFICADO" fica de fora: é tudo R$ 0,00.
O script para com erro se alguma linha da Black Friday ficar sem item ou se uma ligação apontar
para um nome que não existe, para nunca publicar preço trocado ou faltando.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / 'dados' / 'clinicorp.json'
DESTINO = RAIZ / 'site' / 'precos.json'

MAXIMA = '1 - TABELA MAXIMA (NOVA)'
BLACK = 'BLACK FRIDAY 2026'
HOME_CARE = '3 - TABELA HOME CARE'

# Nomes com erro de digitação no Clinicorp.
CORRECOES = {
    '(ALLERGAN) BOTOX - TOXINA BOTULÍNICA SUDORESEBOTOX - TOXINA BOTULÍNICA SUDORESE':
        '(ALLERGAN) BOTOX - TOXINA BOTULÍNICA SUDORESE',
}

# Linha da Black Friday -> itens da Tabela Máxima, quando o nome não é igual.
# Os fios "FILLER" e "LISO/MONO AGULHA I-THREAD" são tratados em ligacoes_de_fios().
LIGACOES = {
    'ELLEVA - FACE E PESCOÇO (210MG)': ['ELLEVA - FACE (210MG)'],
    'HARMONYCA - BIOESTIMULADOR E PREENCHEDOR (1 seringa)': ['HARMONYCA - BIOESTIMULADOR E PREENCHEDOR'],
    'HARMONYCA - BIOESTIMULADOR E PREENCHEDOR (2 seringas)': ['HARMONYCA - BIOESTIMULADOR E PREENCHEDOR'],
    'JUVEDERM PREENCHIMENTO MANDIBULA/QUEIXO (2ML)': ['JUVEDERM PREENCHIMENTO MANDIBULA (2ML)'],
    'RENNOVA PREENCHIMENTO BIGODE CHINÊS / MARIONETE (1ML)': [
        'RENNOVA PREENCHIMENTO BIGODE CHINÊS (1ML)', 'RENNOVA PREENCHIMENTO MARIONETE (1ML)'],
    'RENNOVA PREENCHIMENTO MANDIBULA /QUEIXO (1ML)': [
        'RENNOVA PREENCHIMENTO MANDIBULA (1ML)', 'RENNOVA PREENCHIMENTO QUEIXO (1ML)'],
    'RESTYLANE LYFT LIDO PREENCHIMENTO MALAR (1ML)': ['RESTYLANE PREENCHIMENTO MALAR (1ML)'],
    'SCULPTRA - BIOESTIMULADOR FACIAL / CORPORAL': [
        'SCULPTRA - BIOESTIMULADOR FACIAL', 'SCULPTRA - BIOESTIMULADOR CORPORAL'],
    'XEOMIN - TOXINA BOTULÍNICA 3 REGIÕES (200UI)': ['XEOMIN - TOXINA BOTULÍNICA 3 REGIÕES'],
}

# Quando há mais de uma linha da Black Friday para o mesmo item, o rótulo que separa uma da outra.
ROTULOS = {
    'HARMONYCA - BIOESTIMULADOR E PREENCHEDOR (1 seringa)': '1 seringa',
    'HARMONYCA - BIOESTIMULADOR E PREENCHEDOR (2 seringas)': '2 seringas',
}


def chave(nome):
    s = nome.replace('–', '-').replace('—', '-')
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode()
    return ' '.join(s.upper().split())


def ligacoes_de_fios(nome):
    """'... 03 FIOS FILLER' -> '... 03 FIOS FILLER/MULTI-FILL'; '... LISO/MONO AGULHA I-THREAD' -> '... LISO/MONO'."""
    if re.fullmatch(r'APLICAÇÃO FIOS DE PDO - \d\d FIOS? FILLER', nome):
        return [nome + '/MULTI-FILL']
    if nome.endswith(' LISO/MONO AGULHA I-THREAD'):
        return [nome.removesuffix(' AGULHA I-THREAD')]
    return None


def real(texto):
    return float(texto.replace('R$', '').strip().replace('.', '').replace(',', '.'))


def linhas(tabela):
    """Linhas da tabela sem repetição exata (o Clinicorp tem um item cadastrado duas vezes na Black Friday)."""
    vistas, saida = set(), []
    for nome, esp, maximo, minimo in tabela:
        nome = CORRECOES.get(nome.strip(), nome.strip())
        linha = (nome, esp.strip(), real(maximo), real(minimo))
        if linha not in vistas:
            vistas.add(linha)
            saida.append(linha)
    return saida


def gerar(fonte):
    tabelas = fonte['tabelas']
    itens = {}
    for nome, esp, maximo, minimo in linhas(tabelas[MAXIMA]):
        # Mínimo R$ 0,00 com máximo acima de zero = mínimo não cadastrado.
        itens[chave(nome)] = {'n': nome, 'e': esp, 'max': maximo, 'min': minimo if minimo or not maximo else None}

    sem_item = []
    for nome, esp, maximo, minimo in linhas(tabelas[BLACK]):
        oferta = {'p': maximo}
        if minimo and minimo != maximo:
            oferta['min'] = minimo
        if nome in ROTULOS:
            oferta['r'] = ROTULOS[nome]
        if chave(nome) in itens:
            destinos = [chave(nome)]
        else:
            ligados = LIGACOES.get(nome) or ligacoes_de_fios(nome)
            if ligados is None:
                if esp != 'COMBO':
                    sem_item.append(nome)
                itens[chave(nome)] = {'n': nome, 'e': esp, 'max': None, 'min': None, 'soBf': True}
                destinos = [chave(nome)]
            else:
                faltando = [d for d in ligados if chave(d) not in itens]
                if faltando:
                    sys.exit(f'Ligação para item que não existe na Tabela Máxima: {nome} -> {faltando}')
                destinos = [chave(d) for d in ligados]
                oferta['como'] = nome
        for d in destinos:
            itens[d].setdefault('bf', []).append(oferta)
    if sem_item:
        sys.exit('Itens da Black Friday sem item na Tabela Máxima (inclua em LIGACOES):\n  ' + '\n  '.join(sem_item))

    for nome, esp, maximo, minimo in linhas(tabelas[HOME_CARE]):
        nome = nome.replace('[MERC]', '').strip()
        itens[chave(nome)] = {'n': nome, 'e': 'HOME CARE', 'max': maximo, 'min': minimo or None}

    for item in itens.values():
        item.get('bf', []).sort(key=lambda o: o['p'])
    return {
        'atualizado': fonte['lidoEm'][:10],
        'fonte': 'Clinicorp: tabelas "1 - Tabela Máxima (Nova)", "Black Friday 2026" e "3 - Tabela Home Care"',
        'itens': sorted(itens.values(), key=lambda i: chave(i['n'])),
    }


def conferir(fonte, dados):
    """Confere cada preço do Clinicorp contra o que a página vai mostrar."""
    erros = []
    por_nome = {chave(i['n']): i for i in dados['itens']}
    for nome, esp, maximo, minimo in linhas(fonte['tabelas'][MAXIMA]):
        i = por_nome.get(chave(nome))
        esperado_min = minimo if minimo or not maximo else None
        if not i or i['max'] != maximo or i['min'] != esperado_min:
            erros.append(f'Máxima: {nome} {maximo}/{minimo} -> {i and (i["max"], i["min"])}')
    for nome, esp, maximo, minimo in linhas(fonte['tabelas'][BLACK]):
        alvos = [nome] if chave(nome) in por_nome else (LIGACOES.get(nome) or ligacoes_de_fios(nome) or [])
        for alvo in alvos:
            ofertas = por_nome.get(chave(alvo), {}).get('bf', [])
            if not any(o['p'] == maximo and o.get('min', maximo) == (minimo or maximo) for o in ofertas):
                erros.append(f'Black Friday: {nome} {maximo}/{minimo} não aparece em {alvo}')
        if not alvos:
            erros.append(f'Black Friday: {nome} sem item')
    for nome, esp, maximo, minimo in linhas(fonte['tabelas'][HOME_CARE]):
        i = por_nome.get(chave(nome.replace('[MERC]', '').strip()))
        if not i or i['max'] != maximo:
            erros.append(f'Home Care: {nome} {maximo}')
    return erros


if __name__ == '__main__':
    fonte = json.loads(ORIGEM.read_text(encoding='utf-8'))
    dados = gerar(fonte)
    erros = conferir(fonte, dados)
    if erros:
        sys.exit('Preços que não batem com o Clinicorp:\n  ' + '\n  '.join(erros))
    texto = json.dumps(dados, ensure_ascii=False, separators=(',', ':'))
    if '--conferir' in sys.argv:
        if DESTINO.read_text(encoding='utf-8') != texto:
            sys.exit('site/precos.json está desatualizado: rode python3 scripts/gerar_dados.py')
        print('Todos os preços batem com o Clinicorp.')
    else:
        DESTINO.write_text(texto, encoding='utf-8')
    lista = dados['itens']
    print(f'{len(lista)} itens; {sum(1 for i in lista if i.get("bf"))} com Black Friday; '
          f'{sum(1 for i in lista if i.get("soBf"))} só na Black Friday (combos)')
