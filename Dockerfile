# First stage: Builder
FROM python:3.11-slim AS builder

# Set environment variables for Poetry
ENV POETRY_VERSION=1.6.1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_NO_INTERACTION=1
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy only the necessary files to install dependencies
COPY pyproject.toml poetry.lock* ./

# Install project dependencies without installing the package itself
RUN poetry install --no-root

# Export the dependencies to requirements.txt
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Second stage: Final Image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install runtime dependencies, including postgresql-client
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt from the builder stage
COPY --from=builder requirements.txt .

# Install dependencies using pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY src/ ./src/
COPY alembic.ini ./
COPY database/ ./database/
COPY wait-for-postgres.sh /wait-for-postgres.sh
RUN chmod +x /wait-for-postgres.sh

# Default command (can be overridden)
CMD ["python", "src/app.py"]
