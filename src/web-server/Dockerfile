FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY web_server.py .

EXPOSE 6000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "web_server:app"]
