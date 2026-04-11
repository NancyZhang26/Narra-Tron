FROM debian:trixie-slim

RUN apt-get update && api-get install -y \
    python3 \
    python3-pip \ && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

CMD ["python3", "main.py"]