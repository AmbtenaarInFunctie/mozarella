FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen

# Copy the rest of the application
COPY src/ ./src/
COPY docker/ ./docker/
COPY .env ./
COPY data/ ./data/

CMD ["uv", "run", "python", "src/api.py"]