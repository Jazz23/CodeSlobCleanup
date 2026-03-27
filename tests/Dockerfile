FROM node:latest

ENV PATH="/home/node/.local/bin:$PATH"
ENV CLAUDE_CONFIG_DIR="/home/node/.claude"
ENV COLORTERM="truecolor"
ENV TERM="xterm-256color"

RUN npm install -g @google/gemini-cli

USER node
RUN curl -fsSL https://claude.ai/install.sh | bash



WORKDIR /app