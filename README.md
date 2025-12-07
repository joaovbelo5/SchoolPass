# SchoolPass 🎓

> Sistema moderno de gerenciamento de acesso escolar, segurança e carteirinhas digitais.

O **SchoolPass** é uma solução completa para escolas que desejam modernizar o controle de entrada e saída de alunos. Com foco em segurança e facilidade de uso, o sistema oferece monitoramento em tempo real, emissão de carteirinhas com código de barras, e uma integração poderosa com o Telegram para notificar pais e responsáveis instantaneamente.

---

## ✨ Funcionalidades Principais

### 🚀 Controle de Acesso & Monitoramento
*   **Painel Administrativo (`start_admin_only.py`)**: Visão geral em tempo real de quem entra e sai da escola.
*   **Registro Automático & Manual**: Suporte para leitura de código de barras ou registro manual em caso de esquecimento da carteirinha.
*   **Carômetro Digital**: Visualização rápida dos alunos por turma com fotos para fácil identificação.
*   **Histórico Detalhado**: Logs individuais de acesso mantidos para cada aluno.

### 📱 Integração com Telegram
*   **Notificações Instantâneas**: Pais recebem mensagens no momento exato em que o aluno entra ou sai da escola.
*   **Bot Interativo**: Sistema fácil para vincular o contato do responsável ao cadastro do aluno.
*   **Alertas de Ocorrências**: Envio de advertências ou comunicados disciplinares diretamente pelo app.

### 💳 Carteirinhas Digitais
*   **Gerador Integrado**: Crie e imprima carteirinhas estudantis personalizadas automaticamente.
*   **Código de Barras**: Padrão Code128 para leitura rápida e eficiente.
*   **Personalizável**: Configure logo, assinatura, e dados da escola via painel.

### 🛡️ Segurança & Gestão
*   **Gestão de Usuários (`user_creator_gui.py`)**: Controle quem acessa o sistema com senhas criptografadas.
*   **Backup & Restore**: Ferramentas robustas para salvar e restaurar todos os dados do sistema (ZIP).
*   **Limpeza de Dados**: Função segura para virada de ano letivo ou manutenção.

---

## 🛠️ Tecnologias Utilizadas

*   **Backend**: Python 3 (Flask)
*   **Frontend**: HTML5, CSS3 (Design Responsivo), JavaScript
*   **Banco de Dados**: CSV (Simples, portável e eficiente para o escopo)
*   **Containerização**: Docker & Docker Compose
*   **Bibliotecas Chave**: `pandas` (dados), `python-barcode` (carteirinhas), `Pillow` (imagens).

---

## 🚀 Como Iniciar

### Opção 1: Docker (Recomendada) 🐳
A maneira mais fácil e limpa de rodar o projeto.

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/joaovbelo5/SchoolPass.git
    cd SchoolPass
    ```
2.  **Configure o ambiente:**
    Crie um arquivo `.env` na raiz (baseado no exemplo abaixo).
3.  **Execute com Docker Compose:**
    ```bash
    docker-compose up -d --build
    ```
    *   **Painel Admin**: [http://localhost:5000](http://localhost:5000)
    *   **Portal de Busca**: [http://localhost:5010](http://localhost:5010)

### Opção 2: Instalação Manual 🐍

1.  **Pré-requisitos:** Python 3.8+ instalado.
2.  **Crie um ambiente virtual:**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate
    ```
3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Inicie os servidores:**
    *   **Completo (Admin + Busca):** `python start_server.py`
    *   **Apenas Admin:** `python start_admin_only.py`
    *   **Apenas Busca:** `python start_search_only.py`

---

## ⚙️ Configuração (.env)

Crie um arquivo `.env` na raiz do projeto para configurar as variáveis essenciais:

```ini
# --- Telegram Bot ---
TELEGRAM_TOKEN=seu_token_aqui
# COOLDOWN_MINUTES=5 (opcional: tempo entre notificações repetidas)

# --- Carteirinha Escolar ---
CARTEIRINHA_ESCOLA=Nome da Escola
CARTEIRINHA_TELEFONE=(XX) XXXX-XXXX
CARTEIRINHA_ENDERECO=Rua, Número, Bairro
CARTEIRINHA_VALIDADE=31/12/2025

# --- Segurança ---
SECRET_KEY=sua_chave_secreta_aqui
```

---

## 👥 Gerenciando Usuários Admin

O sistema possui uma ferramenta gráfica dedicada para criar usuários administrativos.

1.  Execute o script:
    ```bash
    python user_creator_gui.py
    ```
2.  Utilize a interface para **Adicionar**, **Remover** ou **Listar** usuários que poderão acessar o painel administrativo.

---

## 📂 Estrutura do Projeto

*   `chamadas/`: Listas de chamadas por turma.
*   `registros/`: Logs individuais de entrada/saída por aluno.
*   `registros_diarios/`: Logs agrupados por dia (JSON).
*   `database.csv`: Cadastro principal de alunos.
*   `usuarios.csv`: Cadastro de administradores (hash).
*   `backups/`: Armazenamento de backups gerados.
*   `static/` & `templates/`: Arquivos do Frontend (Web).

---

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Sinta-se livre para usar e modificar.