#!/usr/bin/env bash
# Para o processo que está escutando numa porta e confirma que ela ficou livre.
# Use no lugar de pkill pelo nome do comando, que falha quando o processo foi
# iniciado com caminho relativo e deixa a versão antiga respondendo.
# Uso: stop_port.sh <porta> [timeout_segundos=10]
# Saída 0 com a porta livre; 1 se ainda houver processo escutando no fim do tempo.
set -u
port="${1:?uso: stop_port.sh <porta> [timeout]}"
timeout="${2:-10}"
pids() { lsof -t -i ":$port" -sTCP:LISTEN 2>/dev/null; }
p=$(pids)
if [ -z "$p" ]; then
  echo "free: porta $port já estava livre"
  exit 0
fi
kill $p 2>/dev/null
for _ in $(seq 1 "$timeout"); do
  sleep 1
  [ -z "$(pids)" ] && { echo "stopped: porta $port livre (pid $(echo $p | tr '\n' ' '))"; exit 0; }
done
kill -9 $(pids) 2>/dev/null
sleep 1
if [ -z "$(pids)" ]; then
  echo "stopped: porta $port livre após kill -9"
  exit 0
fi
echo "erro: ainda há processo na porta $port: $(pids | tr '\n' ' ')" >&2
exit 1
