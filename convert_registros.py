
import os
import json
from datetime import datetime

REGISTROS_DIR = 'registros'

def parse_txt_file(filepath):
    """Lê um arquivo TXT antigo e estrutura em JSON."""
    data = {}
    history = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # Extrair metadados
    for line in lines[:6]:
        line = line.strip()
        if line.startswith('Nome:'):
            data['nome'] = line.replace('Nome:', '').strip()
        elif line.startswith('Turma:'):
            data['turma'] = line.replace('Turma:', '').strip()
        elif line.startswith('Turno:'):
            data['turno'] = line.replace('Turno:', '').strip()
        elif line.startswith('Código:'):
            data['codigo'] = line.replace('Código:', '').strip()

    # Validar metadados mínimos
    if 'codigo' not in data:
        return None

    # Extrair histórico
    for line in lines:
        line = line.strip()
        # Procura linhas com formato de data: DD/MM/YYYY HH:MM:SS - Detalhe
        if ' - ' in line and '/' in line and ':' in line:
            parts = line.split(' - ', 1)
            date_str = parts[0].strip()
            tipo = parts[1].strip()
            
            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
                history.append({
                    "data_hora": date_str,
                    "tipo": tipo,
                    "timestamp": dt.timestamp()
                })
            except ValueError:
                pass # Ignora linhas que parecem data mas não são válidas

    data['historico'] = history
    return data

def convert_all():
    count_success = 0
    count_fail = 0
    
    # Percorrer todas as pastas dentro de 'registros'
    for root, dirs, files in os.walk(REGISTROS_DIR):
        for file in files:
            if file.endswith('.txt') and not file.endswith('_old.txt'):
                txt_path = os.path.join(root, file)
                
                try:
                    data = parse_txt_file(txt_path)
                    
                    if data:
                        # Criar arquivo JSON
                        json_filename = file.replace('.txt', '.json')
                        json_path = os.path.join(root, json_filename)
                        
                        # Se já existe JSON, mesclar (opcional, mas seguro assumir sobrescrita ou merge)
                        # Aqui vamos sobrescrever ou criar se não existir, pois o TXT deve ser a fonte da verdade antiga
                        
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                            
                        # Renomear TXT original para não processar de novo
                        new_txt_name = txt_path.replace('.txt', '_old.txt')
                        # Se já existir o _old, remover antes para evitar erro no rename
                        if os.path.exists(new_txt_name):
                            os.remove(new_txt_name)
                        os.rename(txt_path, new_txt_name)
                        
                        print(f"Convertido: {file} -> {json_filename}")
                        count_success += 1
                    else:
                        print(f"Ignorado (formato inválido): {file}")
                        count_fail += 1
                        
                except Exception as e:
                    print(f"Erro ao converter {file}: {e}")
                    count_fail += 1

    print(f"\nConcluído! Sucessos: {count_success}, Falhas/Ignorados: {count_fail}")

if __name__ == "__main__":
    if not os.path.exists(REGISTROS_DIR):
        print(f"Diretório '{REGISTROS_DIR}' não encontrado.")
    else:
        convert_all()
