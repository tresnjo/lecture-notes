"""Build lecture-graph.js: which earlier lectures each lecture builds on.
Runs before every render (pre-render in _quarto.yml)."""
import re, glob, json, os

PARTS = {"Noether's theorem": range(1, 100)}

# named concepts -> chapter that introduces them
CONCEPTS = [
    (1, "symmetries", r"[Ss]ymmetr"),
    (1, "invariance", r"[Ii]nvarian"),
    (1, "conservation laws", r"[Cc]onserv"),
    (1, "Noether's theorem", r"Noether"),
    (1, "covariance", r"[Cc]ovarian"),
    (2, "functionals", r"[Ff]unctional"),
    (2, "the Lagrangian", r"Lagrangian"),
    (2, "the action", r"\baction\b"),
    (2, "Fermat's principle", r"Fermat"),
    (2, "Hamilton's principle", r"Hamilton's principle"),
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
    part = next(p for p, r in PARTS.items() if n in r) 
    lec[n] = {"n": n, "title": title.group(1) if title else "Chapter %d" % n,
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
