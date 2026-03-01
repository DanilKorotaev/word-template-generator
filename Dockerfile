FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir -e .

EXPOSE 8080

CMD ["aosr-gen", "web-ui", "--host", "0.0.0.0", "--port", "8080", "--no-open"]
