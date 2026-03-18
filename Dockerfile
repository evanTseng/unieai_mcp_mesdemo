FROM python:3.10-slim
LABEL "language"="python"
LABEL "framework"="fastapi"

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -e .

EXPOSE 9090

CMD ["unieai-mcp-mesdemo", "run", "--host", "0.0.0.0", "--port", "9090"]