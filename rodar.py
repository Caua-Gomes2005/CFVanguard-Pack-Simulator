import subprocess
import sys

def instalar(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import pandas as pd# Exemplo de biblioteca
except ImportError:
    instalar('pandas')
    import pandas as pd

import random as rd

def escolhe_pacote(name):
    data = pd.read_csv(f'packs\{name}.csv')
    for index, row in data.iterrows(): 
        print(f'0{row["id"]} {row["name"]} - {row["grade"]} - {row["clan"]} - {row["type"]} - {row["rarity"]}')

def ver_colecao(nome):
    try:
        save = pd.read_csv(f'{nome}.csv')
        for index, row in save.iterrows():
            print(f'0{row["id"]} {row["name"]} - {row["grade"]} - {row["clan"]} - {row["type"]} - {row["rarity"]} - Qtt: {row["qtt"]}')
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
    elif luck <= 99:
        raridade = 'RRR'
    else:
        raridade = 'SP'

    raras = data[data['rarity'] == raridade]
    r_tirada = raras.sample(n=1).to_dict('records')
    pacote.extend(r_tirada)

    pacote = pd.DataFrame(pacote)
    
    return pacote

def atualizar_save(box, pacote):
    #Quero colocar os valores do pacote na box e se houver repetidos, qtt += 1
    
    for index, row in pacote.iterrows():
        card = box[(box['set'] == row['set']) & (box['id'] == row['id'])]
        if not card.empty:
            box.loc[card.index, 'qtt'] += 1
        else:
            new_card = row.to_dict()
            new_card['qtt'] = 1
            #box não tem append, então vou criar um novo dataframe com a nova linha e concatenar com a box
            new_card_df = pd.DataFrame([new_card])
            box = pd.concat([box, new_card_df], ignore_index=True)
           
    return box

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
    save.sort_values(by=['id'], inplace=True)
    save.to_csv('save.csv', index=False)
    return box

print('Seja bem vindo ao CF Vanguard Pack Simulator!')

print('O que gostaria de fazer?: ')
option = input('1 - Rodar pacotes \n2 - Ver pacotes disponíveis \n3 - Ver sua coleção \n4 - Sair \nDigite o número da opção desejada: ')

if option == '1':
    name = input('Digite o nome do pacote (ex: BT01): ')
    qtt = int(input('Digite a quantidade de pacotes que deseja abrir: '))
    box = rodar_box(name.upper(), qtt)
    print('Pacotes abertos! As cartas foram salvas em last_box.csv e a coleção foi atualizada em save.csv')
    ver_colecao('last_box')
    input('\nPressione Enter para sair...')

if option == '2':
    name = input('Digite o nome do pacote (ex: BT01): ')
    escolhe_pacote(name)
    input('\nPressione Enter para sair...')

if option == '3':
    ver_colecao('save')
    input('\nPressione Enter para sair...')

if option == '4':
    print('Obrigado por usar o CF Vanguard Pack Simulator! Até a próxima!')
    input('\nPressione Enter para sair...')