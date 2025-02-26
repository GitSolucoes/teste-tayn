# Usa uma imagem base com Python 3 (exemplo: Debian)
FROM python:3.10-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia os arquivos do projeto para dentro do contêiner
COPY . .

# Instala as dependências do projeto, incluindo o Gunicorn
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Define a porta que o contêiner vai expor
EXPOSE 1400

# Comando para rodar o Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
