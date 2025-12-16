# SchoolPass - Sistema de Controle de Acesso Escolar

O **SchoolPass** é um sistema completo para gerenciamento de acesso escolar, emissão de carteirinhas digitais e comunicação automática com responsáveis via Telegram. Desenvolvido para ser robusto, independente e fácil de implantar.

## 🚀 Funcionalidades Principais

*   **Arquitetura Dual-Server**: O sistema opera com dois servidores simultâneos para maior segurança e organização:
    *   **Servidor Admin (Porta 5000)**: Acesso restrito para gestão, configurações e controle.
    *   **Servidor Público (Porta 5010)**: Portal de consulta para alunos e pais verem históricos e carteirinhas.
*   **Controle de Acesso**: Registro de entrada e saída de alunos, com suporte a leitura de códigos de barras.
*   **Carteirinhas Digitais**: Geração automática de carteirinhas estudantis (PDF/Impressão) com código de barras integrado.
*   **Integração com Telegram**: O sistema envia notificações em tempo real para os pais quando o aluno entra ou sai da escola (requer configuração do Bot).
*   **Gestão de Ocorrências**: Registro de ocorrências disciplinares ou observações no histórico do aluno.
*   **Modo Legado (Arquivamento)**: Capacidade de arquivar anos letivos anteriores (Ex: 2024, 2023) e consultá-los em modo somente-leitura.
*   **Painel Administrativo Completo**:
    *   Configuração visual (Logo, Assinatura) via upload.
    *   Backups instantâneos e restauração de dados.
    *   Limpeza segura de dados para iniciar novos períodos.

## 🛠️ Instalação e Configuração

### Pré-requisitos

*   **Python 3.12+** (para execução local)
*   Ou **Docker** e **Docker Compose** (para execução em container)

### Configuração Inicial (.env)

O projeto já contém um arquivo `.env` na raiz. Este arquivo armazena configurações sensíveis iniciais.

> [!IMPORTANT]
> A maioria das configurações do dia a dia (Nome da Escola, Telefone, Validade da Carteirinha, Tokens) pode e deve ser alterada diretamente pelo **Painel Administrativo** (`/admin`) após o sistema estar rodando. Evite editar o `.env` manualmente a menos que seja necessário alterar chaves de criptografia ou configurações de boot.

---

## 💻 Como Rodar (Localmente)

Siga os passos abaixo para rodar o projeto diretamente em sua máquina Windows, Linux ou Mac.

1.  **Crie um Ambiente Virtual (Recomendado)**:
    Isso isola as dependências do projeto do seu sistema principal.
    ```bash
    # Criação do venv
    python -m venv venv

    # Ativação (Windows)
    venv\Scripts\activate

    # Ativação (Linux/Mac)
    source venv/bin/activate
    ```

2.  **Instale as Dependências**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Inicie o Servidor**:
    Execute o script gerenciador que iniciará tanto o servidor Admin quanto o Público/Busca.
    ```bash
    python start_server.py
    ```

4.  **Acesse o Sistema**:
    *   **Admin**: Abra `http://localhost:5000` (ou use o IP da sua máquina, ex: `http://192.168.1.X:5000`).
    *   **Público**: Abra `http://localhost:5010` (ou use o IP da sua máquina).

---

## 🐳 Como Rodar (Via Docker)

Se preferir usar containers para uma infraestrutura mais limpa e reprodutível.

1.  Certifique-se de ter o Docker e Docker Compose instalados.
2.  Na raiz do projeto, execute:
    ```bash
    docker-compose up --build -d
    ```
3.  O sistema estará acessível nas mesmas portas:
    *   **Admin**: Porta `5000`
    *   **Público**: Porta `5010`

---

## 👥 Gerenciamento de Usuários

O sistema possui um controle de usuários (RBAC) com níveis de acesso (Admin e Professor). Para criar ou gerenciar usuários, utilize as ferramentas inclusas:

### Opção 1: Interface Gráfica (Recomendado)
Execute a ferramenta visual de gerenciamento de usuários:
```bash
python user_creator_gui.py
```
*   Permite criar, deletar e alterar senhas de forma fácil.
*   Defina se o usuário é "Admin" (acesso total) ou "Professor" (acesso restrito apenas a registros).

### Opção 2: Linha de Comando
Se você estiver em um servidor sem interface gráfica:
```bash
python user_creator.py
```
Siga as instruções no terminal para adicionar ou remover usuários.

---

## 📂 Estrutura do Projeto

*   `start_server.py`: Script principal que gerencia os processos `start_admin_only.py` e `start_search_only.py`.
*   `templates/`: Arquivos HTML do frontend (Jinja2).
*   `static/`: Arquivos CSS, JS, imagens e uploads (fotos de alunos).
*   `legacy/`: Armazena dados de anos anteriores arquivados.
*   `backups/`: Local onde os backups gerados pelo painel admin são salvos temporariamente.
*   `registros/`: Banco de dados de registros de entrada/saída (JSON organizados por turma).

---

## 📝 Licença

Este projeto usa licença MIT.