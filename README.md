# SchoolPass

Sistema de controle de acesso para portaria escolar, desenvolvido em Python com Flask.

Repositório oficial: [github.com/joaovbelo5/schoolpass](https://github.com/joaovbelo5/schoolpass)

---

## Funcionalidades

- Registro de **entradas e saídas** com histórico diário e geral.
- **Geração automática de carteirinhas** com código de barras (Code128) e foto do usuário.
- **Upload e edição de fotos** de alunos.
- **Monitoramento em tempo real** do número de pessoas presentes por dia de acordo com o turno.
- **Notificações no Telegram** para avisar os pais quando o filho chega ou sai da escola.
- Administração web completa: dados da instituição, token do bot, logo e assinatura, tudo via painel `/admin`.

---

## 📂 Estrutura do Projeto

```
.  
├── LICENSE
├── README.md
├── requirements.txt
├── start_server.py
├── database.csv
├── usuarios.csv
├── registros/
├── registros_diarios/
├── static/
│   ├── alert.mp3
│   ├── assinatura.png
│   ├── barcodes/
│   ├── fotos/
│   └── style.css
└── templates/
   ├── base.html
   ├── index.html
   ├── login.html
   ├── consulta.html
   ├── historico.html
   ├── carometro.html
   ├── carteirinha_index.html
   ├── carteirinha_template.html
   ├── upload_index.html
   ├── upload_novo.html
   ├── upload_editar.html
   └── erro.html
```

---

## ⚙️ Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/joaovbelo5/schoolpass.git
   cd schoolpass
   ```

2. **Crie um ambiente virtual e ative-o:**
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   source venv/bin/activate # Linux/macOS
   ```

3. **Instale as dependências:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure o sistema:**
   - Edite o arquivo `.env` com os dados da instituição, token do Telegram, logo e assinatura.
   - Crie usuários de acesso no arquivo `usuarios.csv` (usuário e senha padrão: admin/admin).
   - Substitua os arquivos `logo.svg` e `assinatura.png` na pasta `static/` conforme sua escola.

---

## 🚀 Uso

1. **Inicie o servidor:**
   ```bash
   python start_server.py
   ```

2. **Acesse no navegador:**
   ```
   http://localhost:5000 ou http://IP_DO_SERVIDOR:5000
   ```

3. **Faça login** e utilize as funcionalidades:
   - Gerenciar registros de entrada/saída
   - Consultar histórico
   - Gerar carteirinhas
   - Upload/edição de fotos
   - Monitorar carômetro
   - Receber notificações no Telegram
   - Administrar dados da escola via `/admin`

---

## 🤝 Contribuição

1. Faça um _fork_ do projeto.
2. Crie uma _branch_ para sua feature: `git checkout -b feature/nova-funcionalidade`.
3. Commit suas mudanças: `git commit -m 'Adiciona X'`.
4. Envie para o remoto: `git push origin feature/nova-funcionalidade`.
5. Abra um _Pull Request_ detalhando as alterações.

---

## 📄 Licença

Este projeto está sob a licença descrita em [LICENSE](LICENSE).
# SchoolPass

Sistema de controle de acesso para portaria escolar, desenvolvido em Python com Flask, que permite:

- Registro de **entradas e saídas** com histórico diário e geral.
- **Geração automática de carteirinhas** com código de barras (Code128) e foto do usuário.
- **Upload e edição de fotos** de alunos.
- **Monitoramento em tempo real** do número de pessoas presentes por dia de acordo com o turno.
- **Notificações no Telegram** para avisar os pais quando o filho chegar e sair da escola.
- Ferramentas auxiliares para **configuração** (dados da instituição, token do bot, logo e assinatura).

---

## 📂 Estrutura do Projeto

```
.
├── .gitattributes
├── LICENSE
├── README.md
├── requirements.txt
├── start_server.py
├── change_telegram_token.py
├── change_info_id.py
├── change_logo_sign_gui.py
├── user_creator.py
├── database.csv
├── usuarios.csv
├── registros/
├── registros_diarios/
├── static/
│   ├── alert.mp3
│   ├── assinatura.png
│   ├── barcodes/
│   ├── fotos/
│   └── style.css
└── templates/
    ├── base.html
    ├── index.html
    ├── login.html
    ├── consulta.html
    ├── historico.html
    ├── carometro.html
    ├── carteirinha_index.html
    ├── carteirinha_template.html
    ├── upload_index.html
    ├── upload_novo.html
    ├── upload_editar.html
    └── erro.html
```

---

## ⚙️ Instalação

1. **Clone** o repositório:
   ```bash
   git clone https://github.com/gordaoescolas/schoolpass.git
   cd schoolpass
   ```

2. **Crie** um ambiente virtual e ative-o:
   ```bash
   python3 -m venv venv
   source venv/bin/activate       # Linux/macOS
   venv\Scripts\activate.bat    # Windows
   ```

3. **Instale** as dependências:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   ou
      ```bash
   pip install --upgrade pip
   pip install Flask Werkzeug python-barcode Pillow requests python-dotenv Flask-Login
   ```

4. **Configure** variáveis de ambiente:
   - Use o script interativo:
     ```bash
     python change_telegram_token.py
     ```

5. **Atualize** os dados da instituição:
   ```bash
   python change_info_id.py
   ```

6. **Altere** logo e assinatura:
   ```bash
   python change_logo_sign_gui.py
   ```
   ou

   Substitua os arquivos "logo.svg" (tamanho 156x56) e "assinatura.png" (600x400) com os respectivos da Escola.

7. **Crie** usuários de acesso:
   ```bash
   python user_creator.py
   ```
   - Usuário e senha padrão: admin/admin
---

## 🚀 Uso

1. **Inicie** o servidor:
   ```bash
   python start_server.py
   ```

2. **Acesse** no navegador:
   ```
   http://localhost:5000 ou http://IP_DO_SERVIDOR:5000
   ```

3. **Faça login** e utilize as funcionalidades:
   - Gerenciar registros de entrada/saída
   - Consultar histórico
   - Gerar carteirinhas
   - Upload/edição de fotos
   - Monitorar carômetro
   - Receber notificações no Telegram

---

## 🤝 Contribuição

1. Faça um _fork_ do projeto.
2. Crie uma _branch_ para sua feature: `git checkout -b feature/nova-funcionalidade`.
3. Commit suas mudanças: `git commit -m 'Adiciona X'`.
4. Envie para o remoto: `git push origin feature/nova-funcionalidade`.
5. Abra um _Pull Request_ detalhando as alterações.

---

## 📄 Licença

Este projeto está sob a licença descrita em [LICENSE](LICENSE).
