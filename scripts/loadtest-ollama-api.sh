#!/usr/bin/env bash
set -e

# Load test script for Samplemind Ollama API

URL="http://localhost:8000/api/llm"
DATA='{"prompt": "Test prompt for load testing."}'
CONCURRENCY=4
REQUESTS=20

if ! command -v ab &> /dev/null; then
  echo "[!] ApacheBench (ab) is not installed. Please install it (brew install httpd or apt install apache2-utils)."
  exit 1
fi

echo "[+] Running load test: $REQUESTS requests, concurrency $CONCURRENCY..."
ab -p <(echo $DATA) -T application/json -c $CONCURRENCY -n $REQUESTS $URL 