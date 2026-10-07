"""Export Excel (.xlsx) sans dépendance : un classeur avec une feuille « Offres » (en-têtes figés,
filtres automatiques, largeurs ajustées, score coloré) et une feuille « Résumé »."""
import zipfile
from collections import Counter
from xml.sax.saxutils import escape

HEADERS_FR = {
    "score": "Score", "title": "Titre", "company": "Entreprise", "location": "Lieu", "contract": "Contrat",
    "remote": "Télétravail", "salary": "Salaire", "status": "Statut", "source": "Source",
    "published_at": "Publiée le", "detected_at": "Détectée le", "url": "Lien",
    "score_rationale": "Pourquoi ce score", "secondary_sources": "Vue aussi sur", "id": "Identifiant",
}
COLUMNS = ["score", "title", "company", "location", "contract", "remote", "salary", "status", "source",
           "published_at", "detected_at", "url", "score_rationale", "secondary_sources", "id"]
WIDTHS = {"score": 8, "title": 40, "company": 24, "location": 20, "contract": 11, "remote": 12, "salary": 20,
          "status": 11, "source": 14, "published_at": 12, "detected_at": 20, "url": 50, "score_rationale": 60,
          "secondary_sources": 30, "id": 18}


def _col(n):
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _cell(ref, value, style=0, number=False):
    if value is None or value == "":
        return '<c r="%s" s="%d"/>' % (ref, style) if style else ""
    if number:
        return '<c r="%s" s="%d"><v>%s</v></c>' % (ref, style, value)
    text = escape(str(value)).replace("\n", "&#10;")
    return '<c r="%s" s="%d" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, style, text)


# styles : 0 normal, 1 en-tête, 2 score vert (>= seuil), 3 score orange (>= seuil - 20), 4 score gris
STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>
<fills count="6"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFC6EFCE"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFFFEB9C"/><bgColor indexed="64"/></patternFill></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FFEDEDED"/><bgColor indexed="64"/></patternFill></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="5">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/>
<xf numFmtId="0" fontId="0" fillId="3" borderId="0" xfId="0" applyFill="1"/>
<xf numFmtId="0" fontId="0" fillId="4" borderId="0" xfId="0" applyFill="1"/>
<xf numFmtId="0" fontId="0" fillId="5" borderId="0" xfId="0" applyFill="1"/>
</cellXfs>
<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""


def _sheet(rows_xml, cols_xml="", freeze=False, autofilter=None):
    pane = ('<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" '
            'state="frozen"/></sheetView></sheetViews>') if freeze else '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
    af = '<autoFilter ref="%s"/>' % autofilter if autofilter else ""
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">%s%s<sheetData>%s</sheetData>%s</worksheet>'
            % (pane, cols_xml, "".join(rows_xml), af))


def export(rows, path, threshold):
    # Feuille Offres
    rows_xml = ['<row r="1">%s</row>' % "".join(_cell("%s1" % _col(i), HEADERS_FR[c], 1) for i, c in enumerate(COLUMNS))]
    for n, r in enumerate(rows, start=2):
        cells = []
        for i, c in enumerate(COLUMNS):
            ref = "%s%d" % (_col(i), n)
            v = r.get(c, "")
            if c == "score":
                if str(v).strip():
                    s = int(v)
                    style = 2 if s >= threshold else (3 if s >= threshold - 20 else 4)
                    cells.append(_cell(ref, s, style, number=True))
                continue
            cells.append(_cell(ref, v))
        rows_xml.append('<row r="%d">%s</row>' % (n, "".join(cells)))
    cols = "<cols>%s</cols>" % "".join('<col min="%d" max="%d" width="%d" customWidth="1"/>' % (i + 1, i + 1, WIDTHS[c])
                                         for i, c in enumerate(COLUMNS))
    last = "%s%d" % (_col(len(COLUMNS) - 1), max(1, len(rows) + 1))
    offers_sheet = _sheet(rows_xml, cols, freeze=True, autofilter="A1:" + last)

    # Feuille Résumé
    summary = [("Offres au total", len(rows))]
    def bucket(r):
        if not str(r.get("score", "")).strip():
            return "non notées"
        s = int(r["score"])
        return "≥ %d (seuil)" % threshold if s >= threshold else ("50 à %d" % (threshold - 1) if s >= 50 else "< 50")
    blocks = [("Par source", Counter(r.get("source", "") for r in rows)),
              ("Par statut", Counter(r.get("status", "") for r in rows)),
              ("Par tranche de score", Counter(bucket(r) for r in rows))]
    srows, n = [], 1
    for label, value in summary:
        srows.append('<row r="%d">%s%s</row>' % (n, _cell("A%d" % n, label, 1), _cell("B%d" % n, value, 1, number=True)))
        n += 2
    for title, counter in blocks:
        srows.append('<row r="%d">%s</row>' % (n, _cell("A%d" % n, title, 1)))
        n += 1
        for k, v in counter.most_common():
            srows.append('<row r="%d">%s%s</row>' % (n, _cell("A%d" % n, k or "–"), _cell("B%d" % n, v, number=True)))
            n += 1
        n += 1
    summary_sheet = _sheet(srows, '<cols><col min="1" max="1" width="28" customWidth="1"/><col min="2" max="2" width="10" customWidth="1"/></cols>')

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                   '<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   '</Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   '</Relationships>')
        z.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                   '<sheets><sheet name="Offres" sheetId="1" r:id="rId1"/><sheet name="Résumé" sheetId="2" r:id="rId2"/></sheets>'
                   '<definedNames><definedName name="_xlnm._FilterDatabase" localSheetId="0" hidden="1">Offres!$A$1:$%s$%d</definedName></definedNames>'
                   '</workbook>' % (_col(len(COLUMNS) - 1), max(1, len(rows) + 1)))
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                   '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>'
                   '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                   '</Relationships>')
        z.writestr("xl/styles.xml", STYLES)
        z.writestr("xl/worksheets/sheet1.xml", offers_sheet)
        z.writestr("xl/worksheets/sheet2.xml", summary_sheet)
    return path
