# Reproduces the benchmark and test suite on a known Python/OS combination,
# independent of the host machine. See docs/benchmarking.md and
# paper/sections/artifact.tex for what this does and does not cover: it
# runs the code (tests, benchmark suite, table/figure generation), not the
# LaTeX build (no TeX Live here — see the README for building main.pdf
# locally) and not the Jena/Virtuoso/GraphDB external-store comparisons
# (those require their own separately running server/container, reachable
# from wherever this image runs; see docs/benchmarking.md).
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy dependency manifests first so `uv sync` is cached across rebuilds
# that only change source code.
COPY pyproject.toml uv.lock ./
RUN uv sync --group dev --frozen --no-install-project

COPY . .
RUN uv sync --group dev --frozen

# Default: run the test suite. Override to run the benchmark instead, e.g.:
#   docker run --rm sfdb uv run sfdb benchmark
#   docker run --rm sfdb uv run python scripts/generate_tables.py
CMD ["uv", "run", "pytest"]
