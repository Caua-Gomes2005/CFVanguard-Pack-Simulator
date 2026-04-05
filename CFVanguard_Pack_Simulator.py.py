import os
import tkinter as tk
from tkinter import ttk, messagebox
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
        self.root.geometry("950x700")
        self.root.minsize(850, 550)

        self.image_cache_pil = {}

        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
        
        self.style.configure("Treeview", rowheight=25, font=('Arial', 9))
        self.style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        self.style.map('Treeview', background=[('selected', '#0078D7')])

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

        self.notebook.add(self.tab_abrir, text='Rodar Pacotes')
        self.notebook.add(self.tab_pacotes, text='Pacotes Disponíveis')
        self.notebook.add(self.tab_colecao, text='Minha Coleção')

        self.setup_tab_abrir()
        self.setup_tab_pacotes()
        self.setup_tab_colecao()

    # ==========================================
    # MOTOR DE BUSCA E VISUALIZAÇÃO DE IMAGENS
    # ==========================================
    def obter_imagem_pil_api(self, nome_carta):
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
            print(f"Erro ao buscar {nome_carta}: {e}")
        return None

    def abrir_imagem_solo(self, nome_carta):
        popup = tk.Toplevel(self.root)
        popup.title(nome_carta)
        popup.geometry("350x500")
        popup.resizable(True, True)
        popup.minsize(200, 300)
        
        lbl_status = ttk.Label(popup, text="Buscando...", font=('Arial', 11))
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
            lbl_status.config(text="Imagem não encontrada.")

    def mostrar_imagem_carta(self, event, tree):
        selecionado = tree.selection()
        if not selecionado: return
            
        valores = tree.item(selecionado[0])['values']
        colunas = tree['columns']
        if 'name' not in colunas: return
            
        nome_carta = str(valores[colunas.index('name')])
        self.abrir_imagem_solo(nome_carta)

    def abrir_galeria_tabela(self, tree):
        itens = tree.get_children()
        if not itens: 
            messagebox.showinfo("Galeria", "Nenhuma carta para exibir.")
            return
            
        if len(itens) > 20:
            if not messagebox.askyesno("Aviso", f"Carregar {len(itens)} imagens pode demorar um pouco. Deseja continuar?"):
                return

        colunas = tree['columns']
        if 'name' not in colunas: return
        idx_nome = colunas.index('name')

        popup = tk.Toplevel(self.root)
        popup.title("Galeria de Cartas")
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

        # --- NOVA FUNÇÃO: SCROLL DO MOUSE ---
        def _on_mousewheel(event):
            try:
                # Suporte para Windows/Mac e Linux
                if hasattr(event, 'delta') and event.delta != 0:
                    direcao = -1 if event.delta > 0 else 1
                    canvas.yview_scroll(direcao, "units")
                elif hasattr(event, 'num'):
                    direcao = -1 if event.num == 4 else 1
                    canvas.yview_scroll(direcao, "units")
            except Exception:
                pass

        # Vincula o scroll ao fundo do canvas e ao frame
        for widget in (canvas, scrollable_frame):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", _on_mousewheel) # Linux para cima
            widget.bind("<Button-5>", _on_mousewheel) # Linux para baixo

        lbl_loading = ttk.Label(scrollable_frame, text="Montando galeria... Aguarde.", font=('Arial', 12, 'bold'))
        lbl_loading.grid(row=0, column=0, pady=20)
        self.root.update()

        row, col = 1, 0
        max_cols = 3 

        for item in itens:
            nome_carta = str(tree.item(item)['values'][idx_nome])
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
                lbl_img = tk.Label(frame_carta, text="Sem Imagem", width=25, height=15, bg="lightgray")
                lbl_img.pack(padx=5, pady=5)

            lbl_nome = ttk.Label(frame_carta, text=nome_carta, font=('Arial', 9, 'bold'), wraplength=200, justify='center')
            lbl_nome.pack(pady=5)

            acao_clique = lambda event, nome=nome_carta: self.abrir_imagem_solo(nome)
            
            # Aplica o duplo clique E o scroll do mouse para cada elemento interno
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
    # FUNÇÕES DE TABELA E UTILITÁRIOS
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
            valores = [row.get(col, "") for col in tree['columns']]
            tree.insert("", tk.END, values=valores, tags=(tag,))
        
        tree.tag_configure('evenrow', background='#f9f9f9')
        tree.tag_configure('oddrow', background='#ffffff')

    def gerar_link_wiki(self, nome_carta):
        return f'https://cardfight.fandom.com/wiki/{nome_carta.replace(" ", "_")}'

    def abrir_wiki_tabela(self, tree):
        itens = tree.get_children()
        if not itens: return
        if len(itens) > 15:
            if not messagebox.askyesno("Aviso", f"Você vai abrir {len(itens)} abas no navegador. Tem certeza?"): return

        for item in itens:
            valores = tree.item(item)['values']
            colunas = tree['columns']
            if 'name' in colunas:
                nome = str(valores[colunas.index('name')])
                webbrowser.open(self.gerar_link_wiki(nome))

    # ==========================================
    # LÓGICA CORE DO SIMULADOR
    # ==========================================
    def rodar_pacote(self, name):
        caminho = os.path.join('packs', f'{name}.csv')
        try: data = pd.read_csv(caminho)
        except FileNotFoundError: return None

        pacote = []
        commons = data[data['rarity'] == 'C']
        if not commons.empty:
            pacote.extend(commons.sample(n=min(4, len(commons))).to_dict('records'))

        luck = rd.randint(1, 100)
        raridade = 'R' if luck <= 70 else 'RR' if luck <= 90 else 'RRR'
        raras = data[data['rarity'] == raridade]
        if not raras.empty:
            pacote.extend(raras.sample(n=1).to_dict('records'))

        return pd.DataFrame(pacote)

    def atualizar_save(self, box, pacote):
        for _, row in pacote.iterrows():
            set_val = row.get('set', '')
            card = box[(box['set'] == set_val) & (box['id'] == row['id'])]
            if not card.empty:
                box.loc[card.index, 'qtt'] += 1
            else:
                new_row = row.to_dict()
                new_row['qtt'] = 1
                box = pd.concat([box, pd.DataFrame([new_row])], ignore_index=True)
        return box

    # ==========================================
    # ABA 1 - ABRIR PACOTES
    # ==========================================
    def setup_tab_abrir(self):
        frame_top = ttk.Frame(self.tab_abrir)
        frame_top.pack(fill='x', pady=15, padx=10)

        ttk.Label(frame_top, text="Pack (ex: BT01):").grid(row=0, column=0, padx=5)
        self.entry_pacote = ttk.Entry(frame_top, width=15)
        self.entry_pacote.grid(row=0, column=1, padx=5)

        ttk.Label(frame_top, text="Quantidade:").grid(row=0, column=2, padx=5)
        self.entry_qtt = ttk.Entry(frame_top, width=8)
        self.entry_qtt.grid(row=0, column=3, padx=5)

        self.btn_abrir = ttk.Button(frame_top, text="Abrir Pacotes!", command=self.action_abrir_pacotes)
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

        ttk.Label(self.tab_abrir, text="💡 Dica: Duplo clique na lista ou na Galeria para ver a carta maior", font=('Arial', 9, 'italic'), foreground='gray').pack(pady=2)
        
        frame_botoes = ttk.Frame(self.tab_abrir)
        frame_botoes.pack(pady=5)
        
        ttk.Button(frame_botoes, text="Ver Galeria (App)", command=lambda: self.abrir_galeria_tabela(self.tree_last_box)).grid(row=0, column=0, padx=5)
        ttk.Button(frame_botoes, text="Ver resultados na Wiki (Web)", command=lambda: self.abrir_wiki_tabela(self.tree_last_box)).grid(row=0, column=1, padx=5)

    def action_abrir_pacotes(self):
        nome = self.entry_pacote.get().upper()
        if not os.path.exists(os.path.join('packs', f'{nome}.csv')):
            messagebox.showerror("Erro", f"Pacote {nome} não encontrado.")
            return

        try:
            qtt = int(self.entry_qtt.get())
            if qtt <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Aviso", "Quantidade inválida.")
            return

        self.btn_abrir.config(text="Abrindo...", state='disabled')
        box = pd.DataFrame(columns=['set', 'id', 'name', 'grade', 'clan', 'type', 'rarity', 'qtt'])
        
        for i in range(qtt):
            p = self.rodar_pacote(nome)
            if p is not None: box = self.atualizar_save(box, p)
            if i % 10 == 0: self.root.update()
        
        if not box.empty:
            box.sort_values(by=['id'], inplace=True)
            self.preencher_treeview(self.tree_last_box, box)
            try: save = pd.read_csv('save.csv').loc[:, ~pd.read_csv('save.csv').columns.str.contains('^Unnamed')]
            except: save = pd.DataFrame(columns=box.columns)
            
            save = self.atualizar_save(save, box)
            save.sort_values(by=['set', 'id'], inplace=True)
            save.to_csv('save.csv', index=False)
            self.atualizar_colecao_view()
        
        self.btn_abrir.config(text="Abrir Pacotes!", state='normal')

    # ==========================================
    # ABA 3 - COLEÇÃO
    # ==========================================
    def setup_tab_colecao(self):
        frame_filtros = ttk.Frame(self.tab_colecao)
        frame_filtros.pack(fill='x', pady=10, padx=10)

        self.cb_filtro = ttk.Combobox(frame_filtros, values=['Todos', 'name', 'rarity', 'grade', 'clan', 'type', 'set'], state='readonly', width=12)
        self.cb_filtro.current(0)
        self.cb_filtro.pack(side='left', padx=5)

        self.entry_busca = ttk.Entry(frame_filtros)
        self.entry_busca.pack(side='left', fill='x', expand=True, padx=5)

        ttk.Button(frame_filtros, text="Buscar", command=self.aplicar_filtro).pack(side='left', padx=5)

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
        self.lbl_stats = ttk.Label(frame_stats, text="Cartas Únicas: 0 | Total: 0", font=('Arial', 9, 'bold'))
        self.lbl_stats.pack(side='left')

        frame_botoes = ttk.Frame(frame_stats)
        frame_botoes.pack(side='right')
        ttk.Button(frame_botoes, text="Ver Galeria (App)", command=lambda: self.abrir_galeria_tabela(self.tree_colecao)).pack(side='left', padx=5)
        ttk.Button(frame_botoes, text="Ver na Wiki (Web)", command=lambda: self.abrir_wiki_tabela(self.tree_colecao)).pack(side='left')
        
        self.atualizar_colecao_view()

    def aplicar_filtro(self):
        try:
            df = pd.read_csv('save.csv')
            tipo = self.cb_filtro.get()
            valor = self.entry_busca.get().lower().strip()
            
            if tipo != 'Todos' and valor:
                df = df[df[tipo].astype(str).str.lower().str.contains(valor, na=False)]
            
            self.preencher_treeview(self.tree_colecao, df)
            self.atualizar_estatisticas(df)
        except Exception as e: pass

    def atualizar_colecao_view(self):
        try:
            df = pd.read_csv('save.csv')
            self.preencher_treeview(self.tree_colecao, df)
            self.atualizar_estatisticas(df)
        except: pass

    def atualizar_estatisticas(self, df):
        unicas = len(df)
        total = df['qtt'].sum() if not df.empty and 'qtt' in df.columns else 0
        self.lbl_stats.config(text=f"Cartas Únicas: {unicas} | Volume Total: {int(total)}")

    def setup_tab_pacotes(self):
        container = ttk.Frame(self.tab_pacotes)
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tree_pacotes = ttk.Treeview(container, columns=('set', 'link'), show='headings')
        self.tree_pacotes.heading('set', text='SET')
        self.tree_pacotes.heading('link', text='LINK DA WIKI')
        self.tree_pacotes.column('set', width=100, anchor='center')
        self.tree_pacotes.column('link', width=600, anchor='w')
        
        self.add_scrollbar(container, self.tree_pacotes)
        self.tree_pacotes.pack(side='left', fill='both', expand=True)

        try:
            self.preencher_treeview(self.tree_pacotes, pd.read_csv(os.path.join('packs', 'direct.csv')))
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = VanguardSimulatorGUI(root)
    root.mainloop()