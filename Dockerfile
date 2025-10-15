# Use Python slim image
FROM python:3.12-slim

RUN apt update && apt install -y postgresql-client libatomic1
# Set working directory
WORKDIR /app
ENV PYTHONPATH=/app:$PYTHONPATH

# Copy dependencies if needed
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your scripts
COPY . . 

# Build the prima 
RUN prisma generate

ENTRYPOINT ["python3"]
