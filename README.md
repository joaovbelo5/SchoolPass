# SchoolPass

O **SchoolPass** é um sistema completo de gerenciamento de acesso e segurança escolar. Ele moderniza o controle de entrada e saída de alunos, oferece carteirinhas digitais, integrações com Telegram para notificações em tempo real e ferramentas administrativas robustas para gestão de dados e usuários.

## ✨ Funcionalidades Principais

### 🏢 Painel Administrativo (`start_admin_only.py`)
O coração do sistema para a equipe da escola.
*   **Monitoramento em Tempo Real**: Visualize entradas e saídas conforme elas acontecem.
*   **Registro Manual**: Registre acessos manualmente caso o aluno esqueça a carteirinha.
*   **Gestão de Dados**: Ferramentas para backup (ZIP), restauração e limpeza segura do banco de dados.
*   **Carômetro**: Visualização rápida de todos os alunos por turma com fotos.
*   **Histórico Completo**: Logs detalhados de acesso de cada aluno.

### 🔍 Portal de Consulta (`start_search_only.py`)
Interface pública ou restrita para alunos e responsáveis.
*   **Busca de Alunos**: Encontre alunos por código e turma.
*   **Carteirinha Digital**: Visualize e imprima a carteirinha estudantil com código de barras.
*   **Histórico de Acesso**: Consulte os registros de entrada e saída do aluno.
*   **Integração Telegram**: Vincule um ID do Telegram para receber notificações.

### 📱 Notificações via Telegram
*   **Alertas em Tempo Real**: Os responsáveis recebem uma mensagem instantânea no Telegram sempre que o aluno entra ou sai da escola.
*   **Cadastro Fácil**: Interface dedicada para vincular o usuário do Telegram ao perfil do aluno.

### 👥 Gerenciador de Usuários (`user_creator_gui.py`)
Uma ferramenta gráfica (GUI) para gerenciar quem tem acesso ao sistema.
*   **Interface Amigável**: Janela desktop simples para adicionar, remover e editar usuários.
*   **Segurança**: As senhas são armazenadas com hash seguro.

---

## 🚀 Instalação

### Pré-requisitos
*   Python 3.8 ou superior
*   Git

### Passo a Passo

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/joaovbelo5/SchoolPass.git
    cd SchoolPass
    ```

2.  **Crie e ative um ambiente virtual:**
    *   Windows:
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```
    *   Linux/Mac:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

---

## ⚙️ Configuração

Crie um arquivo `.env` na raiz do projeto para configurar as variáveis de ambiente. Você pode usar o arquivo `.env.example` (se existir) como base.

**Exemplo de `.env`:**
```ini
# Configurações do Telegram
TELEGRAM_BOT_TOKEN=seu_token_do_bot_aqui

# Configurações da Carteirinha
CARTEIRINHA_ESCOLA=Nome da Sua Escola
CARTEIRINHA_TELEFONE=(XX) XXXXX-XXXX
CARTEIRINHA_ENDERECO=Rua Exemplo, 123
CARTEIRINHA_VALIDADE=31/12/2025

# Outras Configurações
SECRET_KEY=sua_chave_secreta_flask
```

---

## 🖥️ Como Usar

### 1. Iniciar o Servidor Completo
Para rodar tanto o painel administrativo quanto a busca simultaneamente (recomendado para testes ou servidores unificados):
```bash
python start_server.py
```
*   **Admin:** `http://localhost:5000`
*   **Busca:** `http://localhost:5010`

### 2. Rodar Módulos Separadamente
Se preferir rodar serviços em portas ou máquinas diferentes:

*   **Apenas Admin:**
    ```bash
    python start_admin_only.py
    ```
*   **Apenas Busca:**
    ```bash
    python start_search_only.py
    ```

### 3. Gerenciar Usuários do Sistema
Para criar logins para o painel administrativo, execute a ferramenta gráfica:
```bash
python user_creator_gui.py
```
Uma janela abrirá permitindo cadastrar novos administradores.

---

## 📂 Estrutura do Projeto

*   `start_admin_only.py`: Servidor Flask do painel administrativo.
*   `start_search_only.py`: Servidor Flask da busca pública.
*   `user_creator_gui.py`: Interface Tkinter para gestão de usuários (`usuarios.csv`).
*   `database.csv`: Banco de dados principal com informações dos alunos.
*   `usuarios.csv`: Banco de dados de usuários do sistema (admin).
*   `registros/`: Pasta onde são salvos os logs de acesso individuais (`.txt`).
*   `backups/`: Pasta para armazenamento de backups gerados pelo sistema.
*   `templates/`: Arquivos HTML (Jinja2).
*   `static/`: Arquivos CSS, JS e imagens.

## 🛠️ Tecnologias

*   **Backend:** Python (Flask)
*   **Frontend:** HTML5, CSS3, JavaScript
*   **Dados:** CSV (Pandas)
*   **GUI Desktop:** Tkinter
*   **Outros:** `python-barcode`, `Pillow` (processamento de imagem)