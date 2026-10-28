#!/usr/bin/env bash
# fresh-ctx tester: run 1 non-streamed, run 2 streamed (silent), run 3 streamed (live + properly formatted)
set -euo pipefail

BASE="http://localhost:8080"
KEY="your-super-secret-key"
PROMPT="Write a story about a fox who opens a bakery."

hdrs=(-s -H "Content-Type: application/json" -H "Authorization: Bearer $KEY")

# ---------- run 1: one-shot, non-streamed ----------
echo "=== run 1: non-stream (fresh ctx, slot run1) ==="
body=$(jq -n --arg p "$PROMPT" '{
  prompt:$p, n_predict:-1, temperature:0,
  cache_prompt:false, stream:false, timings_per_token:true,
  slot_id:"run1"
}')
curl "${hdrs[@]}" "$BASE/completion" -d "$body" | jq '.timings'
curl -s -X DELETE "${hdrs[@]}" "$BASE/slots/run1" >/dev/null

# ---------- run 2: streamed, fresh ctx (silent/benchmarked) ----------
echo
echo "=== run 2: streamed (fresh ctx, slot run2) ==="
body=$(jq -n --arg p "$PROMPT" '{
  prompt:$p, n_predict:-1, temperature:0,
  cache_prompt:false, stream:true,
  slot_id:"run2"
}')

t0=$(date +%s.%3N)
chunks=$(curl -N "${hdrs[@]}" "$BASE/completion" -d "$body" | grep '^data: ' | sed 's/^data: //')
t1=$(date +%s.%3N)

n=$(printf '%s\n' "$chunks" | grep -v '\[DONE\]' | jq -s 'map(select(.content != "")) | length')
elapsed=$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.3f", b-a}')
tps=$(awk -v n="$n" -v e="$elapsed" 'BEGIN{printf "%.2f", n/e}')

echo "tokens:  $n"
echo "elapsed: ${elapsed}s (client-side, includes prefill)"
echo "tok/s:   $tps"
printf '%s\n' "$chunks" | grep -v '\[DONE\]' | tail -n 1 | jq -r '.timings // "draft stats: not present in stream chunks"'
curl -s -X DELETE "${hdrs[@]}" "$BASE/slots/run2" >/dev/null

# ---------- run 3: streamed live text + stats (properly formatted) ----------
echo
echo "=== run 3: streamed live output + stats (fresh ctx, slot run3) ==="
body=$(jq -n --arg p "$PROMPT" '{
  prompt:$p, n_predict:-1, temperature:0,
  cache_prompt:false, stream:true,
  slot_id:"run3"
}')

temp_file=$(mktemp)
t0=$(date +%s.%3N)

# Stream live output to terminal using -j (join-output) to prevent newline fragmentation
curl -N "${hdrs[@]}" "$BASE/completion" -d "$body" \
| tee "$temp_file" \
| grep '^data: ' \
| sed 's/^data: //' \
| grep -v '\[DONE\]' \
| jq --unbuffered -j '.content // empty'

t1=$(date +%s.%3N)
echo # Final newline after stream finishes

# Read back from temp file to calculate stats
all_chunks=$(grep '^data: ' "$temp_file" | sed 's/^data: //')
rm "$temp_file"

n=$(printf '%s\n' "$all_chunks" | grep -v '\[DONE\]' | jq -s 'map(select(.content != "")) | length')
elapsed=$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.3f", b-a}')
tps=$(awk -v n="$n" -v e="$elapsed" 'BEGIN{printf "%.2f", n/e}')

echo
echo "tokens:  $n"
echo "elapsed: ${elapsed}s (client-side, includes prefill)"
echo "tok/s:   $tps"
printf '%s\n' "$all_chunks" | grep -v '\[DONE\]' | tail -n 1 | jq -r '.timings // "draft stats: not present in stream chunks"'
curl -s -X DELETE "${hdrs[@]}" "$BASE/slots/run3" >/dev/null
