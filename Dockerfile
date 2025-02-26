# Usando uma imagem oficial do Python como base
FROM python:3.9-slim

# Setando o diretório de trabalho
WORKDIR /app

# Copiando os arquivos da aplicação para o contêiner
COPY . /app

# Instalando as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expondo a porta 1400
EXPOSE 1400

# Comando para iniciar o servidor com Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:1400", "main:app"]
