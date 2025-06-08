#!/bin/bash

if [ -z "$1" ]; then
  echo "Podaj nazwę pliku logów (np. daily lub latest)"
  exit 1
fi

LOGPATTERN="logs/$1*"
COMMANDS=(
  "/"
  "/set"
  "/remove"
  "/select"
  "/check"
  "/force set"
  "/force remove"
  "/force purge"
  "/setup toprole"
  "/setup select"
  "/vote"
)

TOTAL=0
declare -A COUNTS

for CMD in "${COMMANDS[@]}"; do
  COUNT=$(grep -o "issued bot command: $CMD" $LOGPATTERN 2>/dev/null | wc -l)
  COUNTS["$CMD"]=$COUNT
  TOTAL=$((TOTAL + COUNT))
done

echo "--------------------------------"
echo "Statystyki poleceń dla plików: $LOGPATTERN"
echo "--------------------------------"
ALL=${COUNTS[/]}
lines=()
for CMD in "${COMMANDS[@]}"; do
  if [ "$CMD" != "/" ] && [ "$ALL" -gt 0 ]; then
    PROC=$(awk "BEGIN {printf \"%.2f\", (${COUNTS[$CMD]} / $ALL) * 100}")
    lines+=("$(printf '%-15s| %5d | %5.2f%%' "$CMD" "${COUNTS[$CMD]}" "$PROC")")
  else
    lines+=("$(printf '%-15s| %5d |' "$CMD" "${COUNTS[$CMD]}")")
  fi
done

printf "%s\n" "${lines[@]}" | sort -t'|' -k2,2nr
echo "--------------------------------"