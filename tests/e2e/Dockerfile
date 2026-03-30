FROM node:latest

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV PATH="/home/node/.local/bin:$PATH"
ENV CLAUDE_CONFIG_DIR="/home/node/.claude"
ENV COLORTERM="truecolor"
ENV TERM="xterm-256color"

RUN npm install -g @google/gemini-cli

RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

USER node
RUN curl -fsSL https://claude.ai/install.sh | bash



WORKDIR /app