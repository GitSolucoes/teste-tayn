# Usando uma imagem base com Python
FROM python:3.9-slim

# Definindo o diretório de trabalho
WORKDIR /app

# Copiando os arquivos do projeto para o contêiner
COPY . .

# Instalando as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Definindo o comando para rodar a aplicação com Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:1400", "main:app"]
