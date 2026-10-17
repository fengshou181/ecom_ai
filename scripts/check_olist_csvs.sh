#!/bin/bash
cd /mnt/e/ecom_ai/data/raw/olist
for f in *.csv; do
  echo "=== $f ==="
  head -1 "$f"
  wc -l "$f"
  echo ""
done
