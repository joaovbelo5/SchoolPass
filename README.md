# SchoolPass

Sistema de controle de acesso para portaria escolar, desenvolvido em Python com Flask.

Repositório oficial: [github.com/joaovbelo5/schoolpass](https://github.com/joaovbelo5/schoolpass)


## Sumário

- Descrição
- Pré-requisitos
- Instalação rápida (Windows)
- Configuração (.env e arquivos)
- Como executar (servidor e utilitários)
- Estrutura do projeto
- Backups e restauração
- Gerenciamento de usuários
- Segurança e boas práticas
- Contribuição e licença

## Descrição

O SchoolPass fornece registro de entradas/saídas, geração de carteirinhas com código de barras, upload/edição de fotos, monitoramento por turno (carômetro), registro de ocorrências e notificações via Telegram.
## Pré-requisitos

- Python 3.8+ (recomendado 3.10/3.11)
- pip
- No Windows: PowerShell (instruções abaixo consideram PowerShell)

Dependências do projeto (arquivo `requirements.txt`):

- Flask
- Werkzeug
- python-barcode
- Pillow
- requests
- python-dotenv
- Flask-Login
- pandas

Instale-as usando:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se preferir instalar pacotes manualmente:

```powershell
pip install Flask Werkzeug python-barcode Pillow requests python-dotenv Flask-Login pandas
```

## Configuração


1. Arquivos estáticos importantes (pasta `static`):

- `logo.svg` — logotipo exibido nas carteirinhas/admin
- `assinatura.png` — assinatura usada nas carteirinhas
- `static/fotos/` — fotos dos alunos (upload de  foto salva aqui)
- `static/barcodes/` — imagens de códigos de barras geradas

2. Base de dados e usuários

- `database.csv` — arquivo CSV com os dados dos alunos (campos esperados: Codigo, Nome, Turma, Turno, Foto, Permissao, ...). Mantenha um cabeçalho.
- `usuarios.csv` — arquivo CSV com usuários de acesso ao painel administrativo. As ferramentas `user_creator.py` (terminal) e `user_creator_gui.py` (GUI Tkinter) gerenciam esse arquivo.

Observação: o sistema preserva o cabeçalho do CSV ao executar operações de limpeza/backup.

## Como executar

O repositório inclui scripts de início que ajudam a executar o servidor e suas partes.

1) Iniciar servidor principal (inicia backend `admin` e `consulta` em subprocessos):

```powershell
python START_SERVER.py
```

Esse script inicia `start_admin_only.py` e `start_search_only.py` em processos separados e repassa stdout/stderr para o terminal.

2) Iniciar apenas o painel administrativo:

```powershell
python start_admin_only.py
```

3) Iniciar apenas a interface pública/consulta:

```powershell
python start_search_only.py
```

4) Porta padrão: os scripts usam Flask com porta 5000/5010 conforme o arquivo. Verifique as linhas `app.run(...)` nos scripts caso precise alterar porta/host.

## Ferramentas de gerenciamento de usuários

- `user_creator.py` — utilitário de terminal para adicionar/listar/excluir usuários no `usuarios.csv`. As senhas são guardadas como hash.
- `user_creator_gui.py` — interface Tkinter para gerenciar usuários (cadastrar, excluir, alterar senha).

## Estrutura principal (resumida)

```
.
├─ START_SERVER.py          # inicia admin + consulta como subprocessos
├─ start_admin_only.py      # aplicação Flask com rotas administrativas e principais
├─ start_search_only.py     # aplicação Flask pública de consulta/carteirinha
├─ user_creator.py          # utilitário CLI para gerenciar usuarios.csv
├─ user_creator_gui.py      # GUI Tkinter para gerenciar usuarios.csv
├─ database.csv             # dados dos alunos (CSV)
├─ usuarios.csv             # credenciais dos administradores (CSV)
├─ templates/               # templates Jinja2 (views)
└─ static/                  # css, imagens, barcodes, fotos, áudio
```

## Backups e restauração

O painel `/admin` possui endpoints para criar backup (`/admin/backup`) e restaurar (`/admin/restore`). O backup gera um ZIP em `backups/` e mantém arquivos por 3 horas (limpeza automática). A restauração exige o upload do ZIP gerado e uma frase de confirmação.

Você também pode criar backups manuais do diretório e dos CSVs.


## Resolução de problemas comuns

- Erro de locale pt_BR: o projeto tenta configurar `pt_BR.UTF-8`; se não existir, ele usa o locale padrão — isso é apenas informativo.
- Se imagens de barcode não aparecem, verifique se `static/barcodes` tem permissão de escrita e se as dependências Pillow/python-barcode estão instaladas.
- Problemas com Telegram: verifique `TELEGRAM_TOKEN` no `.env` e se o servidor consegue acessar a API do Telegram.

## Contribuição

1. Faça um fork.
2. Abra uma branch (`git checkout -b feature/x`).
3. Teste localmente e adicione testes mínimos se possível.
4. Abra um PR descrevendo a alteração.

## Licença

Veja o arquivo `LICENSE` na raiz do repositório.