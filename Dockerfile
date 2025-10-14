FROM python:3.11-slim

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# libs de sistema usadas por PIL/plotly/opencv headless etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Streamlit vai escutar na 0.0.0.0:8080
ENV PORT=8080
CMD ["bash","-lc","streamlit run app.py --server.port $PORT --server.address 0.0.0.0"]
