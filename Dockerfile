FROM python:3.11-slim

WORKDIR /app
COPY src/ /app/

# Sem dependências externas: usa apenas a biblioteca padrão do Python.
ENTRYPOINT ["python", "main.py"]
