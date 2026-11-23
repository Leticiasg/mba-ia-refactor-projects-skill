#!/usr/bin/env bash
# Compara a saída de run_requests.sh antes e depois da refatoração, linha a linha.
# Uso: compare_results.sh <antes.txt> <depois.txt>
# Imprime as linhas diferentes e um resumo "<iguais>/<total> requests match baseline".
# Saída 0 se tudo bate; 1 se houver diferença (avalie cada uma contra as exceções de segurança).
set -u
before="${1:?uso: compare_results.sh <antes> <depois>}"
after="${2:?uso: compare_results.sh <antes> <depois>}"
total=$(wc -l < "$before" | tr -d ' ')
if [ "$total" != "$(wc -l < "$after" | tr -d ' ')" ]; then
  echo "quantidade de linhas diferente: antes=$total depois=$(wc -l < "$after" | tr -d ' ')" >&2
  exit 1
fi
same=0; n=0
while IFS= read -r a && IFS= read -r b <&3; do
  n=$((n + 1))
  if [ "$a" = "$b" ]; then
    same=$((same + 1))
  else
    echo "DIFF #$n"
    echo "  antes:  $a"
    echo "  depois: $b"
  fi
done < "$before" 3< "$after"
echo "$same/$total requests match baseline"
[ "$same" = "$total" ]
