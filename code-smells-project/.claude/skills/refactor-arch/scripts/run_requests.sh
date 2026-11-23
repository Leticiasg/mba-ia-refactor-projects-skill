#!/usr/bin/env bash
# Executa uma lista de requisições e imprime uma linha comparável por requisição:
#   METHOD PATH -> STATUS | <forma da resposta>
# A forma é: chaves do objeto JSON (ordenadas); para lista, a quantidade e as chaves do
# primeiro item; para resposta que não é JSON, "text".
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
raw = sys.stdin.read()
try:
    d = json.loads(raw)
except Exception:
    print("text"); sys.exit()
if isinstance(d, dict):
    print("{" + ",".join(sorted(d)) + "}")
elif isinstance(d, list):
    first = d[0] if d and isinstance(d[0], dict) else None
    print("[%d]" % len(d) + ("{" + ",".join(sorted(first)) + "}" if first is not None else ""))
else:
    print(type(d).__name__)
'; }
elif command -v node >/dev/null 2>&1; then
  shape() { node -e '
let raw = "";
process.stdin.on("data", c => raw += c).on("end", () => {
  let d;
  try { d = JSON.parse(raw); } catch { console.log("text"); return; }
  const keys = o => "{" + Object.keys(o).sort().join(",") + "}";
  if (Array.isArray(d)) {
    const f = d[0];
    console.log("[" + d.length + "]" + (f && typeof f === "object" && !Array.isArray(f) ? keys(f) : ""));
  } else if (d && typeof d === "object") console.log(keys(d));
  else console.log(typeof d);
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
