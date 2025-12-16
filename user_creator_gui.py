import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import csv
import os
from werkzeug.security import generate_password_hash

class UserCreatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SchoolPass Users")
        self.root.geometry("500x650")
        self.root.configure(bg="#f8f9fa")  # Fundo suave
        self.filename = 'usuarios.csv'
        
        self.ensure_csv_exists()
        self.setup_styles()
        self.setup_ui()
        self.load_users()

    def ensure_csv_exists(self):
        """Garante a existência do CSV e verifica cabeçalho."""
        if not os.path.exists(self.filename):
            try:
                with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['username', 'password_hash', 'role'])
            except Exception as e:
                messagebox.showerror("Erro Crítico", f"Não foi possível criar o arquivo de banco de dados: {e}")
                self.root.destroy()
                return

        # Verificar migração simples
        try:
            rows = []
            with open(self.filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            if rows and len(rows[0]) == 2:
                rows[0].append('role')
                for i in range(1, len(rows)):
                    rows[i].append('admin')
                
                with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
        except Exception as e:
            messagebox.showwarning("Aviso", f"Possível erro na verificação do banco de dados: {e}")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')  # Base theme for better customization

        # Cores Minimalistas
        bg_color = "#f8f9fa"
        primary_color = "#2c3e50"
        accent_color = "#3498db"
        text_color = "#2c3e50"
        white = "#ffffff"

        style.configure(".", background=bg_color, foreground=text_color, font=("Segoe UI", 10))
        
        # Labels
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground=primary_color, background=bg_color)
        style.configure("SubHeader.TLabel", font=("Segoe UI", 10, "bold"), foreground="#7f8c8d", background=bg_color)

        # Buttons (Flat & Modern)
        style.configure("Accent.TButton",
                        foreground=white,
                        background=accent_color,
                        font=("Segoe UI", 10, "bold"),
                        borderwidth=0,
                        focuscolor=accent_color,
                        padding=(15, 8))
        style.map("Accent.TButton",
                  background=[('active', "#2980b9")])  # Darker blue on hover

        style.configure("Danger.TButton",
                        foreground=white,
                        background="#e74c3c",
                        font=("Segoe UI", 10),
                        borderwidth=0,
                        focuscolor="#e74c3c",
                        padding=(15, 8))
        style.map("Danger.TButton",
                  background=[('active', "#c0392b")])

        style.configure("Ghost.TButton",
                        foreground=primary_color,
                        background="#ecf0f1",
                        font=("Segoe UI", 10),
                        borderwidth=0,
                        focuscolor="#bdc3c7",
                        padding=(15, 8))
        style.map("Ghost.TButton",
                  background=[('active', "#bdc3c7")])

        # Entry
        style.configure("Card.TFrame", background=white, relief="flat")
        
        # Treeview
        style.configure("Treeview", 
                        background=white,
                        foreground=text_color,
                        fieldbackground=white,
                        borderwidth=0,
                        font=("Segoe UI", 10),
                        rowheight=30)
        style.configure("Treeview.Heading", 
                        background=bg_color, 
                        foreground=primary_color, 
                        font=("Segoe UI", 9, "bold"),
                        borderwidth=0)
        style.map("Treeview", background=[('selected', accent_color)])

    def setup_ui(self):
        # Container Principal com Padding
        main_container = ttk.Frame(self.root, padding=25)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Cabeçalho
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        ttk.Label(header_frame, text="Usuários", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Label(header_frame, text="Gerenciamento de Acesso", style="SubHeader.TLabel").pack(side=tk.LEFT, padx=(10,0), pady=(8,0))

        # Card de Formulário (Fundo Branco com Sombra simulada por borda sutil)
        form_card = ttk.Frame(main_container, style="Card.TFrame", padding=20)
        form_card.pack(fill=tk.X, pady=(0, 25))
        
        # Título do Card
        ttk.Label(form_card, text="NOVO USUÁRIO", font=("Segoe UI", 8, "bold"), foreground="#95a5a6", background="#ffffff").pack(anchor="w", pady=(0, 15))

        # Inputs Grid
        input_frame = ttk.Frame(form_card, style="Card.TFrame")
        input_frame.pack(fill=tk.X)

        # Usuário
        lbl_user = ttk.Label(input_frame, text="Nome de Usuário", background="#ffffff", font=("Segoe UI", 9))
        lbl_user.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.ent_username = ttk.Entry(input_frame, width=25, font=("Segoe UI", 10))
        self.ent_username.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))

        # Senha
        lbl_pass = ttk.Label(input_frame, text="Senha", background="#ffffff", font=("Segoe UI", 9))
        lbl_pass.grid(row=0, column=1, sticky="w")
        self.ent_password = ttk.Entry(input_frame, width=25, show="•", font=("Segoe UI", 10))
        self.ent_password.grid(row=1, column=1, sticky="ew", pady=(0, 15))
        
        input_frame.columnconfigure(0, weight=1)
        input_frame.columnconfigure(1, weight=1)

        # Permissão (Radio Buttons estilizados seriam complexos, usando padrão limpo)
        radio_frame = ttk.Frame(form_card, style="Card.TFrame")
        radio_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(radio_frame, text="Permissão", background="#ffffff", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        
        self.var_role = tk.StringVar(value="professor")
        
        s_radio = ttk.Style()
        s_radio.configure("BW.TRadiobutton", background="#ffffff", font=("Segoe UI", 10))
        
        r1 = ttk.Radiobutton(radio_frame, text="Professor (Acesso Restrito)", variable=self.var_role, value="professor", style="BW.TRadiobutton")
        r1.pack(anchor="w")
        r2 = ttk.Radiobutton(radio_frame, text="Administrador (Acesso Total)", variable=self.var_role, value="admin", style="BW.TRadiobutton")
        r2.pack(anchor="w")

        # Botão Adicionar (Full Width no Card)
        btn_add = ttk.Button(form_card, text="Adicionar Usuário", style="Accent.TButton", command=self.add_user)
        btn_add.pack(fill=tk.X, pady=(10, 0))

        # Botões de Ação Globais (Ao fundo, antes da lista)
        actions_frame = ttk.Frame(main_container)
        actions_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        btn_exit = ttk.Button(actions_frame, text="Sair", style="Ghost.TButton", command=self.root.quit)
        btn_exit.pack(side=tk.RIGHT)

        btn_pass = ttk.Button(actions_frame, text="Alterar Senha", style="Ghost.TButton", command=self.change_password)
        btn_pass.pack(side=tk.LEFT, padx=(0, 10))
        
        btn_del = ttk.Button(actions_frame, text="Excluir", style="Danger.TButton", command=self.delete_user)
        btn_del.pack(side=tk.LEFT)

        # Lista (Preenche o resto)
        tree_frame = ttk.Frame(main_container)
        tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        columns = ("username", "role")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("username", text="USUÁRIO", anchor="w")
        self.tree.heading("role", text="FUNÇÃO", anchor="w")
        
        self.tree.column("username", width=200, anchor="w")
        self.tree.column("role", width=100, anchor="w")
        
        # Scrollbar minimalista
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        # Hack para esconder scrollbar se não necessário ou estilizar (tkinter padrão é difícil estilizar scrollbar)
        
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_users(self):
        # Limpar
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            with open(self.filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.tree.insert("", tk.END, values=(row['username'], row.get('role', 'N/A')))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar usuários: {e}")

    def add_user(self):
        username = self.ent_username.get().strip()
        password = self.ent_password.get().strip()
        role = self.var_role.get()

        if not username or not password:
            messagebox.showwarning("Aviso", "Preencha usuário e senha.")
            return

        # Check exista
        if self.user_exists(username):
            messagebox.showerror("Erro", "Usuário já existe.")
            return

        pass_hash = generate_password_hash(password)

        try:
            with open(self.filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([username, pass_hash, role])
            
            messagebox.showinfo("Sucesso", f"Usuário {username} adicionado.")
            self.ent_username.delete(0, tk.END)
            self.ent_password.delete(0, tk.END)
            self.load_users()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")

    def delete_user(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um usuário para excluir.")
            return

        item = self.tree.item(selected[0])
        username = item['values'][0]

        if not messagebox.askyesno("Confirmar", f"Excluir usuário '{username}'?"):
            return

        try:
            rows = []
            with open(self.filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)

            new_rows = [rows[0]]
            for row in rows[1:]:
                if row[0] != username:
                    new_rows.append(row)

            with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(new_rows)
            
            messagebox.showinfo("Sucesso", "Usuário excluído.")
            self.load_users()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao excluir: {e}")

    def change_password(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um usuário para alterar a senha.")
            return

        item = self.tree.item(selected[0])
        username = item['values'][0]

        new_pass = simpledialog.askstring("Alterar Senha", f"Nova senha para '{username}':", show='*')
        if not new_pass:
            return

        try:
            rows = []
            with open(self.filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)

            header = rows[0]
            idx_user = 0
            idx_pass = 1
            
            # Localizar índices
            if 'username' in header: idx_user = header.index('username')
            if 'password_hash' in header: idx_pass = header.index('password_hash')

            updated = False
            for row in rows[1:]:
                if row[idx_user] == username:
                    row[idx_pass] = generate_password_hash(new_pass)
                    updated = True
                    break

            if updated:
                with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
                messagebox.showinfo("Sucesso", f"Senha de '{username}' alterada.")
            else:
                messagebox.showerror("Erro", "Usuário não encontrado no arquivo.")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao alterar senha: {e}")

    def user_exists(self, username):
        try:
            with open(self.filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['username'] == username:
                        return True
        except:
            pass
        return False

# Adicionar helper para margins no pack (tkinter < 8.7 não suporta mt/mb/ml/mr no pack, temos que usar pady/padx)
# Vou corrigir isso no código final abaixo, substituindo os mt=... por pady=(...)

if __name__ == "__main__":
    # Monkey patch pack to avoid rewriting logic for margins if I used shorthand above
    # But better to just clean up the code string before writing.
    root = tk.Tk()
    app = UserCreatorGUI(root)
    root.mainloop()