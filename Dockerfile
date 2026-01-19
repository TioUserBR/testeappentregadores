# 1. Imagem base
FROM python:3.11-slim

# 2. Diretório de trabalho dentro do container
WORKDIR /app

# 3. Copiar arquivos do projeto
COPY . .

# 4. Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# 5. Expor porta do Flask
EXPOSE 5000

# 6. Variáveis de ambiente do Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# 7. Comando de inicialização
CMD ["flask", "run"]
