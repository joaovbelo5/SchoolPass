# 📘 Documentação Oficial - SchoolPass

Bem-vindo à documentação completa do **SchoolPass**, o sistema moderno de controle de acesso escolar, carteirinhas digitais e comunicação via Telegram.

---

## 📑 Índice

1. [Visão Geral](#visão-geral)
2. [Instalação e Deploy](#instalação-e-deploy)
3. [Manual do Usuário Detalhado](#manual-do-usuário-detalhado)
    - [Painel Administrativo](#painel-administrativo)
        - [Dashboard (Início)](#dashboard-início)
        - [Gestão de Alunos](#gestão-de-alunos)
        - [Carteirinhas](#carteirinhas)
        - [Ocorrências](#ocorrências)
        - [Comunicação (Mensagens)](#comunicação-mensagens)
        - [Relatórios (Histórico, Carômetro, Chamada)](#relatórios-histórico-carômetro-chamada)
    - [Área Pública / Totem](#área-pública--totem)
4. [Documentação Técnica](#documentação-técnica)
5. [Solução de Problemas](#solução-de-problemas)

---

## 🔭 Visão Geral

O **SchoolPass** simplifica a segurança escolar. Ele monitora entradas e saídas, notifica os pais via Telegram em tempo real, gerencia a disciplina dos alunos e envia notificações de alertas da escola para os pais, tudo em uma interface web moderna e responsiva.

---

## 🚀 Instalação e Deploy

### Opção 1: Docker (Recomendada)
1.  **Clone o repositório:** `git clone https://github.com/joaovbelo5/SchoolPass.git`
2.  **Execute:** `docker-compose up -d --build`
3.  **Acesse:**
    *   **Admin:** [http://localhost:5000](http://localhost:5000)
    *   **Público:** [http://localhost:5010](http://localhost:5010)

### Opção 2: Manual
1.  **Instale:** `pip install -r requirements.txt`
2.  **Execute:** `python start_server.py`

---

## 📖 Manual do Usuário Detalhado

Esta seção explica a função de cada página do sistema.

### 🔐 Painel Administrativo

Acesse via porta `5000`. Login necessário (usuário padrão deve ser criado via script `user_creator_gui.py`).

#### Dashboard (Início)
*   **Arquivo:** `index.html`
*   **Função:** É o centro de comando.
*   **Recursos:**
    *   **Indicadores:** Mostra quantos alunos estão na escola e quantos saíram hoje.
    *   **Feed em Tempo Real:** Lista as últimas entradas e saídas com fotos.
    *   **Botões de Ação:** Registro manual de entrada/saída (caso o aluno esqueça a carteirinha).
    *   **Configurações Rápidas:** No rodapé, permite alterar Logo, Assinatura e Token do Telegram.
    *   **Manutenção:** Botões para criar Backup (baixa um ZIP) e Restaurar dados.
    *   **Limpeza de Dados:** Área crítica para zerar o banco de dados na virada de ano (exige "senha matemática" para evitar acidentes).

#### Gestão de Alunos
*   **Arquivos:** `upload_novo.html`, `upload_editar.html`, `upload_index.html`
*   **Novo Aluno:**
    *   Preencha Nome, Turma, Turno e Telefone do Responsável.
    *   **Foto:** Você pode fazer upload de um arquivo ou usar a **Webcam** integrada para tirar a foto na hora. O sistema recorta e ajusta automaticamente.
*   **Pesquisar/Editar:**
    *   Lista todos os alunos. Use a barra de busca para filtrar por nome ou turma.
    *   Permite alterar dados cadastro ou atualizar a foto.
    *   Botão **Excluir**: Remove o aluno do sistema.

#### Carteirinhas
*   **Arquivos:** `carteirinha_index.html`, `carteirinha_template.html`
*   **Função:** Gerar documentos de identificação para impressão.
*   **Emissão por Turma:** Selecione uma turma e o sistema gera um "folhetão" com todas as carteirinhas prontas para recortar.
*   **Emissão Individual:** Digite o código do aluno para gerar apenas uma via.
*   **Design:** As carteirinhas incluem Foto, Nome, Turma, Código de Barras (Code128), Logo da escola e Assinatura do diretor.

#### Ocorrências
*   **Arquivos:** `ocorrencia_nova.html`, `ocorrencias_aluno.html`
*   **Função:** Livro digital de disciplina.
*   **Registro:** Busque um aluno e adicione uma ocorrência (ex: "Sem uniforme", "Atraso", "Indisciplina").
*   **Notificação:** Se a ocorrência for grave (Advertência/Suspensão), o sistema envia um alerta imediato para o Telegram dos pais com os detalhes.

#### Comunicação (Mensagens)
*   **Arquivo:** `mensagens.html`
*   **Função:** Canal oficial de avisos.
*   **Envio em Massa:** Escreva uma mensagem (use `{nome}` para personalizar com o nome do aluno) e envie para **Todos** ou uma **Turma** específica.
*   **Histórico:** Uma tabela mostra todas as mensagens já enviadas, data e quantos pais receberam.

#### Relatórios (Histórico, Carômetro, Chamada)
*   **Histórico (`historico.html`):** Visualize os logs de acesso de dias anteriores.
*   **Carômetro (`carometro.html`):** Uma grade com as fotos de todos os alunos de uma turma. Útil para professores novos ou inspetores identificarem alunos visualmente.
*   **Chamada Mensal (`lista_mensal_turma.html`):** Uma grade estilo "diário de classe" que mostra a presença de cada aluno ao longo do mês. Dias com presença ficam marcados em verde.

---

### 🌍 Área Pública / Totem

Acesse via porta `5010`. Interface simplificada para alunos e pais, sem necessidade de login administrativo.

#### Tela Inicial (Totem)
*   **Arquivo:** `index.html`
*   **Função:** Landing page moderna.
*   **Botões:** Acesso rápido à Consulta de Presença e ao Vínculo do Telegram.

#### Consulta de Presença
*   **Arquivo:** `public_consulta.html`
*   **Uso:** Pais podem receber o histórico de entrada e saída do aluno.
*   **Privacidade:** Exige saber o código exato do aluno para exibir os dados.

#### Cadastro Telegram
*   **Arquivo:** `cadastro_telegram.html`
*   **Finalidade:** Vincular o contato do pai ao sistema para receber notificações.
*   **Como funciona:** Após o pai fornecer o número de telefone, para a escola, ele deve clicar no botão "Vincular ao Telegram", ele receberá um link para autorizar o bot no Telegram.

---

## ⚙️ Documentação Técnica

### Arquitetura de Arquivos
*   `database.csv`: O "banco de dados". Contém: `Nome,Codigo,Turma,Turno,TelefoneResponsavel,TelegramID,Foto`.
*   `usuarios.csv`: Contém usuários admin e senhas (hash SHA-256).
*   `registros/{TURMA}/{CODIGO}.txt`: Log individual de cada aluno.
*   `static/fotos/`: Armazena imagens (JPG/PNG). O nome do arquivo é salvo no CSV.

### Fluxo de Dados
1.  **Leitura do Código de Barras:** O scanner age como teclado, digita o código e aperta Enter.
2.  **Processamento:** O backend recebe o código, busca no CSV, registra a data/hora no TXT do aluno.
3.  **Notificação:** Uma thread separada verifica se o aluno tem `TelegramID` e dispara a mensagem via API do Telegram.

---

## 🛠️ Solução de Problemas Comuns

*   **Fotos não aparecem na carteirinha:**
    *   Verifique se o arquivo existe em `static/fotos`. O nome no CSV deve bater exatamente com o nome do arquivo.
*   **Mensagens do Telegram não chegam:**
    *   O pai iniciou a conversa com o bot? O bot não pode mandar mensagem primeiro (regra anti-spam do Telegram).
    *   O token no `.env` está atualizado?
*   **Sistema lento:**
    *   Se o `database.csv` tiver milhares de linhas, operações de escrita podem demorar milissegundos a mais. O sistema usa "Lock" para evitar corrupção de dados ao salvar acessos simultâneos.

---
**SchoolPass** - Desenvolvido para agilidade e segurança.
