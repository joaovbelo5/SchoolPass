import os
import shutil
import json
import csv
from datetime import datetime
import logging

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ArchiveManager')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEGACY_DIR = os.path.join(BASE_DIR, 'legacy')

def get_available_years():
    """Retorna uma lista de anos que possuem arquivos na pasta legacy."""
    if not os.path.exists(LEGACY_DIR):
        return []
    years = []
    for entry in os.listdir(LEGACY_DIR):
        if os.path.isdir(os.path.join(LEGACY_DIR, entry)) and entry.isdigit():
            years.append(entry)
    return sorted(years, reverse=True)

def archive_year(year):
    """
    Arquiva os dados do ano especificado para a pasta legacy/{year}.
    
    Ações:
    1. Cria estrutura de pastas em legacy/{year}.
    2. Move registros_diarios do ano (ex: 2024-*.json / .csv).
    3. Filtra e move histórico de alunos de registros/{TURMA}/{CODIGO}.json.
    4. Move arquivos de chamadas do ano (ex: *2024.json).
    5. Copia database.csv.
    6. Copia fotos dos alunos ativos naquele ano.
    """
    year_str = str(year)
    target_dir = os.path.join(LEGACY_DIR, year_str)
    
    logger.info(f"Iniciando arquivamento do ano {year_str} para {target_dir}")
    
    # 1. Estrutura de pastas
    dirs_to_create = [
        os.path.join(target_dir, 'registros'),
        os.path.join(target_dir, 'registros_diarios'),
        os.path.join(target_dir, 'chamadas'),
        os.path.join(target_dir, 'fotos')
    ]
    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)
        
    # 2. Mover Registros Diários
    src_registros_diarios = os.path.join(BASE_DIR, 'registros_diarios')
    if os.path.exists(src_registros_diarios):
        for filename in os.listdir(src_registros_diarios):
            # Verifica se o arquivo começa com o ano (ex: 2024-05-20.json)
            if filename.startswith(year_str):
                src = os.path.join(src_registros_diarios, filename)
                dst = os.path.join(target_dir, 'registros_diarios', filename)
                try:
                    shutil.move(src, dst)
                    logger.info(f"Movido log diário: {filename}")
                except Exception as e:
                    logger.error(f"Erro ao mover {filename}: {e}")

    # 3. Filtrar Histórico de Alunos (registros/{TURMA}/{CODIGO}.json)
    src_registros = os.path.join(BASE_DIR, 'registros')
    if os.path.exists(src_registros):
        for turma_name in os.listdir(src_registros):
            turma_path = os.path.join(src_registros, turma_name)
            if not os.path.isdir(turma_path):
                continue
            
            # Criar pasta da turma no legacy
            legacy_turma_path = os.path.join(target_dir, 'registros', turma_name)
            os.makedirs(legacy_turma_path, exist_ok=True)
            
            for alu_file in os.listdir(turma_path):
                if not alu_file.endswith('.json'):
                    continue
                
                full_path = os.path.join(turma_path, alu_file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    historico = data.get('historico', [])
                    active_history = []
                    archived_history = []
                    
                    for entry in historico:
                        # Assumindo formato 'data_hora': 'dd/mm/yyyy HH:MM:SS'
                        dh = entry.get('data_hora', '')
                        if dh and year_str in dh:
                            # Checagem simples de string para robustez
                            archived_history.append(entry)
                        elif dh:
                            # Parsing mais especifico para evitar falsos positivos (Ex: codigo 2025...)
                            # Mas se o ano está na data, geralmente é seguro
                            # Vamos manter a logica de separacao se o ano nao estiver in loco
                            active_history.append(entry)
                        else:
                            active_history.append(entry)
                            
                    # Salvar no Legacy SEMPRE (para garantir que o arquivo exista)
                    data_legacy = data.copy()
                    data_legacy['historico'] = archived_history
                    legacy_file = os.path.join(legacy_turma_path, alu_file)
                    
                    try:
                        with open(legacy_file, 'w', encoding='utf-8') as f:
                            json.dump(data_legacy, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        logger.error(f"Erro ao salvar legacy {legacy_file}: {e}")
                    
                    # Atualizar arquivo original APENAS se houve remoção (itens arquivados)
                    if archived_history:
                        data['historico'] = active_history
                        try:
                            with open(full_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                        except Exception as e:
                             logger.error(f"Erro ao atualizar original {full_path}: {e}")
                            
                        logger.info(f"Processado histórico de {alu_file}: {len(archived_history)} itens arquivados.")
                    else:
                        logger.info(f"Processado {alu_file}: Nenhum item para arquivar, mas arquivo legado criado.")
                        
                except Exception as e:
                    logger.error(f"Erro ao processar histórico do aluno {alu_file}: {e}")

    # 4. Mover Chamadas (chamadas/*{year}.json)
    # Exemplo de arquivo: 1A_11_2025.json ou similar que contenha o ano
    src_chamadas = os.path.join(BASE_DIR, 'chamadas')
    if os.path.exists(src_chamadas):
        for filename in os.listdir(src_chamadas):
            if year_str in filename and filename.endswith('.json'):
                src = os.path.join(src_chamadas, filename)
                dst = os.path.join(target_dir, 'chamadas', filename)
                try:
                    shutil.move(src, dst)
                    logger.info(f"Movido arquivo de chamada: {filename}")
                except Exception as e:
                    logger.error(f"Erro ao mover chamada {filename}: {e}")

    # 4a. Mover Ocorrências
    logger.info("Arquivando ocorrências...")
    ocorrencias_dir = os.path.join(BASE_DIR, 'ocorrencias')
    legacy_ocorrencias_dir = os.path.join(target_dir, 'ocorrencias')
    os.makedirs(legacy_ocorrencias_dir, exist_ok=True)
    
    if os.path.exists(ocorrencias_dir):
        count_ocorrencias = 0
        for filename in os.listdir(ocorrencias_dir):
            if not filename.endswith('.json'):
                continue
                
            original_path = os.path.join(ocorrencias_dir, filename)
            legacy_path = os.path.join(legacy_ocorrencias_dir, filename)
            
            try:
                with open(original_path, 'r', encoding='utf-8') as f:
                    ocorrencias = json.load(f)
                
                ocorrencias_to_archive = []
                ocorrencias_to_keep = []
                
                for oc in ocorrencias:
                    # Data format: "DD/MM/YYYY HH:MM"
                    data_str = oc.get('data', '')
                    if str(year) in data_str: 
                         ocorrencias_to_archive.append(oc)
                    else:
                         ocorrencias_to_keep.append(oc)
                
                # Salvar no legado SEMPRE (para garantir que o arquivo exista)
                try:
                    with open(legacy_path, 'w', encoding='utf-8') as f:
                        json.dump(ocorrencias_to_archive, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.error(f"Erro ao salvar legacy ocorrencia {legacy_path}: {e}")

                # Salvar remanescentes no original APENAS se houve movimentação
                if ocorrencias_to_archive:
                    with open(original_path, 'w', encoding='utf-8') as f:
                        json.dump(ocorrencias_to_keep, f, ensure_ascii=False, indent=2)
                        
                    count_ocorrencias += 1
                else:
                    logger.info(f"Ocorrencia {filename}: Nada para arquivar, mas arquivo legado criado.")
                    
            except Exception as e:
                logger.error(f"Erro ao processar ocorrência {filename}: {e}")
                
        logger.info(f"Ocorrências processadas: {count_ocorrencias} arquivos afetados.")

    # 5. Copiar Database.csv
    db_path = os.path.join(BASE_DIR, 'database.csv')
    if os.path.exists(db_path):
        try:
            shutil.copy2(db_path, os.path.join(target_dir, 'database.csv'))
            logger.info("Database copiado para o arquivo.")
        except Exception as e:
            logger.error(f"Erro ao copiar database: {e}")

    # 6. Copiar Fotos
    # Ler o database copiado para saber quais fotos copiar
    # Isso evita copiar lixo ou fotos não usadas, otimizando espaço
    legacy_db_path = os.path.join(target_dir, 'database.csv')
    src_fotos = os.path.join(BASE_DIR, 'static', 'fotos')
    dst_fotos = os.path.join(target_dir, 'fotos')
    
    if os.path.exists(legacy_db_path) and os.path.exists(src_fotos):
        try:
            with open(legacy_db_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    foto = row.get('Foto')
                    if foto and foto.lower() != 'semfoto.jpg':
                        src_f = os.path.join(src_fotos, foto)
                        if os.path.exists(src_f):
                            try:
                                shutil.copy2(src_f, os.path.join(dst_fotos, foto))
                            except Exception as e:
                                logger.error(f"Erro ao copiar foto {foto}: {e}")
            logger.info("Cópia de fotos concluída.")
        except Exception as e:
            logger.error(f"Erro ao processar cópia de fotos: {e}")

    logger.info(f"Arquivamento do ano {year_str} finalizado.")
    return True
