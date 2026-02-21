FROM python:3.10-slim

# Install Docker CLI (for building test containers)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends docker-ce-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir requests

# Create working directory
WORKDIR /app

# Copy source code
COPY src/ /app/src/
COPY run.py /app/run.py

# Mount points:
# /gists  - the hard-gists folder
# /var/run/docker.sock - Docker socket for building test containers
# /results - output results directory

CMD ["python", "run.py", "--help"]
