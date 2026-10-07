#!/usr/bin/env bash
# Hook SessionStart de Job Hunter : affiche le résumé du jour à l'ouverture de Claude Code.
# Ne bloque jamais l'ouverture : sans Python ou sans installation, il se tait ou guide.
root="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$root" 2>/dev/null && JH_ROOT="$root" "$root/scripts/jh" session-start 2>/dev/null || true
exit 0
