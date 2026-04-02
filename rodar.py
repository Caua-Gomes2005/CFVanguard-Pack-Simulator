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

def web_colecao(nome):
    try:
        save = pd.read_csv(f'{nome}.csv')
        for index, row in save.iterrows():
            link = gerar_link_wiki(row['name'])
            print(f'Abrindo Wiki de: {row["name"]}...')
            webbrowser.open(link) # Isso abre o navegador automaticamente
    except:
        print('Erro ao carregar coleção.')

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
    save.sort_values(by=['set', 'id'], inplace=True)
    save.to_csv('save.csv', index=False)
    return box

def filtra_colecao(tipo, filtro):
    
    save = pd.read_csv('save.csv')
    
    if (tipo == 'type') and (filtro.lower()== 'trigger'):
        save = save[(save['type'].str.lower()) != 'normal unit']
    else:
        save = save[(save[tipo].str.lower()) == filtro]
    if save.empty:
        print(f'Nenhuma carta encontrada para o filtro: {tipo} = {filtro}')
    else:
        for index, row in save.iterrows():
            print(f'0{row["id"]} {row["name"]} - {row["grade"]} - {row["clan"]} - {row["type"]} - {row["rarity"]} - Qtt: {row["qtt"]}')
        
#Main

try: #Cria um backup para garantir que a coleção não seja sobreescrita acidentalmente
    backup = pd.read_csv('save.csv')
except:
    backup = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt']) 
backup.to_csv('save_backup.csv', index=False)

#Tela de entrada
print('Seja bem vindo ao CF Vanguard Pack Simulator!')
print('O que gostaria de fazer?: ')
option = input('1 - Rodar pacotes \n2 - Ver pacotes disponíveis \n3 - Ver sua coleção \n4 - Sair \nDigite o número da opção desejada: ')

if option == '1':
    name = input('Digite o nome do pacote (ex: BT01): ')
    qtt = int(input('Digite a quantidade de pacotes que deseja abrir: '))
    box = rodar_box(name.upper(), qtt)
    print('Pacotes abertos! As cartas foram salvas em last_box.csv e a coleção foi atualizada em save.csv')
    web_colecao('last_box')
    input('\nPressione Enter para sair...')

elif option == '2':
    name = input('Digite o nome do pacote (ex: BT01): ')
    escolhe_pacote(name)
    input('\nPressione Enter para sair...')

elif option == '3':
    filtro = input('\nDeseja filtrar a coleção? (s/n): ')
    if filtro == 's':
        tipo = input('Digite o tipo de filtro (ex: rarity): ')
        valor = input('Digite o valor do filtro (ex: R): \n')
        filtra_colecao(tipo, valor)
    else:
        ver_colecao('save')
    input('\nPressione Enter para sair...')

elif option == '4':
    print('Obrigado por usar o CF Vanguard Pack Simulator! Até a próxima!')
    input('\nPressione Enter para sair...')

else:
    print('Opção inválida! Por favor, escolha uma opção válida na próxima vez.')
    input('\nPressione Enter para sair...')