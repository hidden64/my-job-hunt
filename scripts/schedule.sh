#!/usr/bin/env bash
# Planifie les collectes Job Hunter sur macOS et Linux avec cron, en lançant Claude Code en mode
# non interactif (`claude -p`) dans ce dépôt aux heures de config/kit.yml.
#
# Usage :
#   scripts/schedule.sh install 08:00 13:00 19:00   # remplace les entrées Job Hunter existantes
#   scripts/schedule.sh list                         # affiche les entrées Job Hunter
#   scripts/schedule.sh remove                       # supprime les entrées Job Hunter
#
# Option : JH_CHROME=1 ajoute --chrome (sources navigateur) si l'extension Claude in Chrome est
# installée et que la collecte navigateur a été testée à la main.
# Sortie : JSON sur une ligne.
set -u

MARK="# job-hunter:$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROMPT="Lance une collecte Job Hunter."

json_err() { printf '{"ok": false, "error": "%s", "message": "%s"}\n' "$1" "$2"; exit 1; }

command -v crontab >/dev/null 2>&1 || json_err "no_crontab" "crontab introuvable sur cette machine : utilise les routines de l'application Claude Code."

current() { crontab -l 2>/dev/null || true; }

case "${1:-}" in
  list)
    lines="$(current | grep -F "$MARK" || true)"
    n=$(printf '%s' "$lines" | grep -c . || true)
    printf '{"ok": true, "count": %s, "entries": %s}\n' "$n" "$(printf '%s\n' "$lines" | python3 -c 'import json,sys;print(json.dumps([l for l in sys.stdin.read().splitlines() if l]))' 2>/dev/null || echo '[]')"
    ;;
  remove)
    keep="$(current | grep -vF "$MARK")"
    printf '%s\n' "$keep" | sed '/^$/d' | crontab - || json_err "crontab" "impossible de modifier la crontab"
    echo '{"ok": true, "message": "Collectes planifiées supprimées."}'
    ;;
  install)
    shift
    [ "$#" -ge 1 ] || json_err "no_times" "indique au moins une heure, ex. 08:00"
    CLAUDE_BIN="$(command -v claude || true)"
    [ -n "$CLAUDE_BIN" ] || json_err "no_claude" "commande claude introuvable dans le PATH : installe Claude Code en ligne de commande (https://code.claude.com)."
    extra=""
    [ "${JH_CHROME:-0}" = "1" ] && extra=" --chrome"
    new="$(current | grep -vF "$MARK")"
    for t in "$@"; do
      case "$t" in
        [0-2][0-9]:[0-5][0-9]) ;;
        *) json_err "bad_time" "heure invalide : $t (format HH:MM)";;
      esac
      h=$((10#${t%%:*})); m=$((10#${t##*:}))
      [ "$h" -le 23 ] || json_err "bad_time" "heure invalide : $t"
      line="$m $h * * * cd \"$ROOT\" && PATH=\"$(dirname "$CLAUDE_BIN"):/usr/local/bin:/usr/bin:/bin\" \"$CLAUDE_BIN\" -p \"$PROMPT\" --permission-mode acceptEdits$extra >> \"$ROOT/data/runs/work/cron.log\" 2>&1 $MARK"
      new="$(printf '%s\n%s' "$new" "$line")"
    done
    mkdir -p "$ROOT/data/runs/work"
    printf '%s\n' "$new" | sed '/^$/d' | crontab - || json_err "crontab" "impossible d'écrire la crontab"
    printf '{"ok": true, "times": "%s", "claude": "%s", "chrome": %s, "log": "data/runs/work/cron.log"}\n' "$*" "$CLAUDE_BIN" "$([ -n "$extra" ] && echo true || echo false)"
    ;;
  *)
    sed -n '2,13p' "$0"
    ;;
esac
