"""Normalisation des offres à l'entrée (docs/STORAGE.md) et calcul de la clé de dédoublonnage."""
import hashlib
import html
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

FIELDS = ["id", "title", "company", "location", "contract", "remote", "salary", "url", "source",
          "secondary_sources", "published_at", "detected_at", "status", "score", "score_rationale",
          "description"]

SOURCES = {"france_travail", "wttj", "linkedin", "indeed", "hellowork", "apec", "jobteaser",
           "glassdoor", "test"}
CONTRACTS = {"cdi", "cdd", "alternance", "stage", "freelance", "interim", "autre"}
REMOTES = {"none", "hybrid", "full", "unknown"}
STATUSES = {"new", "seen", "applied", "rejected", "ignored"}

DESCRIPTION_MAX = 2000


def strip_accents(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def clean_text(value):
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace(" ", " ").replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _fold(text):
    return strip_accents(clean_text(text)).lower()


# --- contrat ---------------------------------------------------------------------------------

_CONTRACT_RULES = [
    ("alternance", r"alternan|apprenti|contrat pro|professionnalisation|work[- ]study"),
    ("stage", r"\bstage|intern(ship)?\b|stagiaire"),
    ("interim", r"interim|travail temporaire|\bmis\b|mission d.interim|temporary"),
    ("freelance", r"freelance|independant|\bportage|\bmission\b|\bsai\b|profession liberale|contractor|liberal"),
    ("cdd", r"\bcdd\b|duree determinee|fixed[- ]term|\bcontract\b|saisonnier|\bsaisonn"),
    ("cdi", r"\bcdi\b|duree indeterminee|permanent|full[- ]time|temps plein|part[- ]time"),
]


def normalize_contract(value):
    v = _fold(value)
    if not v:
        return "autre"
    if v in CONTRACTS:
        return v
    for code, pattern in _CONTRACT_RULES:
        if re.search(pattern, v):
            return code
    return "autre"


# --- télétravail -----------------------------------------------------------------------------

def normalize_remote(value, *more_text):
    v = _fold(" ".join([str(value or "")] + [str(t or "") for t in more_text]))
    if not v.strip():
        return "unknown"
    if v.strip() in REMOTES:
        return v.strip()
    if re.search(r"teletravail (total|complet|integral)|full[- ]?remote|100 ?% (teletravail|remote)|"
                 r"entierement a distance|remote only|fully remote|teletravail 100", v):
        return "full"
    if re.search(r"pas de teletravail|sans teletravail|teletravail non|on[- ]site|sur site uniquement|"
                 r"presentiel uniquement|100 ?% presentiel|aucun teletravail", v):
        return "none"
    if re.search(r"hybrid|hybride|teletravail (partiel|occasionnel|possible|ponctuel|regulier)|"
                 r"\d ?jours? (de )?teletravail|teletravail \d|remote partiel|partial remote|"
                 r"\bteletravail\b|\bremote\b", v):
        return "hybrid"
    if re.search(r"sur site|presentiel", v):
        return "none"
    return "unknown"


# --- url -------------------------------------------------------------------------------------

_TRACKING = re.compile(r"^(utm_.*|ref|refid|trk|trackingid|src|from|position|pagenum|tk|fbclid|gclid|"
                       r"xtor|origin|at_.*)$", re.I)


def normalize_url(url):
    url = clean_text(url)
    if not url:
        return ""
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not _TRACKING.match(k)]
    netloc = parts.netloc.lower()
    return urlunsplit((parts.scheme.lower() or "https", netloc, parts.path, urlencode(query), ""))


def url_key(url):
    """Forme canonique d'une URL pour comparer deux URL (sans schéma, sans www, sans / final)."""
    u = normalize_url(url)
    parts = urlsplit(u)
    netloc = re.sub(r"^(www\.|fr\.|m\.)", "", parts.netloc)
    path = parts.path.rstrip("/")
    q = ("?" + parts.query) if parts.query else ""
    return netloc + path + q


# --- clé de dédoublonnage (E3.4) -------------------------------------------------------------

_GENDER = re.compile(r"\(?\b(h ?/ ?f|f ?/ ?h|m ?/ ?f|f ?/ ?m|h ?- ?f|f ?- ?h|m ?/ ?w ?/ ?d|"
                     r"h ?/ ?f ?/ ?x|f ?/ ?h ?/ ?x|x ?/ ?f ?/ ?h|homme ?/ ?femme|femme ?/ ?homme)\b\)?")
_LEGAL = re.compile(r"\b(sas|sasu|sa|sarl|eurl|sci|snc|inc|ltd|llc|gmbh|plc|bv|nv|spa|srl|"
                    r"s\.a\.s|s\.a\.r\.l|s\.a)\b\.?")


def norm_title(title):
    t = _fold(title)
    t = _GENDER.sub(" ", t)
    t = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", t)     # niveaux et références entre parenthèses
    t = re.sub(r"[^a-z0-9+#]+", " ", t)              # garde c++ / c#
    t = re.sub(r"\b(h f|f h|hf|fh)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def norm_company(company):
    c = _fold(company)
    c = _LEGAL.sub(" ", c)
    c = re.sub(r"[^a-z0-9]+", " ", c)
    c = re.sub(r"\s+", " ", c).strip()
    # « Lindab France » et « Lindab » : même entreprise (filiale française du même nom).
    c = re.sub(r"(?<=\S) (france|fr)$", "", c)
    return c


def norm_city(location):
    loc = _fold(location)
    if not loc or loc in ("inconnue", "unknown"):
        return ""
    if re.search(r"teletravail total|full remote|remote", loc) and not re.search(r"[a-z]{3,} ?\(", loc):
        return "remote"
    # France Travail : « 69 - Villeurbanne » ; HelloWork : « Lyon 3e - 69 » ; LinkedIn : « Lyon, Auvergne-... »
    m = re.match(r"^\s*(\d{2,3}|2a|2b)\s*-\s*(.+)$", loc)
    if m:
        loc = m.group(2)
    loc = re.split(r"[(,]| - | – ", loc)[0]
    loc = re.sub(r"\b\d+\s*(e|er|eme|ème)\b", " ", loc)           # arrondissements
    loc = re.sub(r"\b(arrondissement|cedex|france|metropole)\b", " ", loc)
    loc = re.sub(r"\d+", " ", loc)
    loc = re.sub(r"\bst\b", "saint", loc)
    loc = re.sub(r"\bste\b", "sainte", loc)
    loc = re.sub(r"[^a-z]+", " ", loc)
    return re.sub(r"\s+", " ", loc).strip()


def offer_id(company, title, location):
    key = "%s|%s|%s" % (norm_company(company), norm_title(title), norm_city(location))
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


# --- description -----------------------------------------------------------------------------

def truncate_description(text, limit=DESCRIPTION_MAX):
    text = clean_text(text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if end > limit * 0.6:
        return cut[: end + 1]
    return cut.rstrip() + "…"


# --- offre complète --------------------------------------------------------------------------

class InvalidOffer(ValueError):
    pass


def normalize_offer(raw, source):
    """Transforme une offre brute d'une source en offre au schéma. Lève InvalidOffer si un champ
    obligatoire manque. Ne pose ni id, ni detected_at, ni status, ni score : c'est le stockage."""
    if not isinstance(raw, dict):
        raise InvalidOffer("offre qui n'est pas un objet")
    title = clean_text(raw.get("title"))
    url = normalize_url(raw.get("url"))
    if not title:
        raise InvalidOffer("titre absent")
    if not url or not url.startswith("http"):
        raise InvalidOffer("url absente ou invalide")
    company = clean_text(raw.get("company")) or "inconnue"
    location = clean_text(raw.get("location")) or "inconnue"
    description = truncate_description(raw.get("description") or "")
    contract = normalize_contract(raw.get("contract") or title)
    remote = normalize_remote(raw.get("remote"), "" if raw.get("remote") else description)
    published = clean_text(raw.get("published_at"))
    if published and not re.match(r"^\d{4}-\d{2}-\d{2}$", published):
        published = published[:10] if re.match(r"^\d{4}-\d{2}-\d{2}", published) else ""
    return {
        "title": title,
        "company": company,
        "location": location,
        "contract": contract,
        "remote": remote,
        "salary": clean_text(raw.get("salary")),
        "url": url,
        "source": source,
        "published_at": published,
        "description": description,
    }
