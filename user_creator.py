from werkzeug.security import generate_password_hash
import csv
import os

class CadastroUsuariosTerminal:
    def __init__(self):
        self.arquivo_usuarios = 'usuarios.csv'
        # Garante que o arquivo CSV tenha um cabeçalho
        if not os.path.exists(self.arquivo_usuarios):
            with open(self.arquivo_usuarios, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["username", "password_hash"])  # Cabeçalho do CSV
        self.menu_principal()

    def usuario_existe(self, username):
        if os.path.exists(self.arquivo_usuarios):
            with open(self.arquivo_usuarios, 'r') as file:
                reader = csv.reader(file)
                next(reader, None)  # Ignora o cabeçalho
                for row in reader:
                    if row[0] == username:
                        return True
        return False

    def adicionar_usuario(self):
        username = input("Digite o nome do usuário: ").strip()
        password = input("Digite a senha: ").strip()

        if not username or not password:
            print("Erro: Por favor, preencha todos os campos!")
            return

        if self.usuario_existe(username):
            print("Erro: Usuário já existe!")
            return

        hashed_password = generate_password_hash(password)
        
        with open(self.arquivo_usuarios, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([username, hashed_password])
        
        print("Usuário cadastrado com sucesso!")

    def listar_usuarios(self):
        if not os.path.exists(self.arquivo_usuarios):
            print("Nenhum usuário cadastrado.")
            return

        print("\nUsuários cadastrados:")
        with open(self.arquivo_usuarios, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)  # Ignora o cabeçalho
            for row in reader:
                if row:  # Verifica se a linha não está vazia
                    print(f"- {row[0]}")

    def excluir_usuario(self):
        username = input("Digite o nome do usuário a ser excluído: ").strip()

        if not self.usuario_existe(username):
            print("Erro: Usuário não encontrado!")
            return

        try:
            usuarios = []
            with open(self.arquivo_usuarios, 'r') as file:
                reader = csv.reader(file)
                next(reader, None)  # Ignora o cabeçalho
                usuarios = [row for row in reader if row[0] != username]

            with open(self.arquivo_usuarios, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["username", "password_hash"])  # Reescreve o cabeçalho
                writer.writerows(usuarios)

            print("Usuário excluído com sucesso!")
        except Exception as e:
            print(f"Erro ao excluir usuário: {str(e)}")

    def menu_principal(self):
        while True:
            print("\n=== Menu Principal ===")
            print("1. Cadastrar Usuário")
            print("2. Listar Usuários")
            print("3. Excluir Usuário")
            print("4. Sair")
            opcao = input("Escolha uma opção: ").strip()

            if opcao == '1':
                self.adicionar_usuario()
            elif opcao == '2':
                self.listar_usuarios()
            elif opcao == '3':
                self.excluir_usuario()
            elif opcao == '4':
                print("Saindo...")
                break
            else:
                print("Opção inválida! Tente novamente.")

if __name__ == '__main__':
    CadastroUsuariosTerminal()