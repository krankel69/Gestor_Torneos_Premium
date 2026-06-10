# Usamos la imagen oficial de Python 3.14
FROM python:3.14-slim

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos los requirements e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto
COPY . .

# Exponemos el puerto
EXPOSE 8000

# Comando para arrancar la API
CMD ["uvicorn", "src.api_rest.main:app", "--host", "0.0.0.0", "--port", "8000"]