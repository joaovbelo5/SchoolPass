from flask import flash

# --- Rotas administrativas para alterar configurações sensíveis ---
from werkzeug.utils import secure_filename

def register_admin_routes(app):
    from flask import flash, render_template, request, session, jsonify
    from flask_login import login_required
    import os, time

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

        # Gerar token e operação matemática para tripla verificação (serão exibidos no template)
        try:
            clear_token = str(random.randint(100000, 999999))
            a = random.randint(2, 20)
            b = random.randint(2, 20)
            op = random.choice(['+', '-', '*'])
            if op == '+':
                answer = a + b
            elif op == '-':
                if a < b:
                    a, b = b, a
                answer = a - b
            else:
                answer = a * b
            math_question = f"Quanto é {a} {op} {b}?"
            session['clear_token'] = clear_token
            session['clear_answer'] = str(answer)
            session['clear_token_time'] = int(time.time())
        except Exception:
            clear_token = ''
            math_question = ''

        return render_template('admin_index.html', config=config, token=token, clear_token=clear_token, math_question=math_question)

    @app.route('/admin/clear_data', methods=['POST'])
    @login_required
    def admin_clear_data():
        """Executa a limpeza dos dados após validação tripla: token, resposta matemática e frase fixa."""
        try:
            data = request.get_json() or request.form
            token_recv = str(data.get('token', '')).strip()
            math_recv = str(data.get('math', '')).strip()
            phrase_recv = str(data.get('phrase', '')).strip()

            # Validar tempo do token (10 minutos)
            token_time = session.get('clear_token_time')
            if token_time and (int(time.time()) - int(token_time) > 600):
                return jsonify({'ok': False, 'msg': 'Token expirado.'}), 400

            if token_recv != session.get('clear_token') or math_recv != session.get('clear_answer') or phrase_recv.upper() != 'LIMPAR TUDO':
                return jsonify({'ok': False, 'msg': 'Falha na verificação. Dados não removidos.'}), 400

            # Caminhos a serem limpos
            base_dir = os.path.dirname(__file__)
            db_path = os.path.join(base_dir, app.config.get('DATABASE', 'database.csv'))

            def clear_db_keep_header(path):
                try:
                    if os.path.exists(path):
                        with open(path, 'r', encoding='utf-8') as f:
                            first = f.readline()
                        with open(path, 'w', encoding='utf-8', newline='') as f:
                            if first:
                                f.write(first)
                    else:
                        with open(path, 'w', encoding='utf-8') as f:
                            pass
                except Exception as e:
                    logger.error(f"Erro ao limpar database: {e}")

            def clear_dir_contents(path):
                try:
                    if not os.path.exists(path):
                        return
                    for entry in os.listdir(path):
                        full = os.path.join(path, entry)
                        try:
                            if os.path.isfile(full) or os.path.islink(full):
                                os.remove(full)
                            elif os.path.isdir(full):
                                shutil.rmtree(full)
                        except Exception as e:
                            logger.error(f"Erro removendo {full}: {e}")
                except Exception as e:
                    logger.error(f"Erro ao limpar diretório {path}: {e}")

            # Executar limpeza
            clear_db_keep_header(db_path)

            dirs_to_clear = [
                os.path.join(base_dir, 'chamadas'),
                os.path.join(base_dir, 'ocorrencias'),
                os.path.join(base_dir, 'registros'),
                os.path.join(base_dir, 'static', 'barcodes'),
                os.path.join(base_dir, 'static', 'fotos')
            ]

            for d in dirs_to_clear:
                clear_dir_contents(d)

            session.pop('clear_token', None)
            session.pop('clear_answer', None)
            session.pop('clear_token_time', None)

            logger.info('Limpeza de dados concluída pelo administrador.')
            return jsonify({'ok': True, 'msg': 'Limpeza concluída.'})
        except Exception as e:
            logger.exception('Erro durante limpeza de dados')
            return jsonify({'ok': False, 'msg': f'Erro: {e}'}), 500

    @app.route('/admin/backup', methods=['GET'])
    @login_required
    def admin_backup():
        """Cria um arquivo ZIP no disco (pasta backups/) e envia para download. Mantém backups por 3 horas."""
        try:
            import zipfile
            from datetime import datetime
            from flask import send_file
            from flask_login import current_user

            base_dir = os.path.dirname(__file__)
            backups_dir = os.path.join(base_dir, 'backups')
            os.makedirs(backups_dir, exist_ok=True)

            # limpar backups antigos (mais de 3 horas)
            now = time.time()
            try:
                for fn in os.listdir(backups_dir):
                    fp = os.path.join(backups_dir, fn)
                    try:
                        if os.path.isfile(fp) and (now - os.path.getmtime(fp) > 3 * 3600):
                            os.remove(fp)
                    except Exception as e:
                        logger.error(f"Erro removendo backup antigo {fp}: {e}")
            except FileNotFoundError:
                pass

            files_and_dirs = [
                os.path.join(base_dir, app.config.get('DATABASE', 'database.csv')),
                os.path.join(base_dir, 'chamadas'),
                os.path.join(base_dir, 'ocorrencias'),
                os.path.join(base_dir, 'registros'),
                os.path.join(base_dir, 'static', 'barcodes'),
                os.path.join(base_dir, 'static', 'fotos'),
                os.path.join(base_dir, 'static', 'assinatura.png'),
                os.path.join(base_dir, 'static', 'logo.svg'),
                os.path.join(base_dir, '.env')
            ]

            filename = f"backup_schoolpass_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}.zip"
            dest_path = os.path.join(backups_dir, filename)

            # Criar o zip diretamente no disco para suportar grandes volumes
            with zipfile.ZipFile(dest_path, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
                for path in files_and_dirs:
                    if os.path.isfile(path):
                        arcname = os.path.relpath(path, base_dir)
                        try:
                            zf.write(path, arcname)
                        except Exception as e:
                            logger.error(f"Erro ao adicionar arquivo {path} ao zip: {e}")
                    elif os.path.isdir(path):
                        for root, dirs, files in os.walk(path):
                            for f in files:
                                full = os.path.join(root, f)
                                arcname = os.path.relpath(full, base_dir)
                                try:
                                    zf.write(full, arcname)
                                except Exception as e:
                                    logger.error(f"Erro ao adicionar {full} ao zip: {e}")

            # Registrar quem criou o backup (se disponível)
            try:
                user_id = getattr(current_user, 'id', None)
                logger.info(f"Backup criado por {user_id}: {dest_path}")
            except Exception:
                logger.info(f"Backup criado: {dest_path}")

            # Enviar o arquivo para download sem deletar (será limpo por critério de 3 horas)
            return send_file(dest_path, mimetype='application/zip', as_attachment=True, download_name=filename)
        except Exception as e:
            logger.exception('Erro ao criar backup')
            return jsonify({'ok': False, 'msg': f'Erro ao criar backup: {e}'}), 500

    @app.route('/admin/restore', methods=['POST'])
    @login_required
    def admin_restore():
        """Restaura um backup enviado (arquivo ZIP). O upload deve ser o ZIP gerado pelo sistema.
        A requisição deve enviar o arquivo em campo 'backup_file' e a frase de confirmação 'RESTAURAR BACKUP'.
        Processo:
        - salva o upload em diretório temporário
        - extrai o ZIP em um diretório temporário
        - para cada alvo extraído, substitui/reescreve o destino apropriado no projeto
        - limpa temporários e retorna resultado
        """
        try:
            # receber arquivo
            uploaded = request.files.get('backup_file')
            phrase = request.form.get('phrase', '').strip()
            if not uploaded:
                return jsonify({'ok': False, 'msg': 'Nenhum arquivo enviado.'}), 400
            if phrase.upper() != 'RESTAURAR BACKUP':
                return jsonify({'ok': False, 'msg': 'Frase de confirmação incorreta.'}), 400

            import tempfile
            import zipfile

            base_dir = os.path.dirname(__file__)
            tmpdir = tempfile.mkdtemp(prefix='restore_')
            tmpzip = os.path.join(tmpdir, 'upload.zip')
            uploaded.save(tmpzip)

            extract_dir = os.path.join(tmpdir, 'extracted')
            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(tmpzip, 'r') as zf:
                zf.extractall(extract_dir)

            # utilitários
            def try_copy_file(relpath):
                src = os.path.join(extract_dir, relpath)
                dst = os.path.join(base_dir, relpath)
                if os.path.exists(src):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    try:
                        shutil.copy2(src, dst)
                        logger.info(f"Arquivo restaurado: {dst}")
                    except Exception as e:
                        logger.error(f"Erro copiando {src} -> {dst}: {e}")

            def try_replace_dir(relpath):
                src = os.path.join(extract_dir, relpath)
                dst = os.path.join(base_dir, relpath)
                if os.path.exists(src):
                    # remove destino atual se existir
                    if os.path.exists(dst):
                        try:
                            shutil.rmtree(dst)
                        except Exception as e:
                            logger.error(f"Erro removendo destino {dst}: {e}")
                    try:
                        # mover pasta extraída para o local destino
                        shutil.move(src, dst)
                        logger.info(f"Pasta restaurada: {dst}")
                    except Exception as e:
                        logger.error(f"Erro movendo {src} -> {dst}: {e}")

            # Alvos a serem restaurados (mesma lista do backup)
            targets_dirs = [
                'chamadas', 'ocorrencias', 'registros',
                os.path.join('static', 'barcodes'), os.path.join('static', 'fotos')
            ]
            targets_files = [
                'database.csv', os.path.join('static', 'assinatura.png'), os.path.join('static', 'logo.svg'), '.env'
            ]

            # Diretórios: substituir
            for td in targets_dirs:
                try_replace_dir(td)

            # Arquivos: copiar sobrepondo
            for tf in targets_files:
                try_copy_file(tf)

            # cleanup temporário
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                pass

            logger.info('Restauração de backup concluída pelo administrador.')
            return jsonify({'ok': True, 'msg': 'Restauração concluída.'})
        except Exception as e:
            logger.exception('Erro durante restauração de backup')
            return jsonify({'ok': False, 'msg': f'Erro: {e}'}), 500


from flask import Flask, render_template, request, redirect, url_for, send_from_directory, g
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import csv
import os
import time
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
import shutil
import random
import threading

# Carregar variáveis do .env
load_dotenv()

# Configurar o locale para português do Brasil para formatação de data
import locale
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    print("Locale pt_BR.UTF-8 não encontrado, usando o locale padrão.")


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
    'font_size': 10,
    'text_distance': 5,
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
registros_diarios = []  # Buffer em memória para registros do dia (será salvo em JSON)
ultimo_registro = {}
alunos_registrados_hoje = set()  # Alunos registrados no dia atual
last_reset_date = datetime.now().strftime('%Y-%m-%d')
reset_lock = threading.Lock()


def salvar_registro_diario_json(registro):
    """Salva registro no arquivo JSON do dia atual."""
    data = datetime.now().strftime("%Y-%m-%d")
    pasta_registros = 'registros_diarios'
    os.makedirs(pasta_registros, exist_ok=True)
    
    arquivo = os.path.join(pasta_registros, f"{data}.json")
    
    registros = []
    if os.path.exists(arquivo):
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                registros = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao ler {arquivo}: {e}")
    
    registros.append(registro)
    
    try:
        with open(arquivo, 'w', encoding='utf-8', newline='') as f:
            json.dump(registros, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar {arquivo}: {e}")


def _midnight_scheduler_loop():
    """Loop de background que aguarda até a próxima meia-noite e reseta os contadores."""
    while True:
        now = datetime.now()
        # calcular próxima meia-noite (início do próximo dia)
        next_midnight = datetime(now.year, now.month, now.day) + timedelta(days=1)
        seconds = (next_midnight - now).total_seconds()
        try:
            # dormir até a meia-noite
            time.sleep(seconds)
        except Exception:
            # em caso de interrupção, recomputar loop
            continue
        try:
            with reset_lock:
                # Salvar registros do dia anterior em JSON
                if registros_diarios:
                    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    pasta_registros = 'registros_diarios'
                    os.makedirs(pasta_registros, exist_ok=True)
                    arquivo = os.path.join(pasta_registros, f"{yesterday}.json")
                    try:
                        with open(arquivo, 'w', encoding='utf-8') as f:
                            json.dump(registros_diarios, f, ensure_ascii=False, indent=2)
                        logger.info(f"Registros do dia {yesterday} salvos em JSON")
                    except Exception as e:
                        logger.exception(f"Erro ao salvar registros JSON: {e}")
                
                reset_contadores()
                global last_reset_date
                last_reset_date = datetime.now().strftime('%Y-%m-%d')
                logger.info('Reset de contadores executado pelo agendador de meia-noite')
        except Exception as e:
            logger.exception(f'Erro no agendador de meia-noite: {e}')


try:
    # Inicia thread daemon que executa reset pontual à meia-noite
    t = threading.Thread(target=_midnight_scheduler_loop, daemon=True)
    t.start()
except Exception as e:
    logger.exception(f'Falha ao iniciar agendador de meia-noite: {e}')




# Funções auxiliares
def reset_contadores():
    """Reseta os contadores, limpa marcadores e buffer de registros diários."""
    global contadores, alunos_registrados_hoje, registros_diarios
    contadores.clear()
    alunos_registrados_hoje.clear()
    registros_diarios.clear()


def ensure_current_day():
    """Garante que os contadores pertencem ao dia corrente.

    Se detectarmos que a data mudou desde `last_reset_date`, executamos
    `reset_contadores()` (passando a data anterior para compatibilidade) e
    atualizamos `last_reset_date`.
    """
    global last_reset_date
    today = datetime.now().strftime('%Y-%m-%d')
    if today == last_reset_date:
        return
    # Protege contra chamadas concorrentes
    with reset_lock:
        # Re-checar dentro do lock
        if today == last_reset_date:
            return
        # salvar registros do dia anterior não é necessário aqui porque
        # `salvar_registro_diario()` grava por registro. Mantemos a API
        # chamando reset_contadores passando a data anterior por compatibilidade.
        try:
            reset_contadores()
            last_reset_date = today
            logger.info(f"Contadores resetados para o novo dia: {today}")
        except Exception as e:
            logger.exception(f"Erro ao resetar contadores na mudança de dia: {e}")

# Nota: removido o buffer `registros_diarios` e os arquivos diários. O histórico
# por arquivo diário foi descontinuado; preservamos apenas os logs individuais
# nos arquivos de cada aluno em `registros/`.

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
    # Garantir que estamos no dia correto antes de registrar (reset se necessário)
    try:
        ensure_current_day()
    except Exception:
        # não bloquear o registro em caso de erro no mecanismo de reset
        logger.exception('Erro em ensure_current_day')
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
        registrar_chamada(aluno)
        contadores[aluno['Turno']] += 1
        
        # Salvar no JSON diário
        registro_json = {
            'codigo': codigo,
            'nome': nome,
            'turma': turma,
            'turno': aluno['Turno'],
            'foto': aluno.get('Foto', 'semfoto.jpg'),
            'data_hora': data_hora,
            'tipo_acesso': tipo_acesso
        }
        salvar_registro_diario_json(registro_json)

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


def extract_validade_year():
    """Extrai o ano de validade configurado (ex: '31/12/2025' -> 2025).
    Retorna um inteiro com o ano. Se não for possível, retorna o ano atual."""
    try:
        validade = os.getenv('CARTEIRINHA_VALIDADE', CONFIG.get('validade', ''))
        if validade:
            # aceita formatos como DD/MM/YYYY ou YYYY-MM-DD
            if '/' in validade:
                parts = validade.split('/')
                year = int(parts[-1])
                return year
            elif '-' in validade:
                parts = validade.split('-')
                year = int(parts[0])
                return year
    except Exception:
        pass
    return datetime.now().year


def gerar_codigo_automatico(turma, turno, validade_ano=None):
    """Gera um código para a carteirinha seguindo a lógica requisitada:
    - 2 primeiros: ano de validade (ex: 2025 -> '25')
    - 3o dígito: turno (Manhã=1, Tarde=2, Noite=3)
    - 2 dígitos seguintes: código da turma (baseado na ordenação alfabética/numérica das turmas existentes)
    - últimos 4 dígitos: ordem do aluno na turma (contagem atual + 1) — garantido para totalizar 9 dígitos

    Retorna string do código (sem espaços)."""
    # ano
    if validade_ano is None:
        validade_ano = extract_validade_year()
    year_two = str(validade_ano)[-2:]

    # turno
    turno_map = {'manhã': '1', 'manha': '1', 'tarde': '2', 'noite': '3'}
    turno_digit = turno_map.get(turno.lower(), '0')

    # obter turmas ordenadas existentes para mapear código da turma
    alunos = read_database() if os.path.exists(app.config['DATABASE']) else []
    turmas = sorted(list({a['Turma'] for a in alunos if a.get('Turma')}))
    # se a turma não existir ainda na lista, adiciona ao final
    if turma not in turmas:
        turmas.append(turma)
    turma_index = turmas.index(turma) + 1
    turma_code = f"{turma_index:02d}"

    # ordem: contar alunos atuais na turma
    ordem = sum(1 for a in alunos if a.get('Turma', '').lower() == turma.lower()) + 1
    # usar 4 dígitos para a ordem para garantir 9 dígitos totais no código
    ordem_code = f"{ordem:04d}"

    codigo = f"{year_two}{turno_digit}{turma_code}{ordem_code}"
    return codigo


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
    # Garantir que os contadores reflitam o dia atual
    try:
        ensure_current_day()
    except Exception:
        logger.exception('Erro em ensure_current_day durante get_contadores')
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
        nome = request.form.get('nome', '').strip()
        turma = request.form.get('turma', '').strip()
        turno = request.form.get('turno', '').strip()
        permissao = request.form.get('permissao', '').strip()
        telegramid = request.form.get('telegramid', '').strip()
        codigo_fornecido = request.form.get('codigo', '').strip()

        # Lê alunos atuais
        alunos = read_database() if os.path.exists(app.config['DATABASE']) else []

        # Função auxiliar para verificar existência de código
        def codigo_existe(cod):
            return any(a for a in alunos if a.get('Codigo') == cod)

        # Se o usuário informou um código e ele não existe, usa-o.
        if codigo_fornecido and not codigo_existe(codigo_fornecido):
            codigo_final = codigo_fornecido
        else:
            # Caso contrário, gera automaticamente e garante unicidade
            validade_ano = extract_validade_year()
            tentativa = 0
            while True:
                tentativa += 1
                codigo_candidate = gerar_codigo_automatico(turma, turno, validade_ano)
                # Se por algum motivo já existir, incrementa ordem buscando próximo número disponível
                if not codigo_existe(codigo_candidate):
                    codigo_final = codigo_candidate
                    break
                else:
                    # Ajusta: incrementa o contador de alunos ficticiamente e tenta novamente
                    # Para evitar recalcular sempre o mesmo, aumentamos manualmente a ordem no final do código
                    # extrai os últimos 3 dígitos como número e incrementa
                    try:
                        # agora usamos 4 dígitos para a ordem (últimos 4 caracteres)
                        base = codigo_candidate[:-4]
                        num = int(codigo_candidate[-4:]) + 1
                        codigo_candidate = f"{base}{num:04d}"
                        if not codigo_existe(codigo_candidate):
                            codigo_final = codigo_candidate
                            break
                    except Exception:
                        # fallback: acrescenta o timestamp
                        codigo_final = codigo_candidate + str(tentativa)
                        break

        novo_aluno = {
            'Nome': nome,
            'Codigo': codigo_final,
            'Turma': turma,
            'Turno': turno,
            'Permissao': permissao,
            'Foto': 'semfoto.jpg',
            'TelegramID': telegramid
        }

        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                novo_aluno['Foto'] = filename

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

            apenas_com_foto = request.form.get('apenas_com_foto') == '1'
            alunos = buscar_turma(turma)
            if not alunos:
                return render_template('erro.html', mensagem=f"Turma {turma} não encontrada!")

            if apenas_com_foto:
                alunos = [aluno for aluno in alunos if aluno.get('Foto') and aluno['Foto'].lower() != 'semfoto.jpg']
                if not alunos:
                    return render_template('erro.html', mensagem="Nenhum aluno com foto nesta turma!")

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
    """Exibe histórico de acessos por data em formato JSON."""
    pasta_registros = 'registros_diarios'
    registros = []
    data_selecionada = None
    datas_disponiveis = []
    
    # Listar datas disponíveis
    if os.path.exists(pasta_registros):
        try:
            datas_disponiveis = sorted([
                f[:-5] for f in os.listdir(pasta_registros) 
                if f.endswith('.json')
            ], reverse=True)
        except FileNotFoundError:
            pass
    
    # Carregar dados do database para enriquecer informações
    alunos_db = {}
    try:
        with open(app.config['DATABASE'], 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                alunos_db[row['Codigo']] = row
    except FileNotFoundError:
        pass
    
    if request.method == 'POST':
        data_selecionada = request.form.get('data_selecionada')
        if data_selecionada:
            arquivo = os.path.join(pasta_registros, f"{data_selecionada}.json")
            if os.path.exists(arquivo):
                try:
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        registros = json.load(f)
                        # Enriquecer com dados do database se necessário
                        for reg in registros:
                            if reg['codigo'] in alunos_db:
                                reg.setdefault('foto', alunos_db[reg['codigo']].get('Foto', 'semfoto.jpg'))
                except Exception as e:
                    logger.error(f"Erro ao ler {arquivo}: {e}")
                    return render_template('erro.html', mensagem=f"Erro ao carregar registros: {str(e)}")
            else:
                return render_template('erro.html', mensagem=f"Nenhum registro encontrado para {data_selecionada}")
    
    return render_template('historico.html', 
                          datas_disponiveis=datas_disponiveis,
                          registros=registros, 
                          data_selecionada=data_selecionada)

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


import calendar

# --- ROTAS DE OCORRÊNCIAS ---
import json

@app.route('/chamada', methods=['GET', 'POST'])
@login_required
def chamada():
    # 1. Obter todas as turmas do `database.csv`
    turmas = sorted(list(set(aluno['Turma'] for aluno in read_database())))

    # 2. Determinar a turma e o mês selecionados
    if request.method == 'POST':
        turma_selecionada = request.form.get('turma')
        mes_ano_str = request.form.get('mes') # Formato: YYYY-MM
    else:
        turma_selecionada = turmas[0] if turmas else None
        mes_ano_str = datetime.now().strftime('%Y-%m')

    ano, mes = map(int, mes_ano_str.split('-'))

    # 3. Obter a lista de todos os alunos da turma selecionada
    alunos_da_turma = buscar_turma(turma_selecionada)

    # 4. Carregar os dados de presença do arquivo JSON
    mes_ano_arquivo = f"{str(mes).zfill(2)}_{ano}"
    arquivo_chamada = os.path.join('chamadas', f"{turma_selecionada}_{mes_ano_arquivo}.json")

    presencas_data = {}
    if os.path.exists(arquivo_chamada):
        with open(arquivo_chamada, 'r', encoding='utf-8') as f:
            presencas_data = json.load(f)

    # 5. Montar a estrutura de dados para o template
    _, num_dias = calendar.monthrange(ano, mes)
    dias_do_mes = list(range(1, num_dias + 1))

    dados_chamada = []
    for aluno in alunos_da_turma:
        codigo_aluno = aluno['Codigo']
        presencas_do_aluno = presencas_data.get(codigo_aluno, {}).get('presencas', [])

        # Cria uma lista de booleanos para a presença de cada dia
        dias_presente = [int(p.split('-')[2]) for p in presencas_do_aluno if p.startswith(f"{ano}-{str(mes).zfill(2)}")]

        presencas_grid = [dia in dias_presente for dia in dias_do_mes]

        dados_chamada.append({
            'nome': aluno['Nome'],
            'presencas': presencas_grid
        })

    # Formatar o mês para exibição (ex: "Novembro de 2025")
    data_obj = datetime(ano, mes, 1)
    mes_formatado = data_obj.strftime("%B de %Y").capitalize()

    return render_template('lista_mensal_turma.html',
                           turmas=turmas,
                           turma_selecionada=turma_selecionada,
                           mes_selecionado=mes_ano_str,
                           mes_formatado=mes_formatado,
                           dias_do_mes=dias_do_mes,
                           dados_chamada=dados_chamada,
                           escola_nome=CONFIG.get('escola', ''))

def registrar_chamada(aluno):
    """Registra a presença do aluno no arquivo de chamada mensal da turma."""
    now = datetime.now()
    mes_ano = now.strftime("%m_%Y")
    turma = aluno['Turma']

    chamada_dir = 'chamadas'
    os.makedirs(chamada_dir, exist_ok=True)

    arquivo_chamada = os.path.join(chamada_dir, f"{turma}_{mes_ano}.json")

    chamada_data = {}
    if os.path.exists(arquivo_chamada):
        with open(arquivo_chamada, 'r', encoding='utf-8') as f:
            try:
                chamada_data = json.load(f)
            except json.JSONDecodeError:
                chamada_data = {} # Inicia um novo se o arquivo estiver corrompido/vazio

    # Garante que o aluno está no dicionário
    codigo_aluno = aluno['Codigo']
    if codigo_aluno not in chamada_data:
        chamada_data[codigo_aluno] = {
            'nome': aluno['Nome'],
            'presencas': []
        }

    # Adicionar a data de hoje (sem horas) se ainda não estiver na lista
    data_hoje = now.strftime('%Y-%m-%d')
    if data_hoje not in chamada_data[codigo_aluno]['presencas']:
        chamada_data[codigo_aluno]['presencas'].append(data_hoje)

    with open(arquivo_chamada, 'w', encoding='utf-8') as f:
        json.dump(chamada_data, f, ensure_ascii=False, indent=4)

def ocorrencias_path(codigo):
    return os.path.join('ocorrencias', f'{codigo}.json')

@app.route('/ocorrencias/<codigo>')
@login_required
def ocorrencias_aluno(codigo):
    aluno = buscar_aluno(codigo)
    ocorrencias = []
    path = ocorrencias_path(codigo)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            ocorrencias = json.load(f)
    return render_template('ocorrencias_aluno.html', aluno=aluno, ocorrencias=ocorrencias)


@app.route('/ocorrencias/<codigo>/nova', methods=['GET', 'POST'])
@login_required
def nova_ocorrencia(codigo):
    aluno = buscar_aluno(codigo)
    if request.method == 'POST':
        texto = request.form.get('texto', '').strip()
        medida = request.form.get('medida', '').strip()
        registrado_por = request.form.get('registrado_por', '').strip()
        data = datetime.now().strftime('%d/%m/%Y %H:%M')
        ocorrencia = {
            'texto': texto,
            'medida': medida,
            'registrado_por': registrado_por,
            'data': data
        }
        path = ocorrencias_path(codigo)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                ocorrencias = json.load(f)
        else:
            ocorrencias = []
        ocorrencias.append(ocorrencia)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(ocorrencias, f, ensure_ascii=False, indent=2)
        return redirect(url_for('ocorrencias_aluno', codigo=codigo))
    return render_template('ocorrencia_nova.html', aluno=aluno)

# ROTA PARA EXCLUIR OCORRÊNCIA
@app.route('/ocorrencias/<codigo>/excluir', methods=['POST'])
@login_required
def excluir_ocorrencia(codigo):
    indice = request.form.get('indice', type=int)
    path = ocorrencias_path(codigo)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            ocorrencias = json.load(f)
        if 0 <= indice < len(ocorrencias):
            ocorrencias.pop(indice)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(ocorrencias, f, ensure_ascii=False, indent=2)
    return redirect(url_for('ocorrencias_aluno', codigo=codigo))

# Lista de diretórios necessários para o funcionamento do sistema
REQUIRED_DIRECTORIES = [
    'backups',
    'chamadas',
    'ocorrencias',
    'registros',
    'registros_diarios',
    os.path.join('static', 'barcodes'),
    os.path.join('static', 'fotos'),
    'backups'
]

if __name__ == '__main__':
    # Criar todos os diretórios necessários
    for directory in REQUIRED_DIRECTORIES:
        os.makedirs(directory, exist_ok=True)

    app.run(host='0.0.0.0', port=5000, debug=True)
