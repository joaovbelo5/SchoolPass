import csv
import os
import sys
from werkzeug.security import generate_password_hash
from getpass import getpass

class UserCreatorCLI:
    def __init__(self):
        self.filename = 'usuarios.csv'
        self.ensure_csv_exists()

    def ensure_csv_exists(self):
        """Garante que o arquivo CSV existe com o cabeçalho correto."""
        if not os.path.exists(self.filename):
            try:
                with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['username', 'password_hash', 'role'])
                print(f"[INFO] Arquivo {self.filename} criado com sucesso.")
            except Exception as e:
                print(f"[ERRO] Falha ao criar arquivo: {e}")
                sys.exit(1)
        else:
            # Verificar se o cabeçalho está correto (migração simples)
            self.migrate_csv_header()

    def migrate_csv_header(self):
        """Verifica e corrige o cabeçalho se necessário."""
        try:
            rows = []
            with open(self.filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            if not rows:
                with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['username', 'password_hash', 'role'])
                return

            header = rows[0]
            if len(header) == 2 and header == ['username', 'password_hash']:
                print("[AVISO] Atualizando formato do CSV para suportar roles...")
                header.append('role')
                rows[0] = header
                # Atualizar linhas existentes com role padrão (admin, pois antes só havia admin)
                for i in range(1, len(rows)):
                    if len(rows[i]) == 2:
                        rows[i].append('admin')
                
                with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
                print("[INFO] Migração concluída.")
        except Exception as e:
            print(f"[ERRO] Falha na migração do CSV: {e}")

    def list_users(self):
        print("\n--- Usuários Cadastrados ---")
        try:
            with open(self.filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                users = list(reader)
                if not users:
                    print("Nenhum usuário encontrado.")
                else:
                    print(f"{'Usuário':<20} | {'Função':<15}")
                    print("-" * 38)
                    for user in users:
                        role = user.get('role', 'N/A')
                        print(f"{user['username']:<20} | {role:<15}")
        except Exception as e:
            print(f"[ERRO] Ao ler usuários: {e}")
        print("----------------------------")

    def add_user(self):
        print("\n--- Adicionar Novo Usuário ---")
        username = input("Nome de usuário: ").strip()
        if not username:
            print("[ERRO] Nome de usuário não pode ser vazio.")
            return

        # Verificar duplicidade
        if self.user_exists(username):
            print(f"[ERRO] O usuário '{username}' já existe.")
            return

        password = getpass("Senha: ").strip()
        if not password:
            print("[ERRO] Senha não pode ser vazia.")
            return

        print("\nSelecione a função (Role):")
        print("1. Admin (Acesso Total)")
        print("2. Professor (Acesso Restrito)")
        role_opt = input("Opção [2]: ").strip()
        
        role = 'admin' if role_opt == '1' else 'professor'

        password_hash = generate_password_hash(password)

        try:
            with open(self.filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([username, password_hash, role])
            print(f"[SUCESSO] Usuário '{username}' criado com a função '{role}'.")
        except Exception as e:
            print(f"[ERRO] Ao salvar usuário: {e}")

    def delete_user(self):
        print("\n--- Excluir Usuário ---")
        username = input("Nome de usuário a excluir: ").strip()
        if not username:
            return

        if not self.user_exists(username):
            print(f"[ERRO] Usuário '{username}' não encontrado.")
            return

        confirm = input(f"Tem certeza que deseja excluir '{username}'? (s/N): ").lower()
        if confirm != 's':
            print("Operação cancelada.")
            return

        try:
            rows = []
            with open(self.filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)

            new_rows = [rows[0]] # Header
            deleted = False
            for row in rows[1:]:
                if row[0] != username:
                    new_rows.append(row)
                else:
                    deleted = True

            if deleted:
                with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(new_rows)
                print(f"[SUCESSO] Usuário '{username}' excluído.")
            else:
                print("[ERRO] Usuário não encontrado durante a exclusão.")
        except Exception as e:
            print(f"[ERRO] Ao excluir usuário: {e}")

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

    def run(self):
        while True:
            print("\n=== Gerenciador de Usuários (CLI) ===")
            print("1. Listar Usuários")
            print("2. Adicionar Usuário")
            print("3. Excluir Usuário")
            print("4. Sair")
            
            choice = input("Escolha uma opção: ").strip()

            if choice == '1':
                self.list_users()
            elif choice == '2':
                self.add_user()
            elif choice == '3':
                self.delete_user()
            elif choice == '4':
                print("Saindo...")
                break
            else:
                print("Opção inválida.")

if __name__ == "__main__":
    app = UserCreatorCLI()
    app.run()