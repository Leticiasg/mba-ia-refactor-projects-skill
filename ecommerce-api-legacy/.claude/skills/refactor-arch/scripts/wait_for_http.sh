#!/usr/bin/env bash
# Espera a aplicação responder em uma URL.
# Uso: wait_for_http.sh <url> [timeout_segundos=20]
# Saída 0 quando qualquer resposta HTTP chega; 1 se o tempo acabar.
set -u
url="${1:?uso: wait_for_http.sh <url> [timeout]}"
timeout="${2:-20}"
for _ in $(seq 1 "$timeout"); do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$url" 2>/dev/null)
  if [ "$code" != "000" ]; then
    echo "up ($code) $url"
    exit 0
  fi
  sleep 1
done
echo "timeout: nenhuma resposta de $url em ${timeout}s" >&2
exit 1
