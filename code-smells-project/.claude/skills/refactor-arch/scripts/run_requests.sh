#!/usr/bin/env bash
# Executa uma lista de requisições e imprime uma linha comparável por requisição:
#   METHOD PATH -> STATUS | <forma da resposta>
# A forma é: chaves do objeto JSON (ordenadas), descendo nos objetos e listas aninhados
# (ex.: {dados:{email,id,nome},sucesso}); para lista, a quantidade e a forma do primeiro
# item (ex.: [3]{id,nome}); para resposta que não é JSON, "text".
#
# Uso: run_requests.sh <base_url> <arquivo_de_requisicoes>
#
# Arquivo de requisições: uma por linha, campos separados por TAB:
#   METHOD<TAB>PATH[<TAB>BODY_JSON[<TAB>Header: valor]]
# Linhas vazias e começadas por # são ignoradas. Use "-" como BODY para não enviar corpo.
# Requer bash, curl e python3 ou node (só para ler o JSON).
set -u
base="${1:?uso: run_requests.sh <base_url> <arquivo>}"
file="${2:?uso: run_requests.sh <base_url> <arquivo>}"

if command -v python3 >/dev/null 2>&1; then
  shape() { python3 -c '
import json, sys
def shape(d, depth=0):
    if isinstance(d, dict):
        if depth >= 4:
            return "{" + ",".join(sorted(d)) + "}"
        return "{" + ",".join(k + (":" + shape(d[k], depth + 1) if isinstance(d[k], (dict, list)) else "") for k in sorted(d)) + "}"
    if isinstance(d, list):
        return "[%d]" % len(d) + (shape(d[0], depth + 1) if d and isinstance(d[0], (dict, list)) else "")
    return type(d).__name__
try:
    print(shape(json.loads(sys.stdin.read())))
except Exception:
    print("text")
'; }
elif command -v node >/dev/null 2>&1; then
  shape() { node -e '
const isObj = v => v !== null && typeof v === "object";
function shape(d, depth = 0) {
  if (Array.isArray(d)) return "[" + d.length + "]" + (d.length && isObj(d[0]) ? shape(d[0], depth + 1) : "");
  if (isObj(d)) {
    const ks = Object.keys(d).sort();
    if (depth >= 4) return "{" + ks.join(",") + "}";
    return "{" + ks.map(k => k + (isObj(d[k]) ? ":" + shape(d[k], depth + 1) : "")).join(",") + "}";
  }
  return typeof d;
}
let raw = "";
process.stdin.on("data", c => raw += c).on("end", () => {
  let d;
  try { d = JSON.parse(raw); } catch { console.log("text"); return; }
  console.log(shape(d));
});'; }
else
  echo "erro: precisa de python3 ou node para ler o JSON" >&2
  exit 2
fi

fail=0
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
while IFS=$'\t' read -r method path body header || [ -n "${method:-}" ]; do
  case "$method" in ''|'#'*) continue ;; esac
  args=(-s -o "$tmp" -w '%{http_code}' -X "$method")
  if [ -n "${body:-}" ] && [ "$body" != "-" ]; then
    args+=(-H 'Content-Type: application/json' --data-raw "$body")
  fi
  [ -n "${header:-}" ] && args+=(-H "$header")
  status=$(curl "${args[@]}" "$base$path")
  [ "$status" = "000" ] && fail=1
  echo "$method $path -> $status | $(shape < "$tmp")"
  body=""; header=""
done < "$file"
exit $fail
