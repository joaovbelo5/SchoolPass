from flask import flash

# --- Rotas administrativas para alterar configurações sensíveis ---
from werkzeug.utils import secure_filename

def register_admin_routes(app):
    from flask import flash, render_template, request
    from flask_login import login_required
    import os
    @app.route('/admin', methods=['GET', 'POST'])
    @login_required
    def admin_index():
        from dotenv import set_key
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        # Processar formulários de configuração, logo/assinatura e token
        if request.method == 'POST':
            # Configurações da carteirinha
            for key in ['CARTEIRINHA_ESCOLA', 'CARTEIRINHA_TELEFONE', 'CARTEIRINHA_ENDERECO', 'CARTEIRINHA_VALIDADE']:
                if request.form.get(key):
                    set_key(env_path, key, request.form[key])
                    flash('Informações da carteirinha atualizadas!', 'success')
            # Token do Telegram
            if request.form.get('TELEGRAM_TOKEN'):
                set_key(env_path, 'TELEGRAM_TOKEN', request.form['TELEGRAM_TOKEN'])
                flash('Token do Telegram atualizado!', 'success')
            # Logo e assinatura
            assinatura = request.files.get('assinatura')
            if assinatura and assinatura.filename.lower().endswith('.png'):
                assinatura_path = os.path.join('static', 'assinatura.png')
                assinatura.save(assinatura_path)
                set_key(env_path, 'CARTEIRINHA_ASSINATURA', 'assinatura.png')
                flash('Assinatura atualizada!', 'success')
            logo = request.files.get('logo')
            if logo and logo.filename.lower().endswith('.svg'):
                logo_path = os.path.join('static', 'logo.svg')
                logo.save(logo_path)
                set_key(env_path, 'CARTEIRINHA_LOGO', 'logo.svg')
                flash('Logo atualizada!', 'success')
        config = {
            'escola': os.getenv('CARTEIRINHA_ESCOLA', ''),
            'telefone': os.getenv('CARTEIRINHA_TELEFONE', ''),
            'endereco': os.getenv('CARTEIRINHA_ENDERECO', ''),
            'validade': os.getenv('CARTEIRINHA_VALIDADE', '')
        }
        token = os.getenv('TELEGRAM_TOKEN', '')
        return render_template('admin_index.html', config=config, token=token)


from flask import Flask, render_template, request, redirect, url_for, send_from_directory, g
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import csv
import os
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from collections import defaultdict
from datetime import datetime, timedelta
import requests
import barcode
from barcode.codex import Code128
from barcode.writer import ImageWriter
import logging
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()




app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/fotos'
app.config['STATIC_FOLDER'] = 'static'
app.config['DATABASE'] = 'database.csv'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')
app.config['TELEGRAM_TOKEN'] = os.getenv('TELEGRAM_TOKEN', 'SEU_TOKEN_AQUI')
app.config['TELEGRAM_API_URL'] = f'https://api.telegram.org/bot{app.config["TELEGRAM_TOKEN"]}/sendMessage'
app.config['COOLDOWN_MINUTES'] = int(os.getenv('COOLDOWN_MINUTES', 5))

# Configurações da instituição para carteirinhas
CONFIG = {
    'escola': os.getenv('CARTEIRINHA_ESCOLA', 'CE NOVO FUTURO'),
    'telefone': os.getenv('CARTEIRINHA_TELEFONE', '61 91234-5678'),
    'endereco': os.getenv('CARTEIRINHA_ENDERECO', 'Rua dos Bobos, nº 0'),
    'validade': os.getenv('CARTEIRINHA_VALIDADE', '31/12/2025'),
    'assinatura': os.getenv('CARTEIRINHA_ASSINATURA', 'assinatura.png'),
    'logo': os.getenv('CARTEIRINHA_LOGO', 'logo.svg')
}

# Registrar rotas administrativas após definição do app
register_admin_routes(app)

# Configurações do código de barras
BARCODE_SETTINGS = {
    'module_width': 0.3,
    'module_height': 15,
    'font_size': 12,
    'text_distance': 1,
    'quiet_zone': 5
}

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Variáveis globais para registro de acessos
TURNOS = ['Manhã', 'Tarde', 'Noite']
contadores = defaultdict(int)
registros_diarios = []
ultimo_registro = {}
alunos_registrados_hoje = set()  # Alunos registrados no dia atual

# Funções auxiliares
def reset_contadores():
    """Reseta os contadores à meia-noite e salva os registros do dia anterior."""
    global contadores, registros_diarios, alunos_registrados_hoje
    contadores.clear()
    alunos_registrados_hoje.clear()  # Limpa os alunos registrados no dia atual
    if registros_diarios:
        data = datetime.now().strftime("%Y-%m-%d")
        pasta_registros = 'registros_diarios'
        os.makedirs(pasta_registros, exist_ok=True)
        
        arquivo = os.path.join(pasta_registros, f"{data}.csv")
        with open(arquivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['codigo', 'turno', 'data/hora', 'tipo'])
            writer.writeheader()
            for registro in registros_diarios:
                writer.writerow({
                    'codigo': registro['codigo'],
                    'turno': registro['turno'],
                    'data/hora': f"{datetime.now().strftime('%Y-%m-%d')} {registro['hora']}",
                    'tipo': registro['tipo']
                })
    registros_diarios.clear()

def salvar_registro_diario(registro):
    """Salva o registro no arquivo CSV do dia atual."""
    data = datetime.now().strftime("%Y-%m-%d")
    pasta_registros = 'registros_diarios'
    os.makedirs(pasta_registros, exist_ok=True)
    
    arquivo = os.path.join(pasta_registros, f"{data}.csv")
    arquivo_existe = os.path.exists(arquivo)
    
    with open(arquivo, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['codigo', 'turno', 'data/hora', 'tipo'])
        if not arquivo_existe:
            writer.writeheader()
        writer.writerow({
            'codigo': registro['codigo'],
            'turno': registro['turno'],
            'data/hora': f"{datetime.now().strftime('%Y-%m-%d')} {registro['hora']}",
            'tipo': registro['tipo']
        })

def buscar_aluno(codigo):
    """Busca um aluno no arquivo database.csv pelo código."""
    try:
        with open(app.config['DATABASE'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Codigo'] == codigo.strip():
                    return row
    except FileNotFoundError:
        logger.error("Arquivo database.csv não encontrado.")
    return None

def buscar_turma(turma):
    """Busca todos os alunos de uma turma no arquivo database.csv."""
    try:
        alunos = []
        with open(app.config['DATABASE'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Turma'].lower() == turma.lower():
                    alunos.append(row)
        return alunos
    except Exception as e:
        logger.error(f"Erro ao buscar turma: {str(e)}")
        return []

def registrar_acesso(codigo, nome, turma, tipo_acesso):
    """Registra o acesso no arquivo TXT."""
    global alunos_registrados_hoje
    now = datetime.now()
    data_atual = now.strftime("%Y-%m-%d")

    # Verifica se o aluno já foi registrado hoje
    if (codigo, data_atual) in alunos_registrados_hoje:
        return  # Não registra novamente

    alunos_registrados_hoje.add((codigo, data_atual))  # Marca o aluno como registrado hoje

    data_hora = now.strftime("%d/%m/%Y %H:%M:%S")
    registro = f"{data_hora} - {tipo_acesso}"
    
    pasta_turma = os.path.join('registros', turma)
    os.makedirs(pasta_turma, exist_ok=True)
        
    arquivo_path = os.path.join(pasta_turma, f"{codigo}.txt")
    arquivo_existe = os.path.exists(arquivo_path)
    
    with open(arquivo_path, 'a', encoding='utf-8') as f:
        if not arquivo_existe:
            aluno = buscar_aluno(codigo)
            f.write(f"Nome: {nome}\n")
            f.write(f"Turma: {turma}\n")
            f.write(f"Turno: {aluno['Turno']}\n")
            f.write(f"Código: {codigo}\n")
            f.write("\nREGISTRO DE ACESSOS:\n")
            f.write("-" * 30 + "\n")
        f.write(f"{registro}\n")
    
    aluno = buscar_aluno(codigo)
    if aluno:
        contadores[aluno['Turno']] += 1
        registro_diario = {
            'hora': now.strftime("%H:%M:%S"),
            'codigo': codigo,
            'turno': aluno['Turno'],
            'tipo': tipo_acesso
        }
        registros_diarios.append(registro_diario)
        salvar_registro_diario(registro_diario)

def enviar_telegram(chat_id, nome, tipo_acesso):
    """Envia mensagem ao Telegram indicando entrada ou saída."""
    import threading
    mensagem = f"O aluno {nome} passou a carteirinha às {datetime.now().strftime('%H:%M')}"
    params = {'chat_id': chat_id, 'text': mensagem}
    def send_async():
        try:
            response = requests.post(app.config['TELEGRAM_API_URL'], params=params, timeout=2)
            response.raise_for_status()
            logger.info(f"Mensagem enviada com sucesso: {response.json()}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar para Telegram: {e}")
    threading.Thread(target=send_async, daemon=True).start()

def verificar_usuario(username, password):
    """Verifica as credenciais do usuário no arquivo usuarios.csv."""
    with open('usuarios.csv', 'r') as f:
        reader = csv.DictReader(f)
        for user in reader:
            if user['username'] == username:
                if check_password_hash(user['password_hash'], password):
                    return True
    return False

def allowed_file(filename):
    """Verifica se o arquivo tem uma extensão permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def read_database():
    """Lê o arquivo database.csv e retorna a lista de alunos."""
    with open(app.config['DATABASE'], 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def write_database(data):
    """Escreve os dados no arquivo database.csv."""
    with open(app.config['DATABASE'], 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def gerar_codigo_barras(codigo):
    """Gera um código de barras para o aluno."""
    try:
        codigo_formatado = codigo.zfill(9)
        caminho_barcode = os.path.join(app.config['STATIC_FOLDER'], 'barcodes')
        os.makedirs(caminho_barcode, exist_ok=True)
        
        arquivo_final = os.path.join(caminho_barcode, f"{codigo_formatado}.png")
        
        if not os.path.exists(arquivo_final):
            code128 = Code128(codigo_formatado, writer=ImageWriter())
            code128.save(os.path.join(caminho_barcode, codigo_formatado), BARCODE_SETTINGS)
        
        return arquivo_final
    except Exception as e:
        logger.error(f"Erro na geração do código de barras: {str(e)}")
        return None

# Rotas de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if verificar_usuario(username, password):
            user = User(username)
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        return render_template('login.html', error="Credenciais inválidas!")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Rotas de registro de acesso
@app.route('/', methods=['GET', 'POST'])
def index():
    mensagem = ""
    aluno = None
    alerta = False
    erro = False

    if request.method == 'POST':
        codigo = request.form.get('codigo', '')
        aluno = buscar_aluno(codigo)
        
        if aluno:
            if aluno['Permissao'].lower() == 'sim':
                now = datetime.now()
                ultimo = ultimo_registro.get(codigo)
                if ultimo and (now - ultimo['hora']) < timedelta(minutes=app.config['COOLDOWN_MINUTES']):
                    mensagem = "⏳ Aguarde antes de registrar novamente."
                else:
                    registrar_acesso(aluno['Codigo'], aluno['Nome'], aluno['Turma'], "Acesso")
                    if aluno['TelegramID']:
                        enviar_telegram(aluno['TelegramID'], aluno['Nome'], "Acesso")
                    ultimo_registro[codigo] = {'hora': now}
                    mensagem = "✅ Acesso Registrado com Sucesso!"
            else:
                alerta = True
                mensagem = "⛔ Acesso Negado!"
        else:
            erro = True
            mensagem = "⚠️ Código não encontrado!"

    return render_template('index.html', 
                          mensagem=mensagem, 
                          aluno=aluno, 
                          alerta=alerta, 
                          erro=erro)

@app.route('/consulta', methods=['GET', 'POST'])
@login_required
def consulta():
    resultados = []
    termo = ''
    mensagem = ''
    alerta = False
    erro = False

    if request.method == 'POST':
        if 'termo' in request.form:
            termo = request.form.get('termo', '').lower()
            with open(app.config['DATABASE'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                resultados = [row for row in reader if (
                    termo in row['Nome'].lower() or
                    termo == row['Codigo'] or
                    termo in row['Turma'].lower()
                )]
        elif 'registrar_codigo' in request.form:
            codigo = request.form.get('registrar_codigo', '').strip()
            aluno = buscar_aluno(codigo)
            if aluno:
                if aluno['Permissao'].lower() == 'sim':
                    now = datetime.now()
                    ultimo = ultimo_registro.get(codigo)
                    if ultimo and (now - ultimo['hora']) < timedelta(minutes=app.config['COOLDOWN_MINUTES']):
                        mensagem = "⏳ Aguarde antes de registrar novamente."
                    else:
                        registrar_acesso(aluno['Codigo'], aluno['Nome'], aluno['Turma'], "Acesso")
                        if aluno['TelegramID']:
                            enviar_telegram(aluno['TelegramID'], aluno['Nome'], "Acesso")
                        ultimo_registro[codigo] = {'hora': now}
                        mensagem = "✅ Acesso Registrado com Sucesso!"
                else:
                    alerta = True
                    mensagem = "⛔ Acesso Negado!"
            else:
                erro = True
                mensagem = "⚠️ Código não encontrado!"

    return render_template('consulta.html', 
                           resultados=resultados, 
                           termo=termo, 
                           mensagem=mensagem, 
                           alerta=alerta, 
                           erro=erro)

@app.route('/get_contadores')
def get_contadores():
    now = datetime.now()
    if now.hour == 0 and now.minute == 0:
        reset_contadores()
    return {'contadores': dict(contadores), 'total': sum(contadores.values())}

# Rotas de cadastro (protegidas)
@app.route('/cadastro')
@login_required
def cadastro():
    alunos = read_database()
    return render_template('upload_index.html', alunos=alunos)

@app.route('/cadastro/editar/<codigo>', methods=['GET', 'POST'])
@login_required
def editar(codigo):
    alunos = read_database()
    aluno = next((a for a in alunos if a['Codigo'] == codigo), None)
    
    if request.method == 'POST':
        aluno['Nome'] = request.form['nome']
        aluno['Turma'] = request.form['turma']
        aluno['Turno'] = request.form['turno']
        aluno['Permissao'] = request.form['permissao']
        aluno['TelegramID'] = request.form['telegramid']
        
        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                aluno['Foto'] = filename
        
        write_database(alunos)
        return redirect(url_for('cadastro'))
    
    return render_template('upload_editar.html', aluno=aluno)

@app.route('/cadastro/excluir/<codigo>')
@login_required
def excluir(codigo):
    alunos = read_database()
    alunos = [a for a in alunos if a['Codigo'] != codigo]
    write_database(alunos)
    return redirect(url_for('cadastro'))

@app.route('/cadastro/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        novo_aluno = {
            'Nome': request.form['nome'],
            'Codigo': request.form['codigo'],
            'Turma': request.form['turma'],
            'Turno': request.form['turno'],
            'Permissao': request.form['permissao'],
            'Foto': 'semfoto.jpg',
            'TelegramID': request.form['telegramid']
        }
        
        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                novo_aluno['Foto'] = filename
        
        alunos = read_database()
        alunos.append(novo_aluno)
        write_database(alunos)
        return redirect(url_for('cadastro'))
    
    return render_template('upload_novo.html')

# Rotas de emissão de carteirinhas (protegidas)
@app.route('/emissao')
@login_required
def emissao():
    try:
        turmas = set()
        with open(app.config['DATABASE'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                turmas.add(row['Turma'])
        return render_template('carteirinha_index.html', 
                              turmas=sorted(turmas), 
                              config=CONFIG)
    except Exception as e:
        return render_template('erro.html', 
                              mensagem=f"Erro ao carregar dados: {str(e)}")

@app.route('/emitir', methods=['POST'])
@login_required
def emitir():
    try:
        # Recarregar variáveis do .env em tempo real
        from dotenv import load_dotenv
        load_dotenv(override=True)
        tipo_emissao = request.form.get('tipo_emissao')
        data_emissao = datetime.now().strftime("%d/%m/%Y")
        
        if not tipo_emissao:
            return render_template('erro.html', mensagem="Tipo de emissão não especificado!")

        if tipo_emissao == 'unitaria':
            codigo = request.form.get('codigo', '').strip()
            if not codigo:
                return render_template('erro.html', mensagem="Código não informado!")
            
            aluno = buscar_aluno(codigo)
            if not aluno:
                return render_template('erro.html', mensagem=f"Código {codigo} não encontrado!")
            
            barcode_path = gerar_codigo_barras(aluno['Codigo'])
            if not barcode_path:
                return render_template('erro.html', mensagem="Erro ao gerar código de barras!")
            
            aluno.update({
                'barcode': os.path.basename(barcode_path),
                'data_emissao': data_emissao,
                **CONFIG,
                'CARTEIRINHA_ESCOLA': os.getenv('CARTEIRINHA_ESCOLA', ''),
                'CARTEIRINHA_TELEFONE': os.getenv('CARTEIRINHA_TELEFONE', ''),
                'CARTEIRINHA_ENDERECO': os.getenv('CARTEIRINHA_ENDERECO', ''),
                'CARTEIRINHA_VALIDADE': os.getenv('CARTEIRINHA_VALIDADE', ''),
            })
            return render_template('carteirinha_template.html', alunos=[aluno])

        elif tipo_emissao == 'turma':
            turma = request.form.get('turma', '').strip()
            if not turma:
                return render_template('erro.html', mensagem="Turma não informada!")

            alunos = buscar_turma(turma)
            if not alunos:
                return render_template('erro.html', mensagem=f"Turma {turma} não encontrada!")

            # Filtrar apenas alunos com foto se checkbox estiver marcado
            apenas_com_foto = request.form.get('apenas_com_foto')
            if apenas_com_foto:
                alunos = [a for a in alunos if a.get('Foto') and a['Foto'].strip() and a['Foto'].lower() != 'semfoto.jpg']

            for aluno in alunos:
                barcode_path = gerar_codigo_barras(aluno['Codigo'])
                aluno.update({
                    'barcode': os.path.basename(barcode_path) if barcode_path else '',
                    'data_emissao': data_emissao,
                    **CONFIG,
                    'CARTEIRINHA_ESCOLA': os.getenv('CARTEIRINHA_ESCOLA', ''),
                    'CARTEIRINHA_TELEFONE': os.getenv('CARTEIRINHA_TELEFONE', ''),
                    'CARTEIRINHA_ENDERECO': os.getenv('CARTEIRINHA_ENDERECO', ''),
                    'CARTEIRINHA_VALIDADE': os.getenv('CARTEIRINHA_VALIDADE', ''),
                })

            return render_template('carteirinha_template.html', alunos=alunos)

        else:
            return render_template('erro.html', mensagem="Tipo de emissão inválido!")

    except Exception as e:
        logger.error(f"Erro crítico: {str(e)}")
        return render_template('erro.html', mensagem=f"Erro interno: {str(e)}")

@app.route('/registros/<path:filename>')
@login_required
def registros_files(filename):
    """Serve files from the 'registros' directory."""
    registros_dir = os.path.join('registros')
    return send_from_directory(registros_dir, filename)

@app.route('/historico', methods=['GET', 'POST'])
@login_required
def historico():
    pasta_registros = 'registros_diarios'
    arquivos = sorted(os.listdir(pasta_registros))  # Lista os arquivos na pasta
    registros = []
    data_selecionada = None

    # Carregar os dados do database.csv
    alunos = {}
    try:
        with open(app.config['DATABASE'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                alunos[row['Codigo']] = {'nome': row['Nome'], 'turma': row['Turma']}
    except FileNotFoundError:
        return render_template('erro.html', mensagem="Arquivo database.csv não encontrado!")

    if request.method == 'POST':
        data_selecionada = request.form.get('data')
        if data_selecionada:
            arquivo = os.path.join(pasta_registros, f"{data_selecionada}.csv")
            if os.path.exists(arquivo):
                with open(arquivo, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for registro in reader:
                        codigo = registro['codigo']
                        # Adicionar nome e turma ao registro, se disponíveis
                        if codigo in alunos:
                            registro['nome'] = alunos[codigo]['nome']
                            registro['turma'] = alunos[codigo]['turma']
                        else:
                            registro['nome'] = 'Desconhecido'
                            registro['turma'] = 'Desconhecida'
                        registros.append(registro)
            else:
                return render_template('erro.html', mensagem=f"Arquivo para a data {data_selecionada} não encontrado!")

    return render_template('historico.html', arquivos=arquivos, registros=registros, data_selecionada=data_selecionada)

@app.route('/pesquisar', methods=['GET'])
@login_required
def pesquisar():
    query = request.args.get('query', '').lower()
    resultados = []
    if query:
        with open(app.config['DATABASE'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            resultados = [row for row in reader if query in row['Nome'].lower() or query in row['Turma'].lower()]
    return render_template('upload_index.html', alunos=resultados)

@app.route('/carometro', methods=['GET', 'POST'])
@login_required
def carometro():
    alunos = read_database()
    turma_selecionada = None
    alunos_filtrados = []

    if request.method == 'POST':
        turma_selecionada = request.form.get('turma', '').strip()
        if turma_selecionada:
            alunos_filtrados = [aluno for aluno in alunos if aluno['Turma'].lower() == turma_selecionada.lower()]
        else:
            alunos_filtrados = alunos  # Mostra todos os alunos se nenhuma turma for selecionada
    else:
        alunos_filtrados = alunos  # Mostra todos os alunos por padrão

    turmas = sorted(set(aluno['Turma'] for aluno in alunos))  # Lista de turmas únicas
    return render_template('carometro.html', alunos=alunos_filtrados, turmas=turmas, turma_selecionada=turma_selecionada)

if __name__ == '__main__':
    os.makedirs(os.path.join(app.config['STATIC_FOLDER'], 'barcodes'), exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
