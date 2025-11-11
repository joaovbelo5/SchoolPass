from flask import Flask, render_template, request, redirect, url_for
import csv
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import re

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
        # Construir o caminho para o arquivo de registro do aluno
        # Sanitiza o nome da turma para evitar barras ou caracteres inválidos em paths
        def sanitize_turma(name: str, replacement: str = '_') -> str:
            if not isinstance(name, str):
                return ''
            return re.sub(r'[^A-Za-z0-9]', replacement, name)

        turma_safe = sanitize_turma(turma)
        arquivo_path = os.path.join('registros', turma_safe, f"{codigo}.txt")
        print(f"Tentando ler arquivo: {arquivo_path}")
        
        if os.path.exists(arquivo_path):
            print(f"Arquivo encontrado: {arquivo_path}")
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                print(f"Conteúdo lido: {len(conteudo)} caracteres")
                return conteudo
        else:
            print(f"Arquivo não encontrado: {arquivo_path}")
        return ""
    except Exception as e:
        print(f"Error getting registros: {str(e)}")
        return ""

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
            print(f"Registros obtidos: {registros[:100]}...")  # Mostra os primeiros 100 caracteres
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)
