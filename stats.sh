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

echo "Statystyki poleceń dla plików: $LOGPATTERN"
for CMD in "${COMMANDS[@]}"; do
  printf "%-18s: %d\n" "$CMD" "${COUNTS[$CMD]}"
done

if [ "$TOTAL" -gt 0 ]; then
  PROC=$(awk "BEGIN {printf \"%.2f\", (${COUNTS[/]} / $TOTAL) * 100}")
else
  PROC=0
fi

echo "-----------------------------"
echo "Suma wszystkich poleceń: $TOTAL"
echo "Procent '/': $PROC%"