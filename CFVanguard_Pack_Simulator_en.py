import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import random as rd
import webbrowser
import requests
from PIL import Image, ImageTk
from io import BytesIO

class VanguardSimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CF Vanguard Pack Simulator - Pro Edition")
        self.root.geometry("1100x750")
        self.root.minsize(950, 600)

        self.image_cache_pil = {}
        # DataFrame to store current deck cards
        self.deck_atual = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt'])

        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
        
        self.style.configure("Treeview", rowheight=25, font=('Arial', 9))
        self.style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        self.style.map('Treeview', background=[('selected', '#0078D7')])

        # Auto-Repair
        self._auto_reparo_save()

        try:
            backup = pd.read_csv('save.csv')
            backup.to_csv('save_backup.csv', index=False)
        except FileNotFoundError:
            pass

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tab_abrir = ttk.Frame(self.notebook)
        self.tab_pacotes = ttk.Frame(self.notebook)
        self.tab_colecao = ttk.Frame(self.notebook)
        self.tab_deckbuilder = ttk.Frame(self.notebook)
        self.tab_add_deck = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_abrir, text='Open Packs')
        self.notebook.add(self.tab_pacotes, text='Available Sets')
        self.notebook.add(self.tab_colecao, text='My Collection')
        self.notebook.add(self.tab_deckbuilder, text='Deck Builder')
        self.notebook.add(self.tab_add_deck, text='Add Deck')

        self.setup_tab_abrir()
        self.setup_tab_pacotes()
        self.setup_tab_colecao()
        self.setup_tab_deckbuilder()
        self.setup_tab_add_deck() 

        # Event to dynamically update tabs when selected
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        aba_selecionada = self.notebook.tab(self.notebook.select(), "text")
        if aba_selecionada == 'Available Sets':
            self.atualizar_lista_pacotes()

    def _auto_reparo_save(self):
        try:
            if os.path.exists('save.csv'):
                df = pd.read_csv('save.csv')
                if df.empty: return
                
                primeiro_set = str(df['set'].iloc[0])
                primeiro_id = str(df['id'].iloc[0])
                
                corrompido = False
                if primeiro_set.isdigit() or (any(c.isalpha() for c in primeiro_id) and len(primeiro_id) > 3):
                    corrompido = True
                    
                if corrompido:
                    os.rename('save.csv', 'save_corrupted.csv')
                    pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt']).to_csv('save.csv', index=False)
                    messagebox.showwarning(
                        "Auto-Repair Complete", 
                        "Your collection was detected as corrupted. A new healthy version has been created."
                    )
        except Exception as e:
            print("Save check skipped:", e)

    # ==========================================
    # API IMAGES AND GALLERY
    # ==========================================
    def obter_imagem_pil_api(self, nome_carta):
        if pd.isna(nome_carta) or not nome_carta: return None
        if nome_carta in self.image_cache_pil:
            return self.image_cache_pil[nome_carta]
            
        try:
            nome_formatado = nome_carta.replace(' ', '_')
            api_url = f"https://cardfight.fandom.com/api.php?action=query&titles={nome_formatado}&prop=pageimages&format=json&pithumbsize=500"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            resposta_api = requests.get(api_url, headers=headers).json()
            pages = resposta_api.get('query', {}).get('pages', {})
            page_id = list(pages.keys())[0]
            
            if page_id != '-1' and 'thumbnail' in pages[page_id]:
                img_url = pages[page_id]['thumbnail']['source']
                resposta_img = requests.get(img_url, headers=headers)
                img_data = Image.open(BytesIO(resposta_img.content))
                
                self.image_cache_pil[nome_carta] = img_data
                return img_data
        except Exception as e:
            print(f"Error fetching {nome_carta}: {e}")
        return None

    def abrir_imagem_solo(self, nome_carta):
        popup = tk.Toplevel(self.root)
        popup.title(nome_carta)
        popup.geometry("350x500")
        
        lbl_status = ttk.Label(popup, text="Searching...", font=('Arial', 11))
        lbl_status.pack(expand=True)
        self.root.update()

        img_pil = self.obter_imagem_pil_api(nome_carta)
        
        if img_pil:
            lbl_status.pack_forget()
            lbl_img = tk.Label(popup)
            lbl_img.pack(expand=True, fill='both', padx=5, pady=5)

            def redimensionar(event):
                if event.widget == popup:
                    largura = max(event.width - 20, 100)
                    altura = max(event.height - 20, 100)
                    img_redimensionada = img_pil.copy()
                    img_redimensionada.thumbnail((largura, altura), Image.Resampling.LANCZOS)
                    img_tk = ImageTk.PhotoImage(img_redimensionada)
                    lbl_img.config(image=img_tk)
                    lbl_img.image = img_tk 

            popup.bind("<Configure>", redimensionar)
            popup.event_generate("<Configure>", width=350, height=500)
        else:
            lbl_status.config(text="Image not found.")

    def mostrar_imagem_carta(self, event, tree):
        selecionado = tree.selection()
        if not selecionado: return
        valores = tree.item(selecionado[0])['values']
        colunas = tree['columns']
        if 'name' in colunas:
            nome_carta = str(valores[colunas.index('name')])
            self.abrir_imagem_solo(nome_carta)
            
    def abrir_galeria_tabela(self, tree):
        itens = tree.get_children()
        if not itens: 
            messagebox.showinfo("Gallery", "No cards to display.")
            return
            
        colunas = tree['columns']
        if 'name' not in colunas: return
        idx_nome = colunas.index('name')
        
        nomes = [str(tree.item(item)['values'][idx_nome]) for item in itens]
        self.abrir_galeria_lista("Card Gallery", nomes)

    def abrir_galeria_lista(self, titulo, lista_nomes):
        if not lista_nomes: 
            messagebox.showinfo("Gallery", "No cards to display.")
            return
            
        # Remove duplicates to keep the gallery clean
        nomes_unicos = list(dict.fromkeys(lista_nomes))
            
        if len(nomes_unicos) > 20:
            if not messagebox.askyesno("Warning", f"Loading {len(nomes_unicos)} unique images may take a while. Do you want to continue?"):
                return

        popup = tk.Toplevel(self.root)
        popup.title(titulo)
        popup.geometry("850x650")

        canvas = tk.Canvas(popup, highlightthickness=0)
        scrollbar = ttk.Scrollbar(popup, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            try:
                if hasattr(event, 'delta') and event.delta != 0:
                    direcao = -1 if event.delta > 0 else 1
                    canvas.yview_scroll(direcao, "units")
                elif hasattr(event, 'num'):
                    direcao = -1 if event.num == 4 else 1
                    canvas.yview_scroll(direcao, "units")
            except Exception:
                pass

        for widget in (canvas, scrollable_frame):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", _on_mousewheel) 
            widget.bind("<Button-5>", _on_mousewheel) 

        lbl_loading = ttk.Label(scrollable_frame, text="Building gallery... Please wait.", font=('Arial', 12, 'bold'))
        lbl_loading.grid(row=0, column=0, pady=20)
        self.root.update()

        row, col = 1, 0
        max_cols = 3 

        for nome_carta in nomes_unicos:
            img_pil = self.obter_imagem_pil_api(nome_carta)

            frame_carta = ttk.Frame(scrollable_frame, relief="ridge", borderwidth=2)
            frame_carta.grid(row=row, column=col, padx=10, pady=10)

            if img_pil:
                img_thumb = img_pil.copy()
                img_thumb.thumbnail((250, 350), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img_thumb)
                
                lbl_img = tk.Label(frame_carta, image=img_tk)
                lbl_img.image = img_tk
                lbl_img.pack(padx=5, pady=5)
            else:
                lbl_img = tk.Label(frame_carta, text="No Image", width=25, height=15, bg="lightgray")
                lbl_img.pack(padx=5, pady=5)

            lbl_nome = ttk.Label(frame_carta, text=nome_carta, font=('Arial', 9, 'bold'), wraplength=200, justify='center')
            lbl_nome.pack(pady=5)

            acao_clique = lambda event, nome=nome_carta: self.abrir_imagem_solo(nome)
            
            for elemento in (frame_carta, lbl_img, lbl_nome):
                elemento.bind("<Double-1>", acao_clique)
                elemento.bind("<MouseWheel>", _on_mousewheel)
                elemento.bind("<Button-4>", _on_mousewheel)
                elemento.bind("<Button-5>", _on_mousewheel)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
            self.root.update()

        lbl_loading.destroy()

    # ==========================================
    # UTILS
    # ==========================================
    def treeview_sort_column(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        try: l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError: l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            tv.item(k, tags=(tag,))
        tv.heading(col, command=lambda: self.treeview_sort_column(tv, col, not reverse))

    def add_scrollbar(self, parent, tree):
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

    def preencher_treeview(self, tree, df):
        tree.delete(*tree.get_children())
        for i, (_, row) in enumerate(df.iterrows()):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            valores = [str(row.get(col, "")) if not pd.isna(row.get(col, "")) else "" for col in tree['columns']]
            tree.insert("", tk.END, values=valores, tags=(tag,))
        tree.tag_configure('evenrow', background='#f9f9f9')
        tree.tag_configure('oddrow', background='#ffffff')

    def gerar_link_wiki(self, nome_carta):
        return f'https://cardfight.fandom.com/wiki/{nome_carta.replace(" ", "_")}'

    def abrir_wiki_tabela(self, tree):
        itens = tree.get_children()
        if not itens: return
        if len(itens) > 15:
            if not messagebox.askyesno("Warning", f"You are about to open {len(itens)} tabs. Are you sure?"): return
        for item in itens:
            valores = tree.item(item)['values']
            colunas = tree['columns']
            if 'name' in colunas:
                webbrowser.open(self.gerar_link_wiki(str(valores[colunas.index('name')])))

    # ==========================================
    # CORE SIMULATOR
    # ==========================================
    def rodar_pacote(self, name):
        caminho = os.path.join('packs', f'{name}.csv')
        try: 
            data = pd.read_csv(caminho)
        except FileNotFoundError: 
            return None
            
        pacote = []
        
        # 1. Maps all rarities that exist in this pack
        todas_raridades = set()
        for r in data['rarity'].dropna():
            todas_raridades.update(str(r).split('+'))
            
        # 2. Checks if minor rarities (C, R, RR) are MISSING
        tem_menores = any(r in todas_raridades for r in ['C', 'R', 'RR'])
        menor_e_rrr = (not tem_menores) and ('RRR' in todas_raridades)
        
        # =======================================================
        # SPECIAL CASE: Lowest rarity is RRR (Premium/Special Set)
        # =======================================================
        if menor_e_rrr:
            rrrs = data[data['rarity'].apply(lambda x: 'RRR' in str(x).split('+'))]
            sps = data[data['rarity'].apply(lambda x: 'SP' in str(x).split('+'))]
            
            # Pulls 4 RRRs
            if not rrrs.empty:
                pacote.extend(rrrs.sample(n=min(4, len(rrrs))).to_dict('records'))
                
            # Pulls 1 SP (with safety fallback to RRR in case set doesn't have SP)
            if not sps.empty:
                pacote.extend(sps.sample(n=1).to_dict('records'))
            elif not rrrs.empty: 
                pacote.extend(rrrs.sample(n=1).to_dict('records'))
                
        # =======================================================
        # STANDARD CASE: Normal Packs
        # =======================================================
        else:
            commons = data[data['rarity'].apply(lambda x: 'C' in str(x).split('+'))]
            if not commons.empty: 
                pacote.extend(commons.sample(n=min(4, len(commons))).to_dict('records'))
                
            luck = rd.randint(1, 100)
            
            # Probabilities: <=70 (R), 71-90 (RR), 91-98 (RRR), 99-100 (SP)
            raridade = 'R' if luck <= 70 else 'RR' if luck <= 90 else 'RRR' if luck <= 98 else 'SP'
            
            raras = data[data['rarity'].apply(lambda x: raridade in str(x).split('+'))]
            
            # Fallbacks: If SP is drawn but unavailable, try RRR. If unavailable, try R.
            if raras.empty and raridade == 'SP':
                raras = data[data['rarity'].apply(lambda x: 'RRR' in str(x).split('+'))]
                if raras.empty:
                    raras = data[data['rarity'].apply(lambda x: 'R' in str(x).split('+'))]
                    
            if not raras.empty: 
                pacote.extend(raras.sample(n=1).to_dict('records'))
                
        # 3. Finish DataFrame assembly
        df_pacote = pd.DataFrame(pacote)
        if not df_pacote.empty: 
            df_pacote['set'] = name
            
        return df_pacote

    def atualizar_save(self, box, pacote):
        if pacote is None or pacote.empty: return box
        for _, row in pacote.iterrows():
            set_val, id_val = row.get('set', ''), row.get('id', '')
            qtd_add = row.get('qtt', 1)
            card_mask = (box['set'] == set_val) & (box['id'] == id_val)
            if card_mask.any(): box.loc[card_mask, 'qtt'] += qtd_add
            else:
                new_row = row.to_dict()
                new_row['qtt'] = qtd_add
                box = pd.concat([box, pd.DataFrame([new_row])], ignore_index=True)
        cols_ordem = ['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt']
        for col in cols_ordem:
            if col not in box.columns: box[col] = ''
        return box[cols_ordem]

    # ==========================================
    # TAB 1 - OPEN PACKS
    # ==========================================
    def setup_tab_abrir(self):
        frame_top = ttk.Frame(self.tab_abrir)
        frame_top.pack(fill='x', pady=15, padx=10)
        ttk.Label(frame_top, text="Pack (e.g., BT01):").grid(row=0, column=0, padx=5)
        self.entry_pacote = ttk.Entry(frame_top, width=15)
        self.entry_pacote.grid(row=0, column=1, padx=5)
        ttk.Label(frame_top, text="Quantity:").grid(row=0, column=2, padx=5)
        self.entry_qtt = ttk.Entry(frame_top, width=8)
        self.entry_qtt.grid(row=0, column=3, padx=5)
        self.btn_abrir = ttk.Button(frame_top, text="Open Packs!", command=self.action_abrir_pacotes)
        self.btn_abrir.grid(row=0, column=4, padx=15)

        container = ttk.Frame(self.tab_abrir)
        container.pack(fill='both', expand=True, padx=10, pady=5)
        cols = ('set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt')
        self.tree_last_box = ttk.Treeview(container, columns=cols, show='headings')
        larguras = {'set': 60, 'id': 50, 'name': 200, 'grade': 50, 'clan': 120, 'type': 100, 'rarity': 60, 'qtt': 50}
        for col in cols:
            self.tree_last_box.heading(col, text=col.upper(), command=lambda c=col: self.treeview_sort_column(self.tree_last_box, c, False))
            self.tree_last_box.column(col, width=larguras.get(col, 100), anchor="center" if col != 'name' else "w")
        self.tree_last_box.bind("<Double-1>", lambda event: self.mostrar_imagem_carta(event, self.tree_last_box))
        self.add_scrollbar(container, self.tree_last_box)
        self.tree_last_box.pack(side='left', fill='both', expand=True)
        
        frame_botoes = ttk.Frame(self.tab_abrir)
        frame_botoes.pack(pady=5)
        ttk.Button(frame_botoes, text="View Gallery (App)", command=lambda: self.abrir_galeria_tabela(self.tree_last_box)).grid(row=0, column=0, padx=5)
        ttk.Button(frame_botoes, text="View results on Wiki (Web)", command=lambda: self.abrir_wiki_tabela(self.tree_last_box)).grid(row=0, column=1, padx=5)

    def action_abrir_pacotes(self):
        nome = self.entry_pacote.get().upper()
        if not os.path.exists(os.path.join('packs', f'{nome}.csv')):
            messagebox.showerror("Error", f"Pack {nome} not found.")
            return
        try:
            qtt = int(self.entry_qtt.get())
            if qtt <= 0: raise ValueError
        except:
            messagebox.showwarning("Warning", "Invalid quantity.")
            return

        self.btn_abrir.config(text="Opening...", state='disabled')
        box = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt'])
        
        for i in range(qtt):
            p = self.rodar_pacote(nome)
            if p is not None and not p.empty: box = self.atualizar_save(box, p)
            if i % 10 == 0: self.root.update()
        
        if not box.empty:
            box.sort_values(by=['id'], inplace=True)
            self.preencher_treeview(self.tree_last_box, box)
            try: 
                save = pd.read_csv('save.csv')
                save = save.loc[:, ~save.columns.str.contains('^Unnamed')]
            except: save = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt'])
            save = self.atualizar_save(save, box)
            save.sort_values(by=['set', 'id'], inplace=True)
            save.to_csv('save.csv', index=False)
            self.atualizar_colecao_view()
            self.atualizar_deckbuilder_colecao()
        self.btn_abrir.config(text="Open Packs!", state='normal')

    # ==========================================
    # TAB 2 - AVAILABLE SETS
    # ==========================================
    def setup_tab_pacotes(self):
        container = ttk.Frame(self.tab_pacotes)
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tree_pacotes = ttk.Treeview(container, columns=('set',), show='headings')
        self.tree_pacotes.heading('set', text='PACK NAME (SET)')
        self.tree_pacotes.column('set', width=300, anchor='center')
        
        self.add_scrollbar(container, self.tree_pacotes)
        self.tree_pacotes.pack(side='left', fill='both', expand=True)

        self.tree_pacotes.bind("<Double-1>", self.abrir_galeria_pacote_direto)

        ttk.Label(self.tab_pacotes, text="💡 Tip: Double-click a pack to open a gallery with all its cards.", font=('Arial', 9, 'italic'), foreground='gray').pack(pady=5)

        self.atualizar_lista_pacotes()

    def atualizar_lista_pacotes(self):
        self.tree_pacotes.delete(*self.tree_pacotes.get_children())
        
        if not os.path.exists('packs'):
            os.makedirs('packs')
            return

        arquivos = [f for f in os.listdir('packs') if f.lower().endswith('.csv')]
        if 'direct.csv' in arquivos: arquivos.remove('direct.csv')

        sets = sorted([f.replace('.csv', '').replace('.CSV', '').upper() for f in arquivos])

        for i, nome_set in enumerate(sets):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tree_pacotes.insert("", tk.END, values=(nome_set,), tags=(tag,))
            
        self.tree_pacotes.tag_configure('evenrow', background='#f9f9f9')
        self.tree_pacotes.tag_configure('oddrow', background='#ffffff')

    def abrir_galeria_pacote_direto(self, event):
        selecionado = self.tree_pacotes.selection()
        if not selecionado: return
        nome_set = str(self.tree_pacotes.item(selecionado[0])['values'][0])
        
        caminho = os.path.join('packs', f'{nome_set}.csv')
        try:
            df = pd.read_csv(caminho)
            if 'name' in df.columns:
                nomes = df['name'].dropna().tolist()
                self.abrir_galeria_lista(f"Set Gallery: {nome_set}", nomes)
            else:
                messagebox.showerror("Error", "Invalid pack format ('name' column not found).")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load the pack's cards: {e}")

    # ==========================================
    # TAB 3 - COLLECTION
    # ==========================================
    def setup_tab_colecao(self):
        frame_filtros = ttk.Frame(self.tab_colecao)
        frame_filtros.pack(fill='x', pady=10, padx=10)
        self.cb_filtro = ttk.Combobox(frame_filtros, values=['All', 'name', 'rarity', 'grade', 'clan', 'type', 'set'], state='readonly', width=12)
        self.cb_filtro.current(0)
        self.cb_filtro.pack(side='left', padx=5)
        self.entry_busca = ttk.Entry(frame_filtros)
        self.entry_busca.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(frame_filtros, text="Search", command=self.aplicar_filtro).pack(side='left', padx=5)

        container = ttk.Frame(self.tab_colecao)
        container.pack(fill='both', expand=True, padx=10)
        cols = ('set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt')
        self.tree_colecao = ttk.Treeview(container, columns=cols, show='headings')
        larguras = {'set': 60, 'id': 50, 'name': 200, 'grade': 50, 'clan': 120, 'type': 100, 'rarity': 60, 'qtt': 50}
        for col in cols:
            self.tree_colecao.heading(col, text=col.upper(), command=lambda c=col: self.treeview_sort_column(self.tree_colecao, c, False))
            self.tree_colecao.column(col, width=larguras.get(col, 100), anchor="center" if col != 'name' else "w")
        self.tree_colecao.bind("<Double-1>", lambda event: self.mostrar_imagem_carta(event, self.tree_colecao))
        self.add_scrollbar(container, self.tree_colecao)
        self.tree_colecao.pack(side='left', fill='both', expand=True)
        
        frame_stats = ttk.Frame(self.tab_colecao)
        frame_stats.pack(fill='x', padx=10, pady=5)
        self.lbl_stats = ttk.Label(frame_stats, text="Unique Cards: 0 | Total: 0", font=('Arial', 9, 'bold'))
        self.lbl_stats.pack(side='left')

        frame_botoes = ttk.Frame(frame_stats)
        frame_botoes.pack(side='right')
        ttk.Button(frame_botoes, text="View Gallery (App)", command=lambda: self.abrir_galeria_tabela(self.tree_colecao)).pack(side='left', padx=5)
        ttk.Button(frame_botoes, text="View on Wiki (Web)", command=lambda: self.abrir_wiki_tabela(self.tree_colecao)).pack(side='left')
        
        self.atualizar_colecao_view()

    def aplicar_filtro(self):
        try:
            df = pd.read_csv('save.csv')
            tipo = self.cb_filtro.get()
            valor = self.entry_busca.get().lower().strip()
            if tipo != 'All' and valor: df = df[df[tipo].astype(str).str.lower().str.contains(valor, na=False)]
            self.preencher_treeview(self.tree_colecao, df)
            self.atualizar_estatisticas(df)
        except: pass

    def atualizar_colecao_view(self):
        try:
            df = pd.read_csv('save.csv')
            self.preencher_treeview(self.tree_colecao, df)
            self.atualizar_estatisticas(df)
        except: pass

    def atualizar_estatisticas(self, df):
        unicas = len(df)
        total = df['qtt'].sum() if not df.empty and 'qtt' in df.columns else 0
        self.lbl_stats.config(text=f"Unique Cards: {unicas} | Total Volume: {int(total)}")

    # ==========================================
    # TAB 4 - DECKBUILDER
    # ==========================================
    def setup_tab_deckbuilder(self):
        paned = ttk.PanedWindow(self.tab_deckbuilder, orient=tk.HORIZONTAL)
        paned.pack(fill='both', expand=True, padx=10, pady=10)

        # Left: Collection & Filters
        frame_esq = ttk.Frame(paned)
        paned.add(frame_esq, weight=2)

        f_filtros_db = ttk.Frame(frame_esq)
        f_filtros_db.pack(fill='x', pady=5)
        self.db_filtro_cb = ttk.Combobox(f_filtros_db, values=['All', 'name', 'rarity', 'grade', 'clan', 'type', 'set'], state='readonly', width=12)
        self.db_filtro_cb.current(0)
        self.db_filtro_cb.pack(side='left', padx=2)
        self.db_busca_entry = ttk.Entry(f_filtros_db)
        self.db_busca_entry.pack(side='left', fill='x', expand=True, padx=2)
        ttk.Button(f_filtros_db, text="Filter", command=self.aplicar_filtro_deckbuilder).pack(side='left')

        cols_db = ('set', 'id', 'name', 'grade', 'clan', 'type', 'qtt')
        self.tree_db_colecao = ttk.Treeview(frame_esq, columns=cols_db, show='headings')
        larguras_db = {'set': 50, 'id': 40, 'name': 140, 'grade': 40, 'clan': 90, 'type': 90, 'qtt': 40}
        
        for col in cols_db:
            self.tree_db_colecao.heading(col, text=col.upper(), 
                                         command=lambda c=col: self.treeview_sort_column(self.tree_db_colecao, c, False))
            self.tree_db_colecao.column(col, width=larguras_db.get(col, 50), anchor="center" if col != 'name' else "w")
        
        self.tree_db_colecao.bind("<ButtonRelease-1>", lambda e: self.atualizar_preview_deckbuilder(e, self.tree_db_colecao))
        self.tree_db_colecao.bind("<Double-1>", self.adicionar_ao_deck)
        
        scroll_esq = ttk.Scrollbar(frame_esq, orient="vertical", command=self.tree_db_colecao.yview)
        self.tree_db_colecao.configure(yscrollcommand=scroll_esq.set)
        scroll_esq.pack(side='right', fill='y')
        self.tree_db_colecao.pack(side='left', fill='both', expand=True)

        # Center: Current Deck
        frame_centro = ttk.Frame(paned)
        paned.add(frame_centro, weight=2)
        
        f_botoes_deck = ttk.Frame(frame_centro)
        f_botoes_deck.pack(fill='x', pady=5)
        ttk.Button(f_botoes_deck, text="Save Deck", command=self.salvar_deck).pack(side='left', padx=2)
        ttk.Button(f_botoes_deck, text="Load Deck", command=self.carregar_deck).pack(side='left', padx=2)
        ttk.Button(f_botoes_deck, text="Clear", command=self.limpar_deck).pack(side='right', padx=2)

        self.tree_deck = ttk.Treeview(frame_centro, columns=cols_db, show='headings')
        for col in cols_db:
            self.tree_deck.heading(col, text=col.upper(), 
                                   command=lambda c=col: self.treeview_sort_column(self.tree_deck, c, False))
            self.tree_deck.column(col, width=larguras_db.get(col, 50), anchor="center" if col != 'name' else "w")
            
        self.tree_deck.bind("<ButtonRelease-1>", lambda e: self.atualizar_preview_deckbuilder(e, self.tree_deck))
        self.tree_deck.bind("<Double-1>", self.remover_do_deck)

        scroll_centro = ttk.Scrollbar(frame_centro, orient="vertical", command=self.tree_deck.yview)
        self.tree_deck.configure(yscrollcommand=scroll_centro.set)
        scroll_centro.pack(side='right', fill='y')
        self.tree_deck.pack(side='left', fill='both', expand=True)

        self.lbl_deck_stats = ttk.Label(frame_centro, text="Cards in Deck: 0/50", font=('Arial', 10, 'bold'))
        self.lbl_deck_stats.pack(pady=5)

        # Right: Preview
        frame_dir = ttk.Frame(paned)
        paned.add(frame_dir, weight=2)
        
        self.lbl_deck_preview_nome = ttk.Label(frame_dir, text="Select a card", font=('Arial', 10, 'bold'), wraplength=200, justify='center')
        self.lbl_deck_preview_nome.pack(pady=5)
        
        self.lbl_deck_preview_img = tk.Label(frame_dir, text="[Image Area]", bg="lightgray")
        self.lbl_deck_preview_img.pack(padx=10, pady=10, fill='both', expand=True)

        ttk.Label(self.tab_deckbuilder, text="💡 Tip: Click on column headers to sort. Double-click to manage the deck.", font=('Arial', 9, 'italic'), foreground='gray').pack(pady=2)

        self.atualizar_deckbuilder_colecao()

    def atualizar_deckbuilder_colecao(self, df=None):
        if df is None:
            try: df = pd.read_csv('save.csv')
            except: df = pd.DataFrame()
        self.preencher_treeview(self.tree_db_colecao, df)

    def aplicar_filtro_deckbuilder(self):
        try:
            df = pd.read_csv('save.csv')
            tipo = self.db_filtro_cb.get()
            valor = self.db_busca_entry.get().lower().strip()
            if tipo != 'All' and valor: df = df[df[tipo].astype(str).str.lower().str.contains(valor, na=False)]
            self.atualizar_deckbuilder_colecao(df)
        except: pass

    def atualizar_view_deck(self):
        self.preencher_treeview(self.tree_deck, self.deck_atual)
        total_cartas = self.deck_atual['qtt'].sum() if not self.deck_atual.empty else 0
        self.lbl_deck_stats.config(text=f"Cards in Deck: {int(total_cartas)}/50")
        
    def atualizar_preview_deckbuilder(self, event, tree):
        selecionado = tree.selection()
        if not selecionado: return
        valores = tree.item(selecionado[0])['values']
        colunas = tree['columns']
        if 'name' in colunas:
            nome_carta = str(valores[colunas.index('name')])
            self.lbl_deck_preview_nome.config(text=nome_carta)
            self.root.update()
            
            img_pil = self.obter_imagem_pil_api(nome_carta)
            if img_pil:
                img_thumb = img_pil.copy()
                img_thumb.thumbnail((450, 650), Image.Resampling.LANCZOS)
                img_tk = ImageTk.PhotoImage(img_thumb)
                
                self.lbl_deck_preview_img.config(image=img_tk, text="")
                self.lbl_deck_preview_img.image = img_tk
            else:
                self.lbl_deck_preview_img.config(image='', text="Image unavailable")

    def adicionar_ao_deck(self, event):
        selecionado = self.tree_db_colecao.selection()
        if not selecionado: return
        
        valores = self.tree_db_colecao.item(selecionado[0])['values']
        colunas = self.tree_db_colecao['columns']
        
        set_val = str(valores[colunas.index('set')])
        id_val = str(valores[colunas.index('id')])
        qtt_possuida = int(valores[colunas.index('qtt')])
        
        try: 
            save_df = pd.read_csv('save.csv')
            mask = (save_df['set'].astype(str) == set_val) & (save_df['id'].astype(str) == id_val)
            linhas = save_df[mask]
            if linhas.empty: return
            card_completa = linhas.iloc[0].to_dict()
        except: return

        qtd_no_deck = 0
        mask_deck = pd.Series([False] * len(self.deck_atual))
        if not self.deck_atual.empty:
            mask_deck = (self.deck_atual['set'].astype(str) == set_val) & (self.deck_atual['id'].astype(str) == id_val)
            if mask_deck.any(): 
                qtd_no_deck = int(self.deck_atual.loc[mask_deck, 'qtt'].values[0])

        if qtd_no_deck >= qtt_possuida:
            messagebox.showinfo("Limit", "You don't own any more copies of this card in your collection!")
            return
        if qtd_no_deck >= 4:
            messagebox.showinfo("Rule", "You have already reached the 4-copy limit for this card!")
            return

        if qtd_no_deck == 0:
            card_completa['qtt'] = 1
            self.deck_atual = pd.concat([self.deck_atual, pd.DataFrame([card_completa])], ignore_index=True)
        else:
            self.deck_atual.loc[mask_deck, 'qtt'] += 1

        self.atualizar_view_deck()

    def remover_do_deck(self, event):
        selecionado = self.tree_deck.selection()
        if not selecionado: return
        
        valores = self.tree_deck.item(selecionado[0])['values']
        colunas = self.tree_deck['columns']
        
        set_val = str(valores[colunas.index('set')])
        id_val = str(valores[colunas.index('id')])
        
        if not self.deck_atual.empty:
            mask_deck = (self.deck_atual['set'].astype(str) == set_val) & (self.deck_atual['id'].astype(str) == id_val)
            if mask_deck.any():
                qtd_atual = int(self.deck_atual.loc[mask_deck, 'qtt'].values[0])
                if qtd_atual > 1:
                    self.deck_atual.loc[mask_deck, 'qtt'] -= 1
                else:
                    self.deck_atual = self.deck_atual[~mask_deck]
                    
        self.atualizar_view_deck()

    def limpar_deck(self):
        if messagebox.askyesno("Clear", "Are you sure you want to clear the current deck?"):
            self.deck_atual = self.deck_atual.iloc[0:0] 
            self.atualizar_view_deck()

    def salvar_deck(self):
        if self.deck_atual.empty:
            messagebox.showwarning("Warning", "The deck is empty!")
            return
        caminho = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if caminho:
            self.deck_atual.to_csv(caminho, index=False)
            messagebox.showinfo("Success", "Deck saved successfully!")

    def carregar_deck(self):
        caminho = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if caminho:
            try:
                df = pd.read_csv(caminho)
                if 'id' in df.columns and 'qtt' in df.columns:
                    self.deck_atual = df
                    self.atualizar_view_deck()
                else:
                    messagebox.showerror("Error", "Invalid deck file.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load deck: {e}")

    # ==========================================
    # TAB 5 - ADD DECK TO COLLECTION
    # ==========================================
    def setup_tab_add_deck(self):
        frame_top = ttk.Frame(self.tab_add_deck)
        frame_top.pack(fill='x', pady=15, padx=10)
        
        ttk.Label(frame_top, text="Deck name in 'decks' folder (e.g., TD01):").grid(row=0, column=0, padx=5)
        self.entry_nome_deck = ttk.Entry(frame_top, width=30)
        self.entry_nome_deck.grid(row=0, column=1, padx=5)
        
        self.btn_add_deck = ttk.Button(frame_top, text="Add to Save", command=self.action_adicionar_deck)
        self.btn_add_deck.grid(row=0, column=2, padx=15)

        container = ttk.Frame(self.tab_add_deck)
        container.pack(fill='both', expand=True, padx=10, pady=5)
        
        cols = ('set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt')
        self.tree_deck_adicionado = ttk.Treeview(container, columns=cols, show='headings')
        larguras = {'set': 60, 'id': 50, 'name': 200, 'grade': 50, 'clan': 120, 'type': 100, 'rarity': 60, 'qtt': 50}
        
        for col in cols:
            self.tree_deck_adicionado.heading(col, text=col.upper(), command=lambda c=col: self.treeview_sort_column(self.tree_deck_adicionado, c, False))
            self.tree_deck_adicionado.column(col, width=larguras.get(col, 100), anchor="center" if col != 'name' else "w")
            
        self.tree_deck_adicionado.bind("<Double-1>", lambda event: self.mostrar_imagem_carta(event, self.tree_deck_adicionado))
        self.add_scrollbar(container, self.tree_deck_adicionado)
        self.tree_deck_adicionado.pack(side='left', fill='both', expand=True)

        ttk.Label(self.tab_add_deck, text="💡 Tip: Type the name of the .csv file located in the 'decks' folder to permanently add these cards to your collection.", font=('Arial', 9, 'italic'), foreground='gray').pack(pady=5)

    def action_adicionar_deck(self):
        nome = self.entry_nome_deck.get().strip()
        if not nome:
            messagebox.showwarning("Warning", "Please enter the deck name.")
            return

        if not nome.lower().endswith('.csv'):
            nome += '.csv'

        caminho = os.path.join('decks', nome)
        
        if not os.path.exists(caminho):
            messagebox.showerror("Error", f"Deck file '{nome}' not found in the 'decks' folder.\nMake sure the file exists.")
            return

        try:
            deck_df = pd.read_csv(caminho)
            if not {'id', 'qtt'}.issubset(deck_df.columns):
                messagebox.showerror("Error", "The selected file is missing required columns ('id' and 'qtt').")
                return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {e}")
            return

        self.btn_add_deck.config(text="Adding...", state='disabled')
        self.root.update()

        try:
            save = pd.read_csv('save.csv')
            save = save.loc[:, ~save.columns.str.contains('^Unnamed')]
        except: 
            save = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt'])

        save = self.atualizar_save(save, deck_df)
        save.sort_values(by=['set', 'id'], inplace=True)
        save.to_csv('save.csv', index=False)

        self.preencher_treeview(self.tree_deck_adicionado, deck_df)
        self.atualizar_colecao_view()
        self.atualizar_deckbuilder_colecao()

        messagebox.showinfo("Success", f"Cards from deck '{nome}' were successfully added to your collection!")
        
        self.btn_add_deck.config(text="Add to Save", state='normal')
        self.entry_nome_deck.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = VanguardSimulatorGUI(root)
    root.mainloop()