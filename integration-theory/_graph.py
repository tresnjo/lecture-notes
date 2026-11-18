"""Build lecture-graph.js: which earlier lectures each lecture builds on.
Runs before every render (pre-render in _quarto.yml)."""
import re, glob, json, os

PARTS = {"Measure Theory": range(1, 5), "Integration": range(5, 10),
         "Signed Measures and Differentiation": range(10, 16)}

# named concepts -> lecture that introduces them
CONCEPTS = [
    (1, "the π-λ theorem", r"Dynkin|\\pi\$?[-–]\$?\\lambda|\\pi\$?-system|\\lambda\$?-system"),
    (1, "Borel sets", r"Borel(?![–-]Cantelli)"),
    (2, "outer measure", r"outer measure|\\mu\^\{?\\star"),
    (2, "Carathéodory's theorem", r"Carath[eé]odory"),
    (2, "σ-finiteness", r"\\sigma\$?-finite|σ-finite"),
    (2, "complete measures", r"\bcomplete(?:ness)?\b"),
    (2, "almost everywhere", r"almost (?:every|sure)|\ba\.e\.|\ba\.s\."),
    (3, "the Vitali set", r"Vitali set|nonmeasurable"),
    (4, "premeasures", r"premeasure"),
    (4, "the Cantor set", r"Cantor"),
    (4, "distribution functions", r"distribution function|\bCDF"),
    (4, "the first Borel–Cantelli lemma", r"(?:first|1st) Borel|Borel[–-]Cantelli lemma \(\[Lemma 4"),
    (5, "measurable functions", r"measurable function"),
    (5, "simple functions", r"simple function"),
    (5, "Riemann integration", r"Riemann integra"),
    (6, "monotone convergence", r"[Mm]onotone convergence|\bMCT\b"),
    (6, "Fatou's lemma", r"Fatou"),
    (6, "dominated convergence", r"[Dd]ominated [Cc]onvergence|\bL?DCT\b"),
    (6, "the Lebesgue integral", r"Lebesgue integra"),
    (7, "convergence in measure", r"convergence in measure|converges in measure"),
    (7, "Egoroff's theorem", r"Egoroff|Egorov"),
    (7, "Markov's inequality", r"Markov"),
    (7, "Chebyshev's inequality", r"Chebyshev"),
    (7, "Hölder's inequality", r"H[öo]lder"),
    (8, "product measures", r"product measure|\\mu \\times \\nu"),
    (8, "Fubini–Tonelli", r"Fubini|Tonelli"),
    (9, "independence", r"independen"),
    (9, "laws of large numbers", r"law of large numbers|laws of large numbers"),
    (9, "the second Borel–Cantelli lemma", r"second Borel"),
    (10, "signed measures", r"signed measure"),
    (10, "the Hahn decomposition", r"Hahn"),
    (10, "the Jordan decomposition", r"Jordan"),
    (10, "mutual singularity", r"mutually singular|\\perp"),
    (11, "absolute continuity of measures", r"\\ll\b|absolutely continuous (?:with respect|w\.r\.t)"),
    (11, "the Radon–Nikodym theorem", r"Radon"),
    (11, "the Lebesgue decomposition", r"Lebesgue decomposition|Lebesgue's decomposition"),
    (12, "the covering lemma", r"covering lemma"),
    (12, "regularity", r"\bregular\b"),
    (13, "the maximal function", r"[Mm]aximal (?:function|theorem|inequality)|Hardy"),
    (13, "local integrability", r"locally integrable|L\^1_\{?\\?(?:text\{)?loc"),
    (14, "Lebesgue points", r"Lebesgue point"),
    (14, "the differentiation theorem", r"[Dd]ifferentiation theorem"),
    (14, "nicely shrinking sets", r"shrink(?:s)? nicely|nicely shrinking"),
]

def clean(t):
    t = re.sub(r"```\{=html\}.*?```", " ", t, flags=re.S)       # interactive figures
    t = re.sub(r"</?[a-zA-Z][a-zA-Z0-9-]*(?:\s[^<>\n]*)?>", " ", t)
    return t

files = sorted(glob.glob("lecture-*.qmd"))
lec, text = {}, {}
for f in files:
    n = int(re.search(r"lecture-(\d+)", f).group(1))
    raw = open(f, encoding="utf-8").read()
    title = re.search(r'^title:\s*"(.*)"', raw, re.M)
    part = next(p for p, r in PARTS.items() if n in r) if n <= 15 else ""
    lec[n] = {"n": n, "title": title.group(1) if title else "Lecture %d" % n,
              "href": f.replace(".qmd", ".html"), "part": part,
              "results": len(re.findall(r"^::: \{#r-", raw, re.M))}
    text[n] = clean(raw)

edges = {}   # (from later, to earlier) -> {"w": weight, "via": [...]}
def add(a, b, w, via=None):
    if a == b or a not in lec or b not in lec: return
    if a < b: a, b = b, a                   # always later -> earlier
    e = edges.setdefault((a, b), {"w": 0, "via": []})
    e["w"] += w
    if via and via not in e["via"]: e["via"].append(via)

for n, t in text.items():
    for m in re.findall(r"lecture-(\d+)\.qmd", t): add(n, int(m), 3)
    for m in re.findall(r"\]\(#r-(\d+)-\d+\)", t): add(n, int(m), 3)
    for m in re.findall(r"\b[Ll]ecture (\d{1,2})\b", t): add(n, int(m), 2)
    for home, name, rx in CONCEPTS:
        if home < n:
            k = len(re.findall(rx, t))
            if k: add(n, home, min(k, 4), name)

out = {"lectures": [lec[k] for k in sorted(lec)],
       "edges": [{"from": a, "to": b, "w": e["w"], "via": e["via"][:3]}
                 for (a, b), e in sorted(edges.items()) if e["w"] >= 2]}
with open("lecture-graph.js", "w", encoding="utf-8") as fh:
    fh.write("window.LECTURE_GRAPH = " + json.dumps(out, ensure_ascii=False) + ";\n")
print("lecture-graph.js: %d lectures, %d connections" % (len(out["lectures"]), len(out["edges"])))
