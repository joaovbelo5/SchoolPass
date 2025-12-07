# Use uma imagem base oficial do Python
FROM python:3.12-slim

# Evita que o Python gere arquivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Garante que a saída do Python seja enviada diretamente para o terminal (logs)
ENV PYTHONUNBUFFERED=1

# Instala dependências do sistema necessárias (se houver)
# libgl1-mesa-glx é muitas vezes necessário para bibliotecas de imagem como OpenCV/Pillow em slim
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Configura o fuso horário
ENV TZ=America/Sao_Paulo

# Define o diretório de trabalho no container
WORKDIR /app

# Copia o arquivo de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt /app/

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto para o container
# Nota: É recomendável ter um .dockerignore para não copiar arquivos desnecessários
COPY . /app/

# Expõe as portas que o aplicativo usa
EXPOSE 5000
EXPOSE 5010

# Comando para iniciar o servidor
# Usamos o script start_server.py que já gerencia os dois processos
CMD ["python", "start_server.py"]
