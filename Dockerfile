# Usa uma imagem do Python
FROM python:3.10

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta do Flask
EXPOSE 1400

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:1400", "main:app"]
