from flask import Flask, render_template, request, redirect, url_for
import csv
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

app = Flask(__name__)
app.config['DATABASE'] = 'database.csv'
app.config['STATIC_FOLDER'] = 'static'

def load_user_data(codigo, turma):
    try:
        # Usar a mesma função buscar_aluno do start_server.py
        with open(app.config['DATABASE'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for aluno in reader:
                if aluno['Codigo'] == codigo and aluno['Turma'].lower() == turma.lower():
                    return aluno
        return None
    except Exception as e:
        print(f"Error loading user data: {e}")
        return None

def get_registros(codigo, turma):
    try:
        # Construir o caminho para o arquivo de registro do aluno (JSON)
        arquivo_path = os.path.join('registros', turma, f"{codigo}.json")
        print(f"Tentando ler arquivo: {arquivo_path}")
        
        if os.path.exists(arquivo_path):
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data # Retorna o objeto completo do histórico
        else:
            print(f"Arquivo não encontrado: {arquivo_path}")
        return None
    except Exception as e:
        print(f"Error getting registros: {str(e)}")
        return None

@app.route('/termos')
def termos():
    import markdown
    
    def read_md(filename):
        path = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return markdown.markdown(f.read())
        return "<p>Conteúdo não disponível.</p>"

    terms_html = read_md('terms_of_service.md')
    privacy_html = read_md('privacy_policy.md')
    
    return render_template('termos.html', terms_html=terms_html, privacy_html=privacy_html)

@app.route('/', methods=['GET', 'POST'])
def public_consulta():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        turma = request.form.get('turma')
        action = request.form.get('action')
        
        # Validate input
        if not codigo or not turma:
            return render_template('public_consulta.html', error="Por favor, preencha todos os campos.")
        
        # Check if user exists and data matches
        user_data = load_user_data(codigo, turma)
        if not user_data:
            return render_template('public_consulta.html', error="Código ou turma inválidos.")
        
        if action == 'registros':
            registros = get_registros(codigo, turma)
            print(f"Registros obtidos: {str(registros)[:100]}...")  # Mostra os primeiros 100 caracteres
            return render_template('public_consulta.html', 
                                user=user_data,
                                registros=registros,
                                aluno=user_data,
                                now=datetime.now())
        
        elif action == 'carteirinha':
            # Redirect to carteirinha template with properly capitalized field names
            aluno_data = dict(user_data)
            # Add carteirinha config data from .env
            aluno_data['CARTEIRINHA_ESCOLA'] = os.getenv('CARTEIRINHA_ESCOLA', 'CE NOVO FUTURO')
            aluno_data['CARTEIRINHA_TELEFONE'] = os.getenv('CARTEIRINHA_TELEFONE', '61 91234-5678')
            aluno_data['CARTEIRINHA_ENDERECO'] = os.getenv('CARTEIRINHA_ENDERECO', 'Rua dos Bobos, nº 0')
            aluno_data['CARTEIRINHA_VALIDADE'] = os.getenv('CARTEIRINHA_VALIDADE', '31/12/2025')
            aluno_data['data_emissao'] = datetime.now().strftime('%d/%m/%Y')
            return render_template('carteirinha_template.html', alunos=[aluno_data])
    
    return render_template('public_consulta.html')


# Nova rota para cadastro de TelegramID
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro_telegram():
    if request.method == 'POST':
        codigo = request.form.get('codigo')
        turma = request.form.get('turma')
        nome = request.form.get('nome')
        telegram_id = request.form.get('telegram_id')

        # Validação básica
        if not codigo or not turma or not nome or not telegram_id:
            return render_template('cadastro_telegram.html', error="Por favor, preencha todos os campos.")

        # Autenticação igual à consulta
        user_data = load_user_data(codigo, turma)
        if not user_data:
            return render_template('cadastro_telegram.html', error="Código ou turma inválidos.")
        # Conferir nome do aluno (case-insensitive, ignora espaços extras)
        if user_data['Nome'].strip().lower() != nome.strip().lower():
            return render_template('cadastro_telegram.html', error="Nome do aluno não confere com a carteirinha.")

        # Atualizar o database.csv
        updated = False
        database_path = app.config['DATABASE']
        alunos = []
        with open(database_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row['Codigo'] == codigo and row['Turma'].lower() == turma.lower():
                    row['TelegramID'] = telegram_id
                    updated = True
                alunos.append(row)

        if not updated:
            return render_template('cadastro_telegram.html', error="Não foi possível atualizar o ID do Telegram.")

        # Escrever de volta no CSV
        with open(database_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(alunos)

        return render_template('cadastro_telegram.html', success="ID do Telegram cadastrado com sucesso!")

    return render_template('cadastro_telegram.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=False)
