# Documentação Técnica - SchoolPass

## 1. Introdução

O **SchoolPass** é um sistema completo de gestão de acesso escolar e emissão de identidade digital (carteirinhas). Ele foi projetado para operar com infraestrutura leve, sem necessidade de bancos de dados complexos (SQL), utilizando um sistema híbrido de arquivos CSV e JSON para persistência de dados.

### Visão Geral da Arquitetura
O sistema opera em uma arquitetura de **Processo Duplo (Dual-Process Monolith)** gerenciada por um orquestrador central.

*   **Orquestrador (`start_server.py`)**: Script responsável por iniciar e monitorar os sub-processos.
*   **Serviço Admin (Porta 5000)**: Aplicação Flask protegida por login, onde a administração escolar gerencia alunos, emite carteirinhas e visualiza relatórios.
*   **Serviço de Busca Pública (Porta 5010)**: Aplicação Flask leve e otimizada para leitura, permitindo que alunos e pais consultem a validade da carteirinha e o histórico de acesso via Código de Barras.

---

## 2. Instalação e Configuração

### Opção A: Instalação Manual (Python)

#### Pré-requisitos
*   **Python 3.12+** instalado e adicionado ao PATH.
*   Sistemas Operacionais: Linux (recomendado), Windows ou macOS (não testado).

#### Passos
1.  **Clone o Repositório:**
    ```bash
    git clone https://github.com/joaovbelo5/schoolpass.git
    cd schoolpass
    ```

2.  **Instale as Dependências:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate     # Windows
    pip install -r requirements.txt
    ```

3.  **Inicialização:**
    ```bash
    python start_server.py
    ```

### Opção B: Instalação via Docker (Recomendado)

O projeto já inclui configuração completa para Docker (`Dockerfile` e `docker-compose.yml`).

1.  **Subir o Container:**
    Na raiz do projeto, execute:
    ```bash
    docker-compose up -d
    ```
    Isso irá construir a imagem e iniciar os serviços nas portas `5000` (Admin) e `5010` (Busca).

2.  **Persistência:**
    O volume `./:/app` garante que os dados (`database.csv`, `registros/`, etc.) sejam salvos diretamente na sua pasta local, facilitando backups manuais.

### Configuração do Ambiente (.env)

O arquivo `.env` controla variáveis críticas como chaves de segurança e tokens.
> [!WARNING]
> **Não edite o arquivo .env manualmente** a menos que saiba exatamente o que está fazendo. A maioria das configurações (Nome da Escola, Token do Telegram, etc.) pode e deve ser alterada diretamente pelo painel administrativo em `/admin`.

Exemplo de variáveis geridas pelo sistema:
```ini
CARTEIRINHA_ESCOLA="Nome da Escola"
TELEGRAM_TOKEN="seu_token"
SECRET_KEY="chave_interna"
```

---

## 3. Arquitetura de Dados (File-DB) Detalhada

O SchoolPass utiliza arquivos locais para garantir portabilidade total. Entenda a função de cada componente:

| Arquivo / Diretório | Função Específica | Importância |
| :--- | :--- | :--- |
| **`database.csv`** | **Cadastro Mestre**. Armazena a lista de todos os alunos ativos com seus dados (Nome, Código, Turma, Turno, Foto, TelegramID). | Crítica. Se perdido, perde-se o cadastro dos alunos. |
| **`registros/{TURMA}/{CODIGO}.json`** | **Histórico Individual**. Contém o log detalhado de todas as entradas e saídas de *um único aluno*. | Alta. Garante que o acesso simultâneo não trave o sistema todo (sharding por arquivo). |
| **`registros_diarios/YYYY-MM-DD.json`** | **Log Cronológico**. Um espelho de todos os acessos do dia, em ordem de acontecimento. Útil para auditoria ("Quem entrou na escola entre 13:00 e 13:10?"). | Média. Redundância de segurança. |
| **`chamadas/`** | **Frequência Mensal**. Arquivos JSON que consolidam a presença diária de uma turma inteira para gerar relatórios de grade. | Alta. Alimenta a tela de "Chamada Mensal". |
| **`ocorrencias/*.json`** | **Disciplinar**. Armazena observações comportamentais, advertências e suspensões vinculadas ao aluno. | Alta. Dados sensíveis do aluno. |

### Ciclo de Vida e Arquivamento
Ao final do ano letivo, o sistema permite mover dados antigos para uma pasta `legacy/`.
> [!IMPORTANT]
> **NUNCA execute o script `archive_manager.py` manualmente.** Utilize sempre a função **"Arquivo Morto" no Painel Admin**. O sistema realiza verificações de segurança e integridade que o script manual pode pular se usado incorretamente.

---

## 4. Manual do Painel Administrativo

O painel administrativo (`/admin`) é o centro de controle.

### Dashboard Principal
Ao entrar, você verá métricas em tempo real:
*   **Total de Alunos e Turmas.**
*   **Presenças Hoje:** Contagem em tempo real de entradas únicas.
*   **Status do Telegram:** Indica se o bot de notificações está online.
*   **Atalhos Rápidos:** Botões configuráveis para as funções que você mais usa.
*   **Atividade Recente:** Mostra os últimos 10 registros de acesso.

### Funcionalidades por Aba

#### 1. Registro (Totem)
Esta tela foi desenhada para ficar exposta em um tablet ou computador na portaria (Totem).
*   Mostra feedback visual grande (Verde/Vermelho) para os alunos que passam a carteirinha.
*   Emite alertas sonoros em caso de erro.

#### 2. Cadastro de Alunos
O gerenciador completo de estudantes. Aqui você pode:
*   **Editar:** Alterar foto, nome ou turma.
*   **Histórico:** Visualizar a lista completa de acessos daquele aluno específico.
*   **Ocorrências:** Registrar advertências (que podem notificar os pais via Telegram).
*   **Correção de Presença:** Inserir manualmente uma entrada/saída caso o aluno tenha esquecido a carteirinha.
*   **Importação em Lote:** Envie uma lista CSV (`Nome, Turma, Turno`) para cadastrar centenas de alunos de uma vez. O sistema gera os códigos automaticamente.

#### 3. Mensagens em Massa
Ferramenta para comunicação institucional.
*   Permite enviar mensagens de texto para **todos os alunos** de uma determinada turma (ou turno) que tenham Telegram vinculado.
*   Útil para avisos de provas, passeios ou emergências.

#### 4. Relatórios
*   **Carômetro:** Visualização das fotos da turma toda em grade.
*   **Chamada Mensal:** Tabela cruzada (Aluno x Dias do Mês) para visualizar faltas.

---

## 5. Backup e Recuperação

O sistema possui proteção contra perda de dados.

*   **Backup (Download):** O botão "Backup" no menu lateral gera um arquivo `.zip` contendo TUDO (banco de dados, fotos, configurações e logs). Baixe-o periodicamente.
*   **Restauração:** Se o servidor der problema, você pode subir esse mesmo `.zip` na opção "Restauração". O sistema irá descomprimir e restaurar todos os arquivos para o estado exato do backup.

### Limpeza de Dados (Wipe)
A opção "Zerar Dados" é irreversível e exige tripla verificação (Token + Matemática + Frase de Segurança). Use apenas para resetar o sistema para um novo ano limpo (após fazer backup/arquivamento).

---

## 6. Busca Pública

A rota `/` é a interface leve para validação.
1.  **Escaneamento:** O aluno passa o código de barras.
2.  **Validação:** O sistema mostra Foto, Nome, Turma e, mais importante, a **Permissão de Entrada** (Sim/Não).

### Feedback Sonoro
O sistema dispara um alerta sonoro (`alert.mp3`) especificamente quando a **permissão de entrada é negada** ou o aluno não é encontrado, alertando o inspetor sem que ele precise olhar para a tela o tempo todo.

---

## 7. Ferramentas de Manutenção (Desenvolvedores)

### Kit de Emergência
Se você perder o acesso ao painel web (esqueceu a senha admin), acesse o servidor via terminal e use:

*   **`user_creator_gui.py`**: Interface gráfica para resetar senhas ou criar novos admins.
*   **`user_creator.py`**: Versão em linha de comando (CLI) para a mesma função.
    *   *Nota:* Estes scripts só rodam localmente no servidor por segurança.
