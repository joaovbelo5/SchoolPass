from werkzeug.security import generate_password_hash
import csv
import os
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

class CadastroUsuariosGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cadastro de Usuários")
        self.arquivo_usuarios = 'usuarios.csv'
        self.setup_csv()
        self.create_widgets()
        self.listar_usuarios()

    def setup_csv(self):
        if not os.path.exists(self.arquivo_usuarios):
            with open(self.arquivo_usuarios, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["username", "password_hash"])

    def usuario_existe(self, username):
        if os.path.exists(self.arquivo_usuarios):
            with open(self.arquivo_usuarios, 'r') as file:
                reader = csv.reader(file)
                next(reader, None)
                for row in reader:
                    if row and row[0] == username:
                        return True
        return False

    def adicionar_usuario(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            messagebox.showerror("Erro", "Por favor, preencha todos os campos!")
            return

        if self.usuario_existe(username):
            messagebox.showerror("Erro", "Usuário já existe!")
            return

        hashed_password = generate_password_hash(password)
        with open(self.arquivo_usuarios, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([username, hashed_password])

        messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso!")
        self.entry_username.delete(0, tk.END)
        self.entry_password.delete(0, tk.END)
        self.listar_usuarios()

    def listar_usuarios(self):
        self.listbox_usuarios.delete(0, tk.END)
        if not os.path.exists(self.arquivo_usuarios):
            return
        with open(self.arquivo_usuarios, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)
            for row in reader:
                if row:
                    self.listbox_usuarios.insert(tk.END, row[0])

    def excluir_usuario(self):
        selecionado = self.listbox_usuarios.curselection()
        if not selecionado:
            messagebox.showerror("Erro", "Selecione um usuário para excluir!")
            return
        username = self.listbox_usuarios.get(selecionado[0])
        if not self.usuario_existe(username):
            messagebox.showerror("Erro", "Usuário não encontrado!")
            return
        try:
            usuarios = []
            with open(self.arquivo_usuarios, 'r') as file:
                reader = csv.reader(file)
                next(reader, None)
                usuarios = [row for row in reader if row and row[0] != username]
            with open(self.arquivo_usuarios, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["username", "password_hash"])
                writer.writerows(usuarios)
            messagebox.showinfo("Sucesso", "Usuário excluído com sucesso!")
            self.listar_usuarios()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir usuário: {str(e)}")


    def alterar_senha(self):
        selecionado = self.listbox_usuarios.curselection()
        if not selecionado:
            messagebox.showerror("Erro", "Selecione um usuário para alterar a senha!")
            return
        username = self.listbox_usuarios.get(selecionado[0])
        if not self.usuario_existe(username):
            messagebox.showerror("Erro", "Usuário não encontrado!")
            return
        nova_senha = simpledialog.askstring("Alterar Senha", f"Digite a nova senha para '{username}':", show='*', parent=self.root)
        if not nova_senha:
            messagebox.showerror("Erro", "A senha não pode ser vazia!")
            return
        try:
            usuarios = []
            with open(self.arquivo_usuarios, 'r') as file:
                reader = csv.reader(file)
                next(reader, None)
                for row in reader:
                    if row and row[0] == username:
                        row[1] = generate_password_hash(nova_senha)
                    usuarios.append(row)
            with open(self.arquivo_usuarios, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["username", "password_hash"])
                writer.writerows(usuarios)
            messagebox.showinfo("Sucesso", "Senha alterada com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao alterar senha: {str(e)}")

    def create_widgets(self):
        frame = tk.Frame(self.root)
        frame.pack(padx=10, pady=10)

        tk.Label(frame, text="Nome de Usuário:").grid(row=0, column=0, sticky="e")
        self.entry_username = tk.Entry(frame)
        self.entry_username.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame, text="Senha:").grid(row=1, column=0, sticky="e")
        self.entry_password = tk.Entry(frame, show="*")
        self.entry_password.grid(row=1, column=1, padx=5, pady=5)

        btn_add = tk.Button(frame, text="Cadastrar Usuário", command=self.adicionar_usuario)
        btn_add.grid(row=2, column=0, columnspan=2, pady=5)

        tk.Label(frame, text="Usuários cadastrados:").grid(row=3, column=0, columnspan=2)
        self.listbox_usuarios = tk.Listbox(frame, width=30)
        self.listbox_usuarios.grid(row=4, column=0, columnspan=2, pady=5)

        btn_del = tk.Button(frame, text="Excluir Usuário", command=self.excluir_usuario)
        btn_del.grid(row=5, column=0, columnspan=2, pady=5)

        btn_alterar = tk.Button(frame, text="Alterar Senha", command=self.alterar_senha)
        btn_alterar.grid(row=6, column=0, columnspan=2, pady=5)

        btn_sair = tk.Button(frame, text="Sair", command=self.root.quit)
        btn_sair.grid(row=7, column=0, columnspan=2, pady=5)

if __name__ == '__main__':
    root = tk.Tk()
    app = CadastroUsuariosGUI(root)
    root.mainloop()