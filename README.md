# SchoolPass

O SchoolPass é um sistema de gerenciamento de acesso e registros para escolas, projetado para modernizar e simplificar o controle de entrada e saída de alunos, a geração de carteirinhas estudantis e o registro de ocorrências.

## ✨ Funcionalidades

*   **Controle de Acesso:** Registra a entrada e saída de alunos através da leitura de códigos de barras.
*   **Gerador de Carteirinhas:** Cria e personaliza carteirinhas estudantis com foto, informações do aluno e código de barras.
*   **Carômetro:** Uma interface visual para consulta rápida de alunos por turma.
*   **Histórico de Acesso:** Mantém um registro detalhado de todos os acessos dos alunos.
*   **Gestão de Ocorrências:** Permite o registro e a consulta de ocorrências disciplinares ou de outra natureza.
*   **Alertas no Telegram:** Envia notificações em tempo real para um chatbot no Telegram no momento da entrada ou saída do aluno.
*   **Níveis de Acesso:** Módulos separados para administração completa e para consulta/busca de alunos.
*   **Interface Web:** Acessível a partir de qualquer dispositivo na rede local.

## 🛠️ Tecnologias Utilizadas

*   **Backend:** Python com [Flask](https://flask.palletsprojects.com/)
*   **Frontend:** HTML, CSS, JavaScript
*   **Banco de Dados:** Arquivos CSV (gerenciados com a biblioteca [Pandas](https://pandas.pydata.org/))
*   **Geração de Código de Barras:** [python-barcode](https://pypi.org/project/python-barcode/)
*   **Manipulação de Imagens:** [Pillow](https://python-pillow.org/)
*   **Autenticação:** [Flask-Login](https://flask-login.readthedocs.io/)

## 🚀 Instalação e Execução

Siga os passos abaixo para configurar e executar o projeto em seu ambiente local.

### Pré-requisitos

*   [Python 3.8+](https://www.python.org/downloads/)
*   pip (gerenciador de pacotes do Python)

### 1. Clone o Repositório

```bash
git clone https://github.com/joaovbelo5/SchoolPass.git
cd SchoolPass
```

### 2. Crie um Ambiente Virtual

É uma boa prática usar um ambiente virtual para isolar as dependências do projeto.

```bash
# Para Windows
python -m venv venv
venv\Scripts\activate

# Para macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências

Instale todas as bibliotecas necessárias a partir do arquivo `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 4. Execute o Servidor

Para iniciar a aplicação principal com todas as funcionalidades de administrador, execute:

```bash
python START_SERVER.py
```

O servidor estará disponível em `http://IP_DO_SERVIDOR:5000` (administrador e registros) e `http://IP_DO_SERVIDOR:5010` (consulta/busca).

### Módulos Adicionais

O projeto inclui scripts para iniciar a aplicação em modos específicos:

*   **Admin (somente):** `python start_admin_only.py`
*   **Busca (somente):** `python start_search_only.py`

## 📂 Estrutura de Arquivos

```
SchoolPass/
├─── static/              # Arquivos estáticos (CSS, JS, imagens, sons)
├─── templates/           # Templates HTML do Flask
├─── .env                 # Arquivo de variáveis de ambiente (deve ser criado)
├─── database.csv         # "Banco de dados" principal com informações dos alunos
├─── usuarios.csv         # "Banco de dados" de usuários do sistema
├─── requirements.txt     # Lista de dependências do Python
├─── START_SERVER.py      # Script principal para iniciar a aplicação
└─── ...                  # Outros arquivos e pastas
```

## 🤝 Contribuições

Contribuições são bem-vindas! Se você tem ideias para melhorias ou encontrou um bug, sinta-se à vontade para abrir uma *issue* ou enviar um *pull request*.

1.  Faça um *fork* do projeto.
2.  Crie uma nova *branch* (`git checkout -b feature/nova-funcionalidade`).
3.  Faça o *commit* de suas alterações (`git commit -m 'Adiciona nova funcionalidade'`).
4.  Faça o *push* para a *branch* (`git push origin feature/nova-funcionalidade`).
5.  Abra um *Pull Request*.

## 📄 Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.