import os
import subprocess
import sys
import random as rd
import webbrowser

def instalar(package): #Instala o pacote necessário caso ele não esteja instalado
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import pandas as pd
except ImportError:
    instalar('pandas')
    import pandas as pd

def gerar_link_wiki(nome_carta):
    # A wiki usa underscores no lugar de espaços
    nome_formatado = nome_carta.replace(' ', '_')
    return f'https://cardfight.fandom.com/wiki/{nome_formatado}'

""" def web_colecao(nome):
    if str(type(nome)) == "<class 'pandas.DataFrame'>":
        try:
            for index, row in nome.iterrows():
                link = gerar_link_wiki(row['name'])
                webbrowser.open(link) 
        except:
            print('Erro ao carregar coleção.')
    else:
        try:
            save = pd.read_csv(f'{nome}.csv')
            print(f'Abrindo a Wiki de: {len(save)} cartas...')
            for index, row in save.iterrows():
                link = gerar_link_wiki(row['name'])
                webbrowser.open(link) # Isso abre o navegador automaticamente
        except:
            print('Erro ao carregar coleção.') """

def escolhe_pacote(name):
    view = input('Deseja ver as cartas desse pacote na Wiki?(s/n): ')
    if view == 's':
        link = direct[direct['set'] == name.upper()]['link'].values[0]
        webbrowser.open(link)
    else:
        data = pd.read_csv(f'packs\{name}.csv')
        for index, row in data.iterrows(): 
            print(f'0{row["id"]} {row["name"]} - {row["grade"]} - {row["clan"]} - {row["type"]} - {row["rarity"]}')

def ver_colecao(nome, web=False):
    try:
        save = pd.read_csv(f'{nome}.csv')
        if web == False:
            for index, row in save.iterrows():
                print(f'0{row["id"]} {row["name"]} - {row["grade"]} - {row["clan"]} - {row["type"]} - {row["rarity"]} - Qtt: {row["qtt"]}')
        else:
            print(f'Abrindo a Wiki de: {len(save)} cartas...')
            for index, row in save.iterrows():
                link = gerar_link_wiki(row['name'])
                webbrowser.open(link) 
    except:
        print('Você ainda não tem nenhuma carta na coleção! Abra alguns pacotes para começar a colecionar!')

def rodar_pacote(name):
    data = pd.read_csv(f'packs\{name}.csv')
    pacote = []
    box = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity'])

    commons = data[data['rarity'] == 'C']
    c_tiradas = commons.sample(n=4).to_dict('records')
    pacote.extend(c_tiradas)

    luck = rd.randint(1, 100)

    if luck <= 70:
        raridade = 'R'
    elif luck <= 90:
        raridade = 'RR'
    else:
        raridade = 'RRR'


    raras = data[data['rarity'] == raridade]
    r_tirada = raras.sample(n=1).to_dict('records')
    pacote.extend(r_tirada)

    pacote = pd.DataFrame(pacote)
    
    return pacote

def atualizar_save(box, pacote):
    """Nova Lógica que resolve a contagem e garante a ordem das colunas"""
    if pacote is None or pacote.empty:
        return box
        
    for _, row in pacote.iterrows():
        set_val = row.get('set', '')
        id_val = row.get('id', '')
        qtd_add = row.get('qtt', 1)  # Captura cópias já repetidas e evita perda
        
        card_mask = (box['set'] == set_val) & (box['id'] == id_val)
        if card_mask.any():
            box.loc[card_mask, 'qtt'] += qtd_add
        else:
            new_row = row.to_dict()
            new_row['qtt'] = qtd_add
            df_new = pd.DataFrame([new_row])
            box = pd.concat([box, df_new], ignore_index=True)
            
    # Garante a ordem correta independente do que o Pandas tentou fazer
    cols_ordem = ['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt']
    for col in cols_ordem:
        if col not in box.columns:
            box[col] = ''
                
    return box[cols_ordem]

def rodar_box(name, qtt):
    box = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt'])
    for i in range(qtt):
        pacote = rodar_pacote(name)
        box = atualizar_save(box, pacote)
    
    try:
        save = pd.read_csv('save.csv')
    except:
        save = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt'])
    box.sort_values(by=['id'], inplace=True)
    box.to_csv('last_box.csv', index=False)
    save = atualizar_save(save, box)
    save.sort_values(by=['set', 'id'], inplace=True)
    save.to_csv('save.csv', index=False)
    return box

def filtra_colecao(tipo, filtro, data = 'save'):
    if data == 'save':
        save = pd.read_csv(f'{data}.csv')
    else:
        save = data.copy()
    
    if (tipo == 'type') and (filtro.lower() == 'trigger'):
        save = save[(save['type'].str.lower()) != 'normal unit']
    elif (tipo == 'grade'):
        save = save[(save['grade'] == int(filtro))]
    else:
        save = save[(save[tipo].str.lower()) == filtro]

    if save.empty:
        print(f'Nenhuma carta encontrada para o filtro: {tipo} = {filtro}')
    else:
        for index, row in save.iterrows():
            print(f'0{row["id"]} {row["name"]} - {row["grade"]} - {row["clan"]} - {row["type"]} - {row["rarity"]} - Qtt: {row["qtt"]}')
    return save    

def deck_builder():
    try:
        save = pd.read_csv('save.csv')
    except:
        print('Você ainda não tem nenhuma carta na coleção! Abra alguns pacotes para começar a colecionar!')
        return None
    
    meu_deck = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt'])

    while True:
        print(f'\nNumero de cartas no seu deck: {meu_deck["qtt"].sum()}')

        option = input('1 - Adicionar carta \n2 - Ver Deck \n3 - Remover Carta \n4 - Salvar Deck \n5 - Sair \nDigite o número da opção desejada: ')
        if option == '1':
            nome_carta = input('Digite o nome da carta que deseja adicionar: ')
            
            resultado = save[save['name'].str.contains(nome_carta, case=False)]
            if resultado.empty:
                print('Carta não encontrada na coleção!')
            
            else:
                for _,row in resultado.iterrows():
                    print(f'0{row["id"]} {row["name"]} - {row["grade"]} - {row["clan"]} - {row["type"]} - {row["rarity"]} - Qtt: {row["qtt"]}')

                if len(resultado) > 1:
                    print('Multiplas cartas encontradas! Digite o id da carta que deseja adicionar: ')
                    id_carta = input('Digite o id da carta: ')
                    resultado = resultado[resultado['id'] == id_carta]
                
                quantidade = int(input('Digite a quantidade que deseja adicionar: '))
                if quantidade <= 0:
                    print('Quantidade deve ser maior que zero!')
                elif quantidade <= resultado['qtt'].any():
                    carta_add = resultado.copy()
                    carta_add['qtt'] = quantidade
                    meu_deck = atualizar_save(meu_deck, carta_add)
                    print(meu_deck)

#Main

keep = True
try: #Cria um backup para garantir que a coleção não seja sobreescrita acidentalmente
    backup = pd.read_csv('save.csv')
except:
    backup = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt']) 
backup.to_csv('save_backup.csv', index=False)

direct = pd.read_csv('packs\direct.csv')

while keep == True:

    #Tela de entrada
    print('Seja bem vindo ao CF Vanguard Pack Simulator!')
    print('O que gostaria de fazer?: ')
    option = input('1 - Rodar pacotes \n2 - Ver pacotes disponíveis \n3 - Ver sua coleção\n4 - Deckbuilder \n5 - Sair \n\nDigite o número da opção desejada: ')

    if option == '1':

        name = input('Digite o nome do pacote (ex: BT01): ')
        qtt = int(input('Digite a quantidade de pacotes que deseja abrir: '))
        box = rodar_box(name.upper(), qtt)

        print('Pacotes abertos! As cartas foram salvas em last_box.csv e a coleção foi atualizada em save.csv')
        
        view = input('Deseja ver as cartas que você tirou de que forma? \n1 - Mostre aqui \n2 - Abra a Wiki \n3 - Não mostrar \n:')
        
        if view == '1':
            ver_colecao('last_box')
        elif view == '2':
            ver_colecao('last_box', web=True)
        else:
            print('Tudo bem! Você pode ver as cartas que tirou na last_box.csv')
        input('\nPressione Enter para sair...\n')

    elif option == '2':
        for index, row in direct.iterrows():
            print(f'{row["set"]}')
        name = input('Digite o nome do pacote (ex: BT01): ')
        escolhe_pacote(name)
        input('\nPressione Enter para sair...\n')

    elif option == '3':
        filtro = input('\nDeseja filtrar a coleção? (s/n): ')
        if filtro == 's':
            tipo = input('Digite o tipo de filtro (ex: rarity): ')
            valor = input('Digite o valor do filtro (ex: R): ')
            filtrada = filtra_colecao(tipo, valor)
            view = input('Deseja ver as cartas filtradas na Wiki?(s/n): ')
            print()
            if view == 's':
                filtrada.to_csv('filtrada.csv', index=False)
                ver_colecao('filtrada', web=True)
                os.remove('filtrada.csv')
            else:
                print('Tudo bem! Você pode ver as cartas filtradas na coleção!')
        else:
            print('Tudo bem! Você pode ver as cartas filtradas na coleção!')
            ver_colecao('save')
        input('\nPressione Enter para sair...\n')

    elif option == '4':
        deck_builder()
        input('\nPressione Enter para sair...\n')

    elif option == '5':
        print('Obrigado por usar o CF Vanguard Pack Simulator! Até a próxima!')
        keep = False
        input('\nPressione Enter para sair...\n')

    else:
        print('Opção inválida! Por favor, escolha uma opção válida na próxima vez.')
        input('\nPressione Enter para sair...\n')