from flask import flash

# --- Rotas administrativas para alterar configurações sensíveis ---
from werkzeug.utils import secure_filename

def register_admin_routes(app):
    from flask import flash, render_template, request, session, jsonify
    from flask_login import login_required
    import os, time, sys
    try:
        import archive_manager
    except ImportError:
        # Fallback caso o arquivo ainda não esteja no path ou erro de importação
        print("Erro ao importar archive_manager")


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

    @app.route('/admin/backup_api', methods=['GET'])
    @login_required
    def admin_backup_api():
        """Cria um arquivo ZIP no disco (pasta backups/) e retorna JSON com URL de download. Mantém backups por 3 horas."""
        try:
            import zipfile
            from datetime import datetime
            from flask import url_for
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
                os.path.join(base_dir, 'registros_diarios'),
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

            # Retornar JSON com a URL para download
            download_url = url_for('admin_download_backup', filename=filename)
            return jsonify({'ok': True, 'msg': 'Backup criado com sucesso.', 'download_url': download_url, 'filename': filename})

        except Exception as e:
            logger.exception('Erro ao criar backup')
            return jsonify({'ok': False, 'msg': f'Erro ao criar backup: {e}'}), 500

    @app.route('/admin/download_backup/<path:filename>')
    @login_required
    def admin_download_backup(filename):
        """Serve o arquivo de backup para download."""
        from flask import send_from_directory
        base_dir = os.path.dirname(__file__)
        backups_dir = os.path.join(base_dir, 'backups')
        return send_from_directory(backups_dir, filename, as_attachment=True)

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
                if not os.path.exists(src):
                    return

                # Tentar remover completamente o diretório destino
                if os.path.exists(dst):
                    try:
                        shutil.rmtree(dst)
                    except Exception as e:
                        logger.error(f"Erro removendo destino {dst}: {e}")
                
                # Se o destino ainda existe (remoção falhou), usar copytree com dirs_exist_ok=True
                if os.path.exists(dst):
                    try:
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                        logger.info(f"Pasta restaurada (merge): {dst}")
                    except Exception as e:
                        logger.error(f"Erro mesclando {src} -> {dst}: {e}")
                else:
                    try:
                        # mover pasta extraída para o local destino
                        shutil.move(src, dst)
                        logger.info(f"Pasta restaurada: {dst}")
                    except Exception as e:
                        logger.error(f"Erro movendo {src} -> {dst}: {e}")

            # Alvos a serem restaurados (mesma lista do backup)
            targets_dirs = [
                'chamadas', 'ocorrencias', 'registros', 'registros_diarios',
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

    @app.route('/admin/restart', methods=['POST'])
    @login_required
    def admin_restart():
        """Reinicia o servidor Flask."""
        try:
            logger.info("Reiniciando servidor por solicitação do admin...")
            # Reinicia o processo atual
            # sys.executable é o interpretador Python
            # sys.argv são os argumentos passados para o script
            # Reinicia o processo atual
            # Usa sys.executable e __file__ absoluto para garantir caminhos corretos
            # Soft reboot: apenas "toca" o arquivo para acionar o reloader do Flask
            # Isso evita problemas com os.execv em diferentes ambientes e mantém o processo rodando
            script = os.path.abspath(__file__)
            os.utime(script, None)
            
            return jsonify({'ok': True, 'msg': 'Reiniciando (Soft Reboot)...'})
        except Exception as e:
            logger.exception("Erro ao reiniciar servidor")
            return jsonify({'ok': False, 'msg': f'Erro ao reiniciar: {e}'}), 500

    @app.route('/admin/legacy', methods=['GET', 'POST'])
    @login_required
    def admin_legacy_index():
        """Painel principal de Legado/Arquivamento."""
        if request.method == 'POST':
            year = request.form.get('year')
            if not year or not year.isdigit():
                flash('Ano inválido.', 'error')
            else:
                try:
                    if archive_manager.archive_year(year):
                        flash(f'Ano {year} arquivado com sucesso!', 'success')
                    else:
                        flash(f'Erro ao arquivar ano {year}. Verifique os logs.', 'error')
                except Exception as e:
                    logger.exception(f"Erro ao arquivar {year}: {e}")
                    flash(f'Erro crítico ao arquivar: {e}', 'error')
        
        years = archive_manager.get_available_years()
        return render_template('legacy_index.html', years=years)

    @app.route('/admin/legacy/delete/<year>', methods=['POST'])
    @login_required
    def admin_legacy_delete(year):
        """Exclui um arquivo de ano legado."""
        if not year.isdigit():
            flash('Ano inválido.', 'error')
            return redirect(url_for('admin_legacy_index'))
        
        target_dir = os.path.join(os.path.dirname(__file__), 'legacy', str(year))
        
        if os.path.exists(target_dir):
            try:
                import shutil
                shutil.rmtree(target_dir)
                flash(f'Arquivo do ano {year} excluído permanentemente.', 'success')
            except Exception as e:
                logger.error(f"Erro ao excluir legacy {year}: {e}")
                flash(f'Erro ao excluir arquivo: {e}', 'error')
        else:
            flash(f'Arquivo do ano {year} não encontrado.', 'error')
            
        return redirect(url_for('admin_legacy_index'))

    @app.route('/admin/legacy/view/<year>')
    @login_required
    def admin_legacy_view(year):
        """Visualização de dados históricos (Read-Only)."""
        # Validar se o ano existe
        target_dir = os.path.join(os.path.dirname(__file__), 'legacy', str(year))
        if not os.path.exists(target_dir):
            flash(f'Arquivo do ano {year} não encontrado.', 'error')
            return redirect(url_for('admin_index'))
            
        return render_template('legacy_view.html', year=year)

    @app.route('/admin/legacy/api/<year>/search')
    @login_required
    def admin_legacy_search_api(year):
        """API de busca para o modo legado."""
        query = request.args.get('q', '').lower()
        if not query:
            return jsonify([])
        
        target_dir = os.path.join(os.path.dirname(__file__), 'legacy', str(year))
        db_path = os.path.join(target_dir, 'database.csv')
        
        results = []
        if os.path.exists(db_path):
            try:
                import csv
                with open(db_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Busca por nome ou código
                        if query in row['Nome'].lower() or query in row['Codigo'].lower():
                            # Buscar histórico
                            turma = row['Turma']
                            codigo = row['Codigo']
                            hist_path = os.path.join(target_dir, 'registros', turma, f"{codigo}.json")
                            historico = []
                            if os.path.exists(hist_path):
                                try:
                                    import json
                                    with open(hist_path, 'r', encoding='utf-8') as hf:
                                        hdata = json.load(hf)
                                        historico = hdata.get('historico', [])
                                except:
                                    pass
                            
                            results.append({
                                'Nome': row['Nome'],
                                'Codigo': row['Codigo'],
                                'Turma': row['Turma'],
                                'Foto': row.get('Foto', ''),
                                'Historico': historico
                            })
                            if len(results) > 20: # Limite de resultados
                                break
            except Exception as e:
                logger.error(f"Erro na busca legado: {e}")
        
        return jsonify(results)

    @app.route('/admin/legacy/image/<year>/<filename>')
    @login_required
    def admin_legacy_image(year, filename):
        """Serve imagens do arquivo legado."""
        from flask import send_from_directory
        # Caminho: base_dir/legacy/{year}/fotos/
        base_dir = os.path.dirname(__file__)
        img_dir = os.path.join(base_dir, 'legacy', str(year), 'fotos')
        return send_from_directory(img_dir, filename)

    @app.route('/admin/legacy/print/<year>/<turma>/<codigo>')
    @login_required
    def admin_legacy_print(year, turma, codigo):
        """Gera relatório de impressão para aluno arquivado."""
        import csv
        import json
        
        target_dir = os.path.join(os.path.dirname(__file__), 'legacy', str(year))
        
        # 1. Carregar Aluno do Database Legacy
        aluno = None
        db_path = os.path.join(target_dir, 'database.csv')
        if os.path.exists(db_path):
            try:
                with open(db_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['Codigo'] == codigo:
                            aluno = row
                            break
            except Exception as e:
                logger.error(f"Erro ao ler database legacy: {e}")
        
        if not aluno:
             return f"Aluno {codigo} não encontrado no arquivo de {year}", 404

        # 2. Carregar Histórico
        historico = []
        hist_path = os.path.join(target_dir, 'registros', turma, f"{codigo}.json")
        if os.path.exists(hist_path):
            try:
                with open(hist_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    historico = data.get('historico', [])
            except:
                pass

        # 3. Carregar Ocorrências
        ocorrencias = []
        oco_path = os.path.join(target_dir, 'ocorrencias', f"{codigo}.json")
        if os.path.exists(oco_path):
             try:
                with open(oco_path, 'r', encoding='utf-8') as f:
                    ocorrencias = json.load(f)
             except:
                pass
        
        return render_template('legacy_print.html', aluno=aluno, historico=historico, ocorrencias=ocorrencias, year=year)





from flask import Flask, render_template, request, redirect, url_for, send_from_directory, g, jsonify
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
import re

# Lock global para proteger acesso ao database.csv
# Lock global para proteger acesso ao database.csv
db_lock = threading.RLock()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Adicionar handler de arquivo para debug
file_handler = logging.FileHandler('server.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

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
app.config['TELEGRAM_API_URL'] = f'https://api.telegram.org/bot{app.config["TELEGRAM_TOKEN"]}/'
app.config['COOLDOWN_MINUTES'] = int(os.getenv('COOLDOWN_MINUTES', 5))

# Cache de updates já processados para evitar mensagens duplicadas
processed_updates = set()

def normalize_phone(phone):
    """Remove caracteres não numéricos e ignora código do país (+55)."""
    if not phone:
        return ""
    # Remove tudo que não é dígito
    nums = re.sub(r'\D', '', str(phone))
    # Se começar com 55 e tiver mais de 11 dígitos (ex: 5561999999999), remove o 55
    if nums.startswith('55') and len(nums) > 11:
        nums = nums[2:]
    return nums

def telegram_bot_listener():
    """Thread que escuta atualizações do Bot para vincular contatos."""
    global processed_updates
    offset = 0
    api_url = app.config['TELEGRAM_API_URL']
    logger.info("Iniciando listener do Telegram Bot...")
    logger.info(f"API URL configurada: {api_url.replace(app.config['TELEGRAM_TOKEN'], '******')}")
    
    # Verificar se o token tem aspas extras (erro comum no .env)
    if "'" in app.config['TELEGRAM_TOKEN'] or '"' in app.config['TELEGRAM_TOKEN']:
        logger.warning("⚠️ AVISO: O token do Telegram parece conter aspas. Verifique o arquivo .env!")

    while True:
        try:
            # Long polling
            response = requests.get(f"{api_url}getUpdates", params={'offset': offset, 'timeout': 30}, timeout=40)
            if response.status_code == 200:
                data = response.json()
                if data.get('result'):
                    logger.info(f"Updates recebidos: {data['result']}")
                for result in data.get('result', []):
                    update_id = result['update_id']
                    offset = update_id + 1
                    
                    # Verificar se já processamos este update (evita duplicatas)
                    if update_id in processed_updates:
                        logger.debug(f"Update {update_id} já processado, pulando...")
                        continue
                    
                    message = result.get('message', {})
                    chat_id = message.get('chat', {}).get('id')
                    contact = message.get('contact')
                    
                    if contact and chat_id:
                        phone_number = contact.get('phone_number')
                        user_id = contact.get('user_id')
                        
                        # Normalizar telefone recebido
                        normalized_received = normalize_phone(phone_number)
                        logger.info(f"Recebido contato: {normalized_received} de {user_id}")
                        
                        # Buscar no banco de dados com índice otimizado
                        alunos_encontrados = []
                        with db_lock:
                            alunos = read_database()
                            
                            # Criar índice: telefone normalizado -> lista de índices de alunos
                            phone_index = {}
                            for i, aluno in enumerate(alunos):
                                stored_phone = normalize_phone(aluno.get('TelefoneResponsavel', ''))
                                if stored_phone:
                                    if stored_phone not in phone_index:
                                        phone_index[stored_phone] = []
                                    phone_index[stored_phone].append(i)
                            
                            # Busca otimizada O(1) no índice
                            if normalized_received in phone_index:
                                updated = False
                                for idx in phone_index[normalized_received]:
                                    aluno = alunos[idx]
                                    aluno['TelegramID'] = str(user_id)
                                    alunos_encontrados.append(aluno['Nome'])
                                    updated = True
                                    logger.info(f"MATCH! Vinculando {aluno['Nome']} ao ID {user_id}")
                                
                                if updated:
                                    write_database(alunos)
                            else:
                                logger.info(f"Nenhum aluno encontrado com o telefone {normalized_received}")
                        
                        # Responder ao usuário
                        if alunos_encontrados:
                            nomes = ", ".join(alunos_encontrados)
                            msg = f"✅ Vinculado com sucesso! Você receberá avisos de: {nomes}."
                        else:
                            msg = "❌ Número não encontrado no sistema. Peça para a escola cadastrar seu telefone."
                            
                        requests.post(f"{api_url}sendMessage", json={'chat_id': chat_id, 'text': msg})
                    
                    elif chat_id and message.get('text'):
                        # Se o usuário mandou texto, pedimos o contato
                        msg = "👋 Olá! Para receber os avisos da escola, preciso que você compartilhe seu contato.\n\nPor favor, clique no botão abaixo:"
                        keyboard = {
                            "keyboard": [[{"text": "📱 Compartilhar meu Contato", "request_contact": True}]],
                            "resize_keyboard": True,
                            "one_time_keyboard": True
                        }
                        requests.post(f"{api_url}sendMessage", json={'chat_id': chat_id, 'text': msg, 'reply_markup': keyboard})
                    
                    # Marcar update como processado
                    processed_updates.add(update_id)
                    
                    # Limpar cache se ultrapassar 1000 itens (previne vazamento de memória)
                    if len(processed_updates) > 1000:
                        logger.info("Limpando cache de updates processados...")
                        processed_updates.clear()
                        
            time.sleep(5)
        except Exception as e:
            logger.error(f"Erro no listener do Telegram: {e}")
            time.sleep(5)

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

# Configuração de logging (REMOVIDO - JÁ CONFIGURADO NO TOPO)
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

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
        
    arquivo_path = os.path.join(pasta_turma, f"{codigo}.json")
    
    # Estrutura base do registro
    data_registro = {
        'codigo': codigo,
        'nome': nome,
        'turma': turma,
        'turno': buscar_aluno(codigo).get('Turno', ''),
        'historico': []
    }
    
    # Carregar existente ou criar novo
    if os.path.exists(arquivo_path):
        try:
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                data_registro = json.load(f)
        except Exception as e:
            logger.error(f"Erro ao ler JSON existente {arquivo_path}: {e}")
            # Se der erro, tenta manter os dados básicos
            pass
            
    # Adicionar novo registro ao histórico
    novo_historico = {
        'data_hora': data_hora,
        'tipo': tipo_acesso,
        'timestamp': now.timestamp()
    }
    data_registro['historico'].append(novo_historico)
    
    # Salvar
    try:
        with open(arquivo_path, 'w', encoding='utf-8') as f:
            json.dump(data_registro, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar registro JSON {arquivo_path}: {e}")
    
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
            url = f"{app.config['TELEGRAM_API_URL']}sendMessage"
            response = requests.post(url, params=params, timeout=2)
            response.raise_for_status()
            logger.info(f"Mensagem enviada com sucesso: {response.json()}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar para Telegram: {e}")
    threading.Thread(target=send_async, daemon=True).start()

def enviar_mensagem_generica(chat_id, texto):
    """Envia uma mensagem genérica ao Telegram de forma síncrona."""
    try:
        url = f"{app.config['TELEGRAM_API_URL']}sendMessage"
        params = {'chat_id': chat_id, 'text': texto}
        response = requests.post(url, params=params, timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem genérica para {chat_id}: {e}")
        return False

def enviar_notificacao_ocorrencia(chat_id, nome_aluno, medida, descricao, registrado_por):
    """Envia notificação de ocorrência disciplinar ao Telegram."""
    import threading
    
    msg = (
        f"⚠️ *NOVA OCORRÊNCIA REGISTRADA*\n\n"
        f"👤 *Aluno:* {nome_aluno}\n"
        f"⚖️ *Medida:* {medida}\n"
        f"📝 *Descrição:* {descricao}\n"
        f"👮 *Registrado por:* {registrado_por}\n\n"
        f"📅 {datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    )
    
    params = {'chat_id': chat_id, 'text': msg, 'parse_mode': 'Markdown'}
    
    def send_async():
        try:
            url = f"{app.config['TELEGRAM_API_URL']}sendMessage"
            response = requests.post(url, params=params, timeout=5)
            response.raise_for_status()
            logger.info(f"Notificação de ocorrência enviada para {nome_aluno}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar notificação de ocorrência: {e}")
            
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
    with db_lock:
        with open(app.config['DATABASE'], 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

def write_database(data):
    """Escreve os dados no arquivo database.csv."""
    with db_lock:
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

# Rotas públicas
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
@app.route('/registro', methods=['GET', 'POST'])
@login_required
def registro():
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

    return render_template('registro.html', 
                          mensagem=mensagem, 
                          aluno=aluno, 
                          alerta=alerta, 
                          erro=erro)

@app.route('/', methods=['GET'])
@login_required
def index():
    # Calcular estatísticas para o dashboard
    alunos = read_database()
    total_alunos = len(alunos)
    
    # Contar turmas únicas
    turmas = set(a['Turma'] for a in alunos if a.get('Turma'))
    total_turmas = len(turmas)
    
    # Presentes hoje (total de acessos únicos)
    # A variável global 'alunos_registrados_hoje' contém (codigo, data)
    # Precisamos filtrar pela data de hoje, mas a variável já é limpa diariamente
    # Então basta contar o tamanho do set
    ensure_current_day()
    presentes_hoje = len(alunos_registrados_hoje)
    
    # Breakdown por turno (usando contadores globais)
    por_turno = dict(contadores)

    # Status do Telegram e Alunos Vinculados
    telegram_status = 'Offline'
    telegram_bot_name = ''
    total_linked = sum(1 for a in alunos if a.get('TelegramID'))
    
    try:
        # Check rápido de conexão (timeout curto)
        url = f"{app.config['TELEGRAM_API_URL']}getMe"
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('ok'):
                telegram_status = 'Online'
                telegram_bot_name = data['result'].get('first_name', 'Bot')
    except Exception as e:
        logger.error(f"Erro ao verificar status do Telegram: {e}")

    # Última atualização do banco de dados
    db_last_update = ''
    try:
        mtime = os.path.getmtime(app.config['DATABASE'])
        db_last_update = datetime.fromtimestamp(mtime).strftime('%d/%m/%Y %H:%M')
    except Exception:
        pass
    
    # Recent Activity (from daily JSON log)
    recent_logs = []
    try:
        today_date = datetime.now().strftime('%Y-%m-%d')
        daily_log_path = os.path.join('registros_diarios', f"{today_date}.json")
        if os.path.exists(daily_log_path):
            with open(daily_log_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
                # Sort by reverse order (assuming they are appended, so last is newest)
                # But to be safe, we reverse the list
                recent_logs = logs[::-1][:10] # Get last 10 entries
    except Exception as e:
        logger.error(f"Erro ao ler logs recentes: {e}")

    return render_template('index.html',
                          total_alunos=total_alunos,
                          total_turmas=total_turmas,
                          presentes_hoje=presentes_hoje,
                          por_turno=por_turno,
                          telegram_status=telegram_status,
                          telegram_bot_name=telegram_bot_name,
                          total_linked=total_linked,
                          db_last_update=db_last_update,
                          recent_logs=recent_logs)

@app.route('/api/registrar_acesso', methods=['POST'])
@login_required
def api_registrar_acesso():
    """Registra acesso manualmente via API (substitui antiga /consulta)."""
    try:
        data = request.get_json() or request.form
        codigo = str(data.get('registrar_codigo', '')).strip()
        
        if not codigo:
             return jsonify({'ok': False, 'msg': 'Código não informado!', 'tipo': 'danger'})

        aluno = buscar_aluno(codigo)
        if aluno:
            if aluno['Permissao'].lower() == 'sim':
                now = datetime.now()
                ultimo = ultimo_registro.get(codigo)
                if ultimo and (now - ultimo['hora']) < timedelta(minutes=app.config['COOLDOWN_MINUTES']):
                    return jsonify({'ok': True, 'msg': "⏳ Aguarde antes de registrar novamente.", 'tipo': 'warning'})
                else:
                    registrar_acesso(aluno['Codigo'], aluno['Nome'], aluno['Turma'], "Acesso")
                    if aluno['TelegramID']:
                        enviar_telegram(aluno['TelegramID'], aluno['Nome'], "Acesso")
                    ultimo_registro[codigo] = {'hora': now}
                    return jsonify({'ok': True, 'msg': "✅ Acesso Registrado com Sucesso!", 'tipo': 'success'})
            else:
                 return jsonify({'ok': True, 'msg': "⛔ Acesso Negado!", 'tipo': 'danger'})
        else:
             return jsonify({'ok': False, 'msg': "⚠️ Código não encontrado!", 'tipo': 'danger'})
            
    except Exception as e:
        logger.exception("Erro ao registrar acesso via API")
        return jsonify({'ok': False, 'msg': f"Erro interno: {e}", 'tipo': 'error'}), 500

@app.route('/get_contadores')
@login_required
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
        # aluno['TelegramID'] não é atualizado diretamente pelo form
        aluno['TelefoneResponsavel'] = request.form.get('telefone_responsavel', '')
        
        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                aluno['Foto'] = filename
        
        write_database(alunos)
        return redirect(url_for('cadastro'))
    
    return render_template('upload_editar.html', aluno=aluno)

@app.route('/cadastro/desvincular/<codigo>')
@login_required
def desvincular(codigo):
    alunos = read_database()
    aluno = next((a for a in alunos if a['Codigo'] == codigo), None)
    if aluno:
        aluno['TelegramID'] = ''
        aluno['TelefoneResponsavel'] = ''
        write_database(alunos)
        flash('Telegram e telefone desvinculados com sucesso!', 'success')
    return redirect(url_for('editar', codigo=codigo))

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
        telefone_responsavel = request.form.get('telefone_responsavel', '').strip()
        # telegramid = request.form.get('telegramid', '').strip() # Removido
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
            'TelegramID': '', # Inicialmente vazio, será preenchido pelo bot
            'TelefoneResponsavel': telefone_responsavel
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
    """Serve files from the 'registros' directory."""
    registros_dir = os.path.abspath('registros')
    return send_from_directory(registros_dir, filename)


@app.route('/api/aluno/<turma>/<codigo>/historico')
@login_required
def api_aluno_historico(turma, codigo):
    """API para retornar o histórico de um aluno."""
    arquivo_path = os.path.join('registros', turma, f"{codigo}.json")
    if os.path.exists(arquivo_path):
        try:
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({'ok': True, 'data': data})
        except Exception as e:
            return jsonify({'ok': False, 'msg': f'Erro ao ler dados: {e}'})
    else:
        # Se não existir arquivo, retorna dados básicos do aluno com histórico vazio
        aluno = buscar_aluno(codigo)
        if aluno:
             return jsonify({
                'ok': True, 
                'data': {
                    'codigo': codigo,
                    'nome': aluno['Nome'],
                    'turma': aluno['Turma'],
                    'turno': aluno['Turno'],
                    'historico': []
                }
            })
        return jsonify({'ok': False, 'msg': 'Registro não encontrado'})



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
            
        # Enviar notificação se houver Telegram vinculado e medida relevante
        medidas_ignoradas = ["Advertência Oral", "Outra", "Nenhuma medida necessária"]
        if aluno.get('TelegramID') and medida not in medidas_ignoradas:
            enviar_notificacao_ocorrencia(
                aluno['TelegramID'],
                aluno['Nome'],
                medida,
                texto,
                registrado_por
            )
            
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

# --- ROTA DE MENSAGENS EM MASSA ---
@app.route('/mensagens', methods=['GET', 'POST'])
@login_required
def mensagens():
    historico_path = 'mensagens_historico.json'
    
    # Carregar histórico
    historico = []
    if os.path.exists(historico_path):
        try:
            with open(historico_path, 'r', encoding='utf-8') as f:
                historico = json.load(f)
                # Ordenar por data (mais recente primeiro)
                historico.reverse()
        except Exception as e:
            logger.error(f"Erro ao ler histórico de mensagens: {e}")

    # Carregar turmas para o filtro
    alunos = read_database()
    turmas = sorted(list(set(a['Turma'] for a in alunos if a.get('Turma'))))

    if request.method == 'POST':
        turma_alvo = request.form.get('turma')
        mensagem_template = request.form.get('mensagem')
        
        if not mensagem_template:
            flash('A mensagem não pode estar vazia.', 'error')
            return redirect(url_for('mensagens'))

        # Filtrar destinatários
        destinatarios = []
        for aluno in alunos:
            # Verifica se tem Telegram vinculado
            if not aluno.get('TelegramID'):
                continue
            
            # Verifica filtro de turma
            if turma_alvo != 'todos' and aluno.get('Turma') != turma_alvo:
                continue
                
            destinatarios.append(aluno)

        if not destinatarios:
            flash('Nenhum destinatário encontrado com Telegram vinculado para a seleção atual.', 'warning')
            return redirect(url_for('mensagens'))

        # Enviar mensagens
        enviados_count = 0
        
        for aluno in destinatarios:
            # Personalizar mensagem
            msg_final = mensagem_template.replace('{nome}', aluno['Nome'])
            
            # Enviar
            if enviar_mensagem_generica(aluno['TelegramID'], msg_final):
                enviados_count += 1
        
        # Salvar no histórico
        novo_registro = {
            'data': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'mensagem': mensagem_template,
            'total_enviados': enviados_count,
            'sucesso': True
        }
        
        # Adicionar ao histórico
        try:
            current_hist = []
            if os.path.exists(historico_path):
                with open(historico_path, 'r', encoding='utf-8') as f:
                    current_hist = json.load(f)
            
            current_hist.append(novo_registro)
            
            with open(historico_path, 'w', encoding='utf-8') as f:
                json.dump(current_hist, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Erro ao salvar histórico de mensagens: {e}")

        flash(f'Mensagens enviadas para {enviados_count} pessoas!', 'success')
        return redirect(url_for('mensagens'))

    return render_template('mensagens.html', turmas=turmas, historico=historico)

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
    
    # Iniciar thread do Telegram Bot listener
    logger.info("Iniciando thread do Telegram Bot listener...")
    threading.Thread(target=telegram_bot_listener, daemon=True).start()

    app.run(host='0.0.0.0', port=5000, debug=False)
