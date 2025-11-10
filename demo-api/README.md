# Demo API

A portable Python REST API built with FastAPI for testing across multiple deployment platforms.

## Quick Start

```bash
# Install dependencies with uv
uv pip install -e .

# Run locally
python src/main.py
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## Deployment

See [Kubernetes deployment documentation](../apps/base/demo-api/README.md) for detailed deployment instructions.

## Project Structure

```
demo-api/
├── src/
│   └── main.py          # FastAPI application
├── pyproject.toml       # Dependencies (uv)
├── Dockerfile           # Container image
└── README.md           # This file
```

## Features

- REST API with automatic OpenAPI docs
- Health checks for container orchestration
- System info endpoints for debugging
- Security best practices (non-root user, resource limits)
- Built with uv for fast, reliable builds

## Documentation

Full documentation available at: [apps/base/demo-api/README.md](../apps/base/demo-api/README.md)
