# Docker image for a Hugging Face Space (SDK: docker, app_port: 7860).
# deploy/oracle/docker-compose.yml builds the same image for a plain VM.
#
# The Space repository only needs this file and README.md (with the YAML header). The image
# clones this GitHub repository at REPO_REF, builds the Next.js frontend in standalone mode
# and runs it on port 7860 next to the FastAPI backend on 127.0.0.1:8000. Next.js proxies
# /api/* to the backend (frontend/next.config.ts), so only one port is exposed.
#
# To deploy a newer commit: push it to REPO_REF on GitHub, then "Factory rebuild" the Space.

ARG REPO_URL=https://github.com/DavBao-dev/Dysgraphia-Screening-Prototype.git
ARG REPO_REF=main
# Upload limit for the hosted demo (MB). The free CPU Space has 2 vCPUs, so long 4K videos
# would take several minutes to process.
ARG MAX_VIDEO_MB=200

# ---------------------------------------------------------------- source
FROM debian:bookworm-slim AS source
ARG REPO_URL
ARG REPO_REF
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && git clone --depth 1 --branch "${REPO_REF}" "${REPO_URL}" /src

# ---------------------------------------------------------------- frontend build
FROM node:22-bookworm-slim AS frontend
ARG MAX_VIDEO_MB
WORKDIR /src/frontend
COPY --from=source /src/frontend/package.json /src/frontend/package-lock.json ./
RUN npm ci
COPY --from=source /src/frontend ./
ENV NEXT_OUTPUT_STANDALONE=1 \
    NEXT_PUBLIC_MAX_VIDEO_MB=${MAX_VIDEO_MB} \
    NEXT_TELEMETRY_DISABLED=1
RUN npm run build \
 && cp -r public .next/standalone/ \
 && cp -r .next/static .next/standalone/.next/

# ---------------------------------------------------------------- runtime
FROM python:3.11-slim-bookworm
ARG MAX_VIDEO_MB

# libgl1 / libglib2.0-0: needed by the OpenCV build that mediapipe pulls in.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 curl \
 && rm -rf /var/lib/apt/lists/*
COPY --from=node:22-bookworm-slim /usr/local/bin/node /usr/local/bin/node

# Hugging Face runs the container as uid 1000.
RUN useradd -m -u 1000 user
WORKDIR /app

COPY --from=source /src/requirements.txt ./
# CPU-only PyTorch first (much smaller than the default CUDA build); requirements.txt then
# sees torch/torchvision as already installed.
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

COPY --from=source --chown=user /src/backend ./backend
COPY --from=source --chown=user /src/weights ./weights
COPY --from=source --chown=user /src/deploy/huggingface/start.sh ./start.sh
COPY --from=frontend --chown=user /src/frontend/.next/standalone ./frontend
RUN mkdir -p data && chown user:user data

USER user
ENV HOME=/home/user \
    PYTHONUNBUFFERED=1 \
    MAX_VIDEO_SIZE_MB=${MAX_VIDEO_MB} \
    PORT=7860 \
    HOSTNAME=0.0.0.0 \
    NEXT_TELEMETRY_DISABLED=1
EXPOSE 7860
CMD ["bash", "start.sh"]
