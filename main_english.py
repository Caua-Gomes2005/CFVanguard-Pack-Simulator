import os
import subprocess
import sys
import random as rd
import webbrowser

def install(package): # Installs the necessary package if it is not installed
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import pandas as pd
except ImportError:
    install('pandas')
    import pandas as pd

def generate_wiki_link(card_name):
    # The wiki uses underscores instead of spaces
    formatted_name = card_name.replace(' ', '_')
    return f'https://cardfight.fandom.com/wiki/{formatted_name}'

""" def web_collection(name):
    if str(type(name)) == "<class 'pandas.DataFrame'>":
        try:
            for index, row in name.iterrows():
                link = generate_wiki_link(row['name'])
                webbrowser.open(link) 
        except:
            print('Error loading collection.')
    else:
        try:
            save = pd.read_csv(f'{name}.csv')
            print(f'Opening Wiki for: {len(save)} cards...')
            for index, row in save.iterrows():
                link = generate_wiki_link(row['name'])
                webbrowser.open(link) # This opens the browser automatically
        except:
            print('Error loading collection.') """

def choose_pack(name):
    view = input('Do you want to see the cards from this pack on the Wiki? (y/n): ')
    if view.lower() == 'y':
        link = direct[direct['set'] == name.upper()]['link'].values[0]
        webbrowser.open(link)
    else:
        data = pd.read_csv(f'packs\{name}.csv')
        for index, row in data.iterrows(): 
            print(f'0{row["id"]} {row["name"]} - {row["grade"]} - {row["clan"]} - {row["type"]} - {row["rarity"]}')

def view_collection(name, web=False):
    try:
        save = pd.read_csv(f'{name}.csv')
        if web == False:
            for index, row in save.iterrows():
                print(f'0{row["id"]} {row["name"]} - {row["grade"]} - {row["clan"]} - {row["type"]} - {row["rarity"]} - Qtt: {row["qtt"]}')
        else:
            print(f'Opening Wiki for: {len(save)} cards...')
            for index, row in save.iterrows():
                link = generate_wiki_link(row['name'])
                webbrowser.open(link) 
    except:
        print('You do not have any cards in your collection yet! Open some packs to start collecting!')

def roll_pack(name):
    data = pd.read_csv(f'packs\{name}.csv')
    pack = []
    box = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity'])

    commons = data[data['rarity'] == 'C']
    c_pulled = commons.sample(n=4).to_dict('records')
    pack.extend(c_pulled)

    luck = rd.randint(1, 100)

    if luck <= 70:
        rarity_level = 'R'
    elif luck <= 90:
        rarity_level = 'RR'
    else:
        rarity_level = 'RRR'


    rares = data[data['rarity'] == rarity_level]
    r_pulled = rares.sample(n=1).to_dict('records')
    pack.extend(r_pulled)

    pack = pd.DataFrame(pack)
    
    return pack

def update_save(box, pack):
    # I want to put the pack values into the box and if there are duplicates, qtt += 1
    
    for index, row in pack.iterrows():
        card = box[(box['set'] == row['set']) & (box['id'] == row['id'])]
        if not card.empty:
            box.loc[card.index, 'qtt'] += 1
        else:
            new_card = row.to_dict()
            new_card['qtt'] = 1
            # box doesn't have append, so I will create a new dataframe with the new row and concatenate with the box
            new_card_df = pd.DataFrame([new_card])
            box = pd.concat([box, new_card_df], ignore_index=True)
           
    return box

def roll_box(name, qtt):
    box = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt'])
    for i in range(qtt):
        pack = roll_pack(name)
        box = update_save(box, pack)
    
    try:
        save = pd.read_csv('save.csv')
    except:
        save = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt'])
    box.sort_values(by=['id'], inplace=True)
    box.to_csv('last_box.csv', index=False)
    save = update_save(save, box)
    save.sort_values(by=['set', 'id'], inplace=True)
    save.to_csv('save.csv', index=False)
    return box

def filter_collection(filter_type, filter_value, data='save'):
    if data == 'save':
        save = pd.read_csv(f'{data}.csv')
    else:
        save = data.copy()
    
    if (filter_type == 'type') and (filter_value.lower() == 'trigger'):
        save = save[(save['type'].str.lower()) != 'normal unit']
    elif (filter_type == 'grade'):
        save = save[(save['grade'] == int(filter_value))]
    else:
        save = save[(save[filter_type].str.lower()) == filter_value]

    if save.empty:
        print(f'No cards found for the filter: {filter_type} = {filter_value}')
    else:
        for index, row in save.iterrows():
            print(f'0{row["id"]} {row["name"]} - {row["grade"]} - {row["clan"]} - {row["type"]} - {row["rarity"]} - Qtt: {row["qtt"]}')
    return save    

# Main

keep = True
try: # Creates a backup to ensure the collection is not accidentally overwritten
    backup = pd.read_csv('save.csv')
except:
    backup = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt']) 
backup.to_csv('save_backup.csv', index=False)

direct = pd.read_csv('packs\direct.csv')

while keep == True:

    # Welcome screen
    print('Welcome to the CF Vanguard Pack Simulator!')
    print('What would you like to do?: ')
    option = input('1 - Open packs \n2 - View available packs \n3 - View your collection \n4 - Exit \n\nEnter the number of the desired option: ')

    if option == '1':

        name = input('Enter the pack name (e.g., BT01): ')
        qtt = int(input('Enter the number of packs you want to open: '))
        box = roll_box(name.upper(), qtt)

        print('Packs opened! The cards were saved in last_box.csv and the collection was updated in save.csv')
        
        view = input('How would you like to view the cards you pulled? \n1 - Show here \n2 - Open the Wiki \n3 - Do not show \n:')
        
        if view == '1':
            view_collection('last_box')
        elif view == '2':
            view_collection('last_box', web=True)
        else:
            print('Alright! You can see the cards you pulled in last_box.csv')
        input('\nPress Enter to exit...\n')

    elif option == '2':
        for index, row in direct.iterrows():
            print(f'{row["set"]}')
        name = input('Enter the pack name (e.g., BT01): ')
        choose_pack(name)
        input('\nPress Enter to exit...\n')

    elif option == '3':
        filter_input = input('\nDo you want to filter the collection? (y/n): ')
        if filter_input.lower() == 'y':
            filter_type = input('Enter the filter type (e.g., rarity): ')
            filter_val = input('Enter the filter value (e.g., R): ')
            filtered = filter_collection(filter_type, filter_val)
            view = input('Do you want to view the filtered cards on the Wiki? (y/n): ')
            print()
            if view.lower() == 'y':
                filtered.to_csv('filtered.csv', index=False)
                view_collection('filtered', web=True)
                os.remove('filtered.csv')
            else:
                print('Alright! You can see the filtered cards in the collection!')
        else:
            print('Alright! You can see the filtered cards in the collection!')
            view_collection('save')
        input('\nPress Enter to exit...\n')

    elif option == '4':
        print('Thank you for using the CF Vanguard Pack Simulator! See you next time!')
        keep = False
        input('\nPress Enter to exit...\n')

    else:
        print('Invalid option! Please choose a valid option next time.')
        input('\nPress Enter to exit...\n')