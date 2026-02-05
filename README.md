# SchoolPass - Sistema de Controle de Acesso e Notificação Escolar

O **SchoolPass** é uma solução completa para gestão de segurança escolar que une controle de acesso físico, comunicação com responsáveis e emissão de identidade estudantil. Desenvolvido para rodar localmente com alta performance, o sistema elimina a necessidade de infraestruturas complexas de nuvem e oferece total privacidade aos dados da escola.

Buscando simplicidade e eficiência, o SchoolPass opera com **dois servidores simultâneos**: um painel administrativo seguro para a gestão escolar e um portal público leve para pais e alunos consultarem históricos e carteirinhas digitais.

---

## 🚀 Funcionalidades Principais

*   **Portaria Inteligente**: Registro rápido de entrada e saída por código de barras ou busca manual.
*   **Dual-Server Architecture**:
    *   🔒 **Admin (:5000)**: Área protegida para secretaria e direção (Gestão de alunos, Relatórios, Configurações).
    *   🌍 **Público (:5010)**: Portal para pais acompanharem a presença em tempo real e alunos gerarem suas credenciais.
*   **Notificações via Telegram**: O sistema envia uma mensagem automática para o responsável assim que o aluno passa pela catraca/portaria.
*   **Gestão de Arquivo Morto (Legado)**: Um sistema de arquivamento que congela o ano letivo anterior, mantendo históricos antigos consultáveis sem misturar com os dados atuais.
*   **Carteirinhas Automáticas**: Geração instantânea de carteirinhas em PDF prontos para impressão.
*   **Controle de Usuários (RBAC)**: Níveis de acesso distintos para Administradores (Total) e Professores (Apenas registros e chamadas).

---

## 📋 Pré-requisitos

Para executar o SchoolPass, seu ambiente precisa de:

*   **Sistema Operacional**: Windows, Linux ou macOS.
*   **Python**: Versão 3.10 ou superior.
*   **Bibliotecas**: O sistema depende de pacotes como `Flask`, `Pillow` e `python-barcode` (instalados via `requirements.txt`).
*   *(Opcional)*: Leitor de código de barras USB para agilizar a operação na portaria.

---

## 🛠️ Instalação e Configuração

### 1. Clonando o Repositório
Baixe os arquivos para sua máquina:
```bash
git clone https://github.com/joaovbelo5/SchoolPass.git
cd SchoolPass
```

### 2. Configurando o Ambiente (Recomendado)
Crie um ambiente virtual para manter as dependências organizadas:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalando Dependências
```bash
pip install -r requirements.txt
```

### 4. Configuração Inicial
O sistema já vem com um arquivo `.env` padrão. **Não é necessário editá-lo manualmente agora.**
Ao iniciar o sistema pela primeira vez, acesse o painel Admin e use o menu **Configurações** para definir visualmente:
*   Nome da Escola
*   Tokens do Telegram
*   Logo e Assinatura da Carteirinha

---

## � Como Rodar com Docker (Avançado)

Se preferir manter seu ambiente limpo ou facilitar o deploy em servidores, use o Docker. O projeto já inclui `Dockerfile` e `docker-compose.yml` otimizados.

1.  **Tenha o Docker Instalado**: Certifique-se de ter o Docker Desktop (Windows/Mac) ou Docker Engine (Linux).
2.  **Suba os Containers**:
    Na pasta do projeto, rode:
    ```bash
    docker-compose up -d --build
    ```
3.  **Acesse**:
    O sistema estará disponível nas mesmas portas:
    *   Admin: `http://localhost:5000`
    *   Público: `http://localhost:5010`

> **Nota**: O volume está configurado para salvar os dados na própria pasta do projeto (`.:/app`). Isso garante que seus bancos de dados e fotos não se percam se o container for deletado.

---

## �💡 Tutoriais de Uso

Abaixo estão os guias para as tarefas mais comuns do dia a dia.

### 🟢 Como Rodar o Sistema (Diariamente)
Para colocar a escola "no ar", você só precisa de um comando. O script gerenciador cuidará de subir tanto o servidor administrativo quanto o público.

1.  Com o `venv` ativado, execute:
    ```bash
    python start_server.py
    ```
2.  Aguarde o banner de confirmação "Sistema Iniciado e Pronto para Uso".
3.  Acesse nos navegadores:
    *   **Gestão**: `http://localhost:5000`
    *   **Pais/Alunos**: `http://localhost:5010`

### 👥 Como Gerenciar Usuários (Adm e Professores)
O SchoolPass possui uma ferramenta visual dedicada para criar logins.

1.  Abra um novo terminal (ou execute antes de iniciar o servidor):
    ```bash
    python user_creator_gui.py
    ```
2.  Uma janela se abrirá. Preencha **Usuário** e **Senha**.
3.  Escolha a permissão:
    *   **Administrador**: Pode limpar dados, restaurar backups e alterar configurações globais.
    *   **Professor**: Acesso focado em chamadas, carômetro e registro de ocorrências.
4.  Clique em **Adicionar Usuário**.

### 🗓️ Virada de Ano: Arquivamento (Legado)
No final do ano letivo, você não perde nada. Use a função de *Legado* para limpar o sistema para o próximo ano.

1.  Acesse o Admin (`:5000`) e vá em **Arquivo Morto**.
2.  Digite o ano que se encerrou (ex: `2024`) e clique em **Arquivar**.
    *   *O que acontece nos bastidores:* O sistema move os históricos json, logs diários e ocorrências para a pasta `legacy/2024`, separando inteligentemente o que é antigo do que é novo.
3.  Após arquivar, vá em **Configurações** -> **Limpar Tudo**.
4.  Confirme a operação de segurança (Token + Cálculo).
5.  O sistema agora está vazio e pronto para receber a lista de alunos de 2025, mas os dados de 2024 continuam acessíveis para consulta no menu "Arquivo Morto".

---

## 📂 Estrutura do Projeto

Para desenvolvedores ou curiosos, aqui está como o projeto se organiza:

*   **`start_server.py`**: O "maestro". Inicia e monitora os subprocessos Admin e Search.
*   **`start_admin_only.py`**: A lógica pesada. Contém todas as rotas administrativas, gestão de arquivos e lógica de backup.
*   **`start_search_only.py`**: O portal leve. Focado em leitura rápida e exibição pública sem expor ferramentas de gestão.
*   **`archive_manager.py`**: O cérebro do arquivamento. Contém a lógica para separar históricos ativos de históricos passados.
*   **`registros/`**: Onde a mágica acontece. Cada turma tem uma pasta, e cada aluno tem um arquivo `.json` com todo seu histórico.
*   **`templates/` & `static/`**: Frontend (HTML/CSS) e arquivos de media (fotos dos alunos).

---

## 🤝 Contribuindo

O SchoolPass é Open Source! Se você quer ajudar a melhorá-lo:

1.  Faça um Fork do projeto.
2.  Crie uma branch para sua melhoria (`git checkout -b feature/nova-funcionalidade`).
3.  Submeta um Pull Request.

---

**Licença MIT** | Desenvolvido com ❤️ e Python.