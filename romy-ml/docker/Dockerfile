FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy the project files
COPY . .

# Install dependencies using uv
RUN uv lock

CMD ["uv", "run", "python", "src/api.py"]