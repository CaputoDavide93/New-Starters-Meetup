"""Every diagram in this repository is a drawn SVG, and has to stay one.

The README used to carry Mermaid, which GitHub renders with its own version and
its own theme, after decoding HTML entities, so what you see locally is not
what the page shows. What replaces it is `tools/gen_diagram.py`, which draws
each diagram twice, one file per colour scheme, served from a `<picture>`
element. The tests below are the obligations that come with that: the pictures
are what the generator draws, they reference files that exist, they carry
nothing GitHub strips, and Mermaid does not quietly come back.
"""

import importlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = sorted(ROOT.glob("*.md")) + sorted(ROOT.glob("docs/**/*.md"))
MERMAID = re.compile(r"^```mermaid", re.M)
MIN_DIAGRAMS = 1


def _generator():
    gen = ROOT / "tools" / "gen_diagram.py"
    assert gen.exists(), "tools/gen_diagram.py is missing"
    sys.path.insert(0, str(gen.parent))
    try:
        module = importlib.import_module("gen_diagram")
        return importlib.reload(module)
    finally:
        sys.path.remove(str(gen.parent))


def test_every_committed_svg_is_what_the_generator_draws():
    """A hand-edited SVG is a lie waiting to happen."""
    module = _generator()
    stale = []
    for name, fn in module.DIAGRAMS.items():
        for scheme in module.SCHEMES:
            path = ROOT / "docs" / "assets" / f"{name}-{scheme}.svg"
            if not path.exists():
                stale.append(f"{path.name} is missing")
            elif path.read_text(encoding="utf-8") != fn(scheme):
                stale.append(f"{path.name} differs from tools/gen_diagram.py")
    assert not stale, "re-run tools/gen_diagram.py rather than editing SVGs:\n  " + "\n  ".join(
        stale
    )


def test_every_picture_points_at_files_that_exist():
    """A `<picture>` with a wrong path shows the alt text and nothing else."""
    missing = []
    for page in PAGES:
        base = page.parent
        for ref in re.findall(r'(?:srcset|src)="([^"]+\.svg)"', page.read_text(encoding="utf-8")):
            if not (base / ref).exists():
                missing.append(f"{page.relative_to(ROOT)} -> {ref}")
    assert not missing, "a diagram reference does not resolve:\n  " + "\n  ".join(missing)


def test_every_diagram_offers_both_schemes_and_alt_text():
    """One scheme is half a diagram, and no alt text is none of one."""
    problems = []
    for page in PAGES:
        text = page.read_text(encoding="utf-8")
        for block in re.findall(r"<picture>.*?</picture>", text, re.S):
            where = page.relative_to(ROOT)
            if "prefers-color-scheme: dark" not in block:
                problems.append(f"{where}: a <picture> with no dark source")
            if not re.search(r'alt="[^"]{40,}"', block):
                problems.append(f"{where}: a <picture> with missing or thin alt text")
    assert not problems, "\n  " + "\n  ".join(problems)


def test_the_svgs_carry_nothing_github_will_strip():
    """GitHub sanitises SVG in markdown. The failure is silent: the diagram
    still renders, just without whatever was removed."""
    bad = []
    for path in sorted((ROOT / "docs" / "assets").glob("*.svg")):
        svg = path.read_text(encoding="utf-8")
        for banned in ("<script", "<style", "@import", "<foreignObject"):
            if banned in svg:
                bad.append(f"{path.name} contains {banned}")
    assert not bad, "GitHub strips these without saying so:\n  " + "\n  ".join(bad)


def test_mermaid_has_not_come_back():
    """The diagrams are drawn; a Mermaid block would be a second, drifting copy."""
    found = [
        str(p.relative_to(ROOT)) for p in PAGES if MERMAID.search(p.read_text(encoding="utf-8"))
    ]
    assert not found, "Mermaid block found in: " + ", ".join(found)


def test_there_are_diagrams_to_check():
    """A regex that silently matches nothing is not a test."""
    module = _generator()
    assert len(module.DIAGRAMS) >= MIN_DIAGRAMS
    pictures = sum(len(re.findall(r"<picture>", p.read_text(encoding="utf-8"))) for p in PAGES)
    assert pictures >= MIN_DIAGRAMS, f"only {pictures} <picture> blocks found across the docs"


def test_every_diagram_is_on_a_page():
    """A diagram nobody embeds is a diagram nobody updates."""
    module = _generator()
    text = "".join(p.read_text(encoding="utf-8") for p in PAGES)
    unused = [n for n in module.DIAGRAMS if f"assets/{n}-light.svg" not in text]
    assert not unused, "not embedded anywhere: " + ", ".join(unused)
