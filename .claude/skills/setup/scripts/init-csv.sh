#!/usr/bin/env bash
# Crée data/offers.csv avec l'en-tête du kit (UTF-8 avec BOM) sans écraser un fichier existant.
# Usage : init-csv.sh [chemin]   (défaut : data/offers.csv, relatif à la racine du dépôt)
# Sortie : CREATED <chemin> | EXISTS <chemin> | HEADER_MISMATCH <chemin>

set -u

path="${1:-data/offers.csv}"
header='id,title,company,location,contract,remote,salary,url,source,secondary_sources,published_at,detected_at,status,score,score_rationale,description'

root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$root" || exit 1

if [ -f "$path" ]; then
  # Compare la première ligne sans BOM ni retour chariot.
  first="$(head -n 1 "$path" | sed -e 's/^\xEF\xBB\xBF//' -e 's/\r$//')"
  if [ "$first" = "$header" ]; then
    echo "EXISTS $path"
  else
    echo "HEADER_MISMATCH $path"
  fi
  exit 0
fi

mkdir -p "$(dirname "$path")"
printf '\xEF\xBB\xBF%s\n' "$header" > "$path"
echo "CREATED $path"
