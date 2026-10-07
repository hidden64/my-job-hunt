"""Lecteur YAML minimal pour les fichiers du kit (config/kit.yml, config/candidate.yml).

Utilise PyYAML s'il est installé, sinon un analyseur maison qui couvre le sous-ensemble utilisé
par le kit : mappings et listes en style bloc, listes de mappings, listes et mappings en ligne
(`[a, b]`, `{a: 1}`), chaînes entre guillemets simples ou doubles, entiers, décimaux, booléens,
`null`/`~`, commentaires `#`. Les chaînes multi-lignes (`|`, `>`) ne sont pas prises en charge :
les fichiers du kit n'en utilisent pas.
"""
import re

try:  # pragma: no cover - dépend de l'environnement
    import yaml as _pyyaml  # type: ignore
except Exception:  # pragma: no cover
    _pyyaml = None


class YamlError(ValueError):
    pass


def load(text, force_mini=False):
    if _pyyaml is not None and not force_mini:
        data = _pyyaml.safe_load(text)
        return {} if data is None else data
    return _MiniParser(text).parse()


def load_file(path, force_mini=False):
    with open(path, encoding="utf-8-sig") as f:
        return load(f.read(), force_mini=force_mini)


# --------------------------------------------------------------------------------------------
# Analyseur minimal
# --------------------------------------------------------------------------------------------

def _strip_comment(line):
    """Retire un commentaire en fin de ligne, hors guillemets."""
    out, quote = [], None
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            continue
        if ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


_INT = re.compile(r"^[-+]?\d+$")
_FLOAT = re.compile(r"^[-+]?(\d+\.\d*|\.\d+|\d+(\.\d*)?[eE][-+]?\d+)$")


def _scalar(tok):
    tok = tok.strip()
    if tok == "":
        return None
    if tok[0] in "\"'":
        if len(tok) < 2 or tok[-1] != tok[0]:
            raise YamlError("chaîne non fermée : %s" % tok)
        body = tok[1:-1]
        if tok[0] == '"':
            body = (body.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t")
                    .replace("\\\\", "\\"))
        else:
            body = body.replace("''", "'")
        return body
    if tok[0] == "[":
        return _flow_list(tok)
    if tok[0] == "{":
        return _flow_map(tok)
    low = tok.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "~"):
        return None
    if _INT.match(tok):
        try:
            return int(tok)
        except ValueError:
            pass
    if _FLOAT.match(tok):
        try:
            return float(tok)
        except ValueError:
            pass
    return tok


def _split_flow(body):
    parts, depth, quote, cur = [], 0, None, []
    for ch in body:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def _flow_list(tok):
    if not tok.endswith("]"):
        raise YamlError("liste en ligne non fermée : %s" % tok)
    return [_scalar(p) for p in _split_flow(tok[1:-1])]


def _flow_map(tok):
    if not tok.endswith("}"):
        raise YamlError("mapping en ligne non fermé : %s" % tok)
    out = {}
    for p in _split_flow(tok[1:-1]):
        k, sep, v = _split_key(p.strip())
        if not sep:
            raise YamlError("entrée invalide dans un mapping en ligne : %s" % p)
        out[k] = _scalar(v)
    return out


def _split_key(text):
    """Sépare `clé: valeur` en respectant les guillemets. Renvoie (clé, ':' ou '', valeur)."""
    quote = None
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            continue
        if ch == ":" and (i + 1 == len(text) or text[i + 1] in " \t"):
            key = text[:i].strip()
            if key and key[0] in "\"'":
                key = _scalar(key)
            return key, ":", text[i + 1:].strip()
    return text, "", ""


class _MiniParser:
    def __init__(self, text):
        self.lines = []
        for raw in text.replace("\t", "    ").splitlines():
            if raw.strip() in ("---", "..."):
                continue
            line = _strip_comment(raw)
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip(" "))
            self.lines.append((indent, line.strip()))
        self.pos = 0

    def parse(self):
        if not self.lines:
            return {}
        value = self._block(self.lines[0][0])
        if self.pos != len(self.lines):
            raise YamlError("indentation inattendue près de : %s" % self.lines[self.pos][1])
        return value

    def _block(self, indent):
        if self.lines[self.pos][1].startswith("- ") or self.lines[self.pos][1] == "-":
            return self._list(indent)
        return self._map(indent)

    def _map(self, indent):
        out = {}
        while self.pos < len(self.lines):
            ind, text = self.lines[self.pos]
            if ind < indent:
                break
            if ind > indent:
                raise YamlError("indentation inattendue près de : %s" % text)
            if text.startswith("- "):
                break
            key, sep, rest = _split_key(text)
            if not sep:
                raise YamlError("ligne sans « clé: valeur » : %s" % text)
            self.pos += 1
            if rest:
                out[key] = _scalar(rest)
            elif self.pos < len(self.lines) and self.lines[self.pos][0] > indent:
                out[key] = self._block(self.lines[self.pos][0])
            elif (self.pos < len(self.lines) and self.lines[self.pos][0] == indent
                  and self.lines[self.pos][1].startswith("- ")):
                out[key] = self._list(indent)
            else:
                out[key] = None
        return out

    def _list(self, indent):
        out = []
        while self.pos < len(self.lines):
            ind, text = self.lines[self.pos]
            if ind != indent or not (text.startswith("- ") or text == "-"):
                if ind > indent:
                    raise YamlError("indentation inattendue près de : %s" % text)
                break
            item = text[1:].strip()
            self.pos += 1
            if item == "":
                if self.pos < len(self.lines) and self.lines[self.pos][0] > indent:
                    out.append(self._block(self.lines[self.pos][0]))
                else:
                    out.append(None)
                continue
            key, sep, rest = _split_key(item)
            if sep and not item.startswith(("[", "{", "'", '"')):
                # Élément de liste qui est un mapping : « - clé: valeur » puis clés suivantes.
                child_indent = indent + 2
                # Réinjecte la première paire comme une ligne au niveau des clés suivantes.
                if self.pos < len(self.lines) and self.lines[self.pos][0] > indent:
                    child_indent = self.lines[self.pos][0]
                self.lines.insert(self.pos, (child_indent, item))
                out.append(self._map(child_indent))
            else:
                out.append(_scalar(item))
        return out
