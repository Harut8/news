FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV VIRTUAL_ENV=/opt/venv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
     uv venv /opt/venv && \
     uv pip install -r pyproject.toml
ADD . /app
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ADD . .
RUN ["chmod", "+x", "entrypoint.sh"]
ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ["uvicorn", "--lifespan=on", "main:fastapi_app", "--host", "0.0.0.0", "--workers", "2", "--port", "80"]
# add: greenlet
