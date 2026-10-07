#!/usr/bin/env bash
# Garde-fou du setup : le candidat est-il dans sa copie ou dans le dépôt modèle ?
# Sortie sur une ligne :
#   TEMPLATE <url>  -> dépôt modèle, le setup doit refuser
#   NO_REMOTE       -> aucun remote configuré
#   COPY <url>      -> copie personnelle, le setup peut continuer
# Code de retour 0 dans tous les cas lisibles, 2 si git est absent.

set -u

TEMPLATE_REPO="klakenyuo/the-job-hunter"

if ! command -v git >/dev/null 2>&1; then
  echo "NO_GIT"
  exit 2
fi

url="$(git remote get-url origin 2>/dev/null || true)"

if [ -z "$url" ]; then
  echo "NO_REMOTE"
  exit 0
fi

# Normalise : minuscules, suppression du .git final et du / final.
norm="$(printf '%s' "$url" | tr '[:upper:]' '[:lower:]' | sed -e 's#\.git$##' -e 's#/$##')"

case "$norm" in
  *"github.com/${TEMPLATE_REPO}"|*"github.com:${TEMPLATE_REPO}")
    echo "TEMPLATE $url"
    ;;
  *)
    echo "COPY $url"
    ;;
esac
exit 0
