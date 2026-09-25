#!/usr/bin/env python3
"""Draw every diagram in this repository as SVG, one file per colour scheme.

  docs/assets/<name>-light.svg
  docs/assets/<name>-dark.svg

This replaces the Mermaid flowchart the README used to carry. GitHub renders
Mermaid with its own version and its own theme, decodes HTML entities before
parsing, and lays the graph out however it likes. Drawn here, each picture says
one thing and stays put.

**GitHub sanitises SVG in markdown**, so there is no <style>, no <script>, no
web font and no <foreignObject>. Everything is a presentation attribute and the
type is a system stack. Each pair is served from one <picture>, which GitHub
switches on prefers-color-scheme.

Layout is explicit rather than solved: the diagrams are small enough that
placing them by hand is cheaper than a layout engine nobody can predict.

House rules: a slate scale, a single accent on the one thing that matters in
each picture, drawn icons rather than emoji, monospace for anything that is
literally typed (paths, endpoints, env vars), a footer sentence under every
diagram, and text contrast at or above 4.5:1 in both schemes.

Run it after changing a diagram; tests/test_diagrams.py fails if the committed
SVGs and this file disagree.
"""
from __future__ import annotations

import pathlib
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parents[1]
SANS = "system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"

SCHEMES = {
    "light": dict(card="#ffffff", border="#d8dee4", title="#0f172a", sub="#5b6673",
                  accent="#2b59c3", on_accent="#ffffff", soft="#f1f4f9",
                  line="#94a3b8", rule="#e6e9ee", chip="#475569",
                  warn="#9a3412", warn_soft="#fff4ed", group="#f7f9fb"),
    "dark":  dict(card="#161b22", border="#30363d", title="#e6edf3", sub="#9aa4b0",
                  accent="#4c7ef3", on_accent="#ffffff", soft="#1b2230",
                  line="#6b7684", rule="#232a33", chip="#aeb7c2",
                  warn="#ffa657", warn_soft="#2a1d14", group="#11151b"),
}

# Stroked glyphs on a 24x24 grid, drawn rather than typed.
ICONS = {
    "user":     "M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7",
    "bolt":     "M13 2 4 14h7l-1 8 9-12h-7z",
    "key":      "M8 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M12 12h9 M18 12v3 M15 12v2",
    "users":    "M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6 "
                "M16 4.3a3.5 3.5 0 0 1 0 6.4 M18 14.2c2.1.7 3.5 2.8 3.5 5.8",
    "database": "M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3z M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6 "
                "M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3",
    "calendar": "M4 6h16v15H4z M4 10h16 M8 3v5 M16 3v5 M8 14h2 M14 14h2 M8 17.5h2",
    "chat":     "M4 5h16v11H9l-5 4z M8 9h8 M8 12h5",
}


class Canvas:
    """Parts plus a size. No layout engine, on purpose."""

    def __init__(self, w: int, h: int, scheme: str, label: str) -> None:
        self.w, self.h, self.c, self.label = w, h, SCHEMES[scheme], label
        self.parts: list[str] = []

    def add(self, *svg: str) -> "Canvas":
        self.parts.extend(svg)
        return self

    # ── primitives ────────────────────────────────────────────────────────
    def icon(self, name, x, y, colour, size=21):
        s = size / 24
        return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.4f})" fill="none" '
                f'stroke="{colour}" stroke-width="1.7" stroke-linecap="round" '
                f'stroke-linejoin="round"><path d="{ICONS[name]}"/></g>')

    def text(self, x, y, s, *, size=13, colour=None, font=None, weight=None,
             anchor="start", opacity=None):
        c = colour or self.c["sub"]
        extra = (f' font-weight="{weight}"' if weight else "") + \
                (f' opacity="{opacity}"' if opacity else "")
        return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font or SANS}" '
                f'font-size="{size}" fill="{c}" text-anchor="{anchor}"{extra}>'
                f'{escape(s)}</text>')

    def box(self, x, y, w, h, title, subs=(), *, icon=None, tone="plain", rx=10):
        c = self.c
        fill, edge, tt = c["card"], c["border"], c["title"]
        st, op = c["sub"], ""
        if tone == "accent":
            fill = edge = c["accent"]; tt = st = c["on_accent"]; op = "0.85"
        elif tone == "soft":
            fill = c["soft"]
        elif tone == "warn":
            fill, edge, tt, st = c["warn_soft"], c["warn"], c["warn"], c["warn"]
        out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
               f'stroke="{edge}" stroke-width="1"/>']
        tx = x + 16
        ty = y + (28 if subs else h / 2 + 5)
        if icon:
            out.append(self.icon(icon, x + 16, y + (13 if subs else h / 2 - 10), tt))
            tx = x + 47
        out.append(self.text(tx, ty, title, size=15 if subs else 14,
                             colour=tt, weight="600"))
        for i, s in enumerate(subs):
            out.append(self.text(x + 16, y + 52 + i * 18, s, size=12.5,
                                 colour=st, opacity=op or None))
        return "".join(out)

    def diamond(self, cx, cy, w, h, lines):
        c = self.c
        pts = f"{cx},{cy - h/2} {cx + w/2},{cy} {cx},{cy + h/2} {cx - w/2},{cy}"
        out = [f'<polygon points="{pts}" fill="{c["soft"]}" stroke="{c["border"]}" '
               f'stroke-width="1"/>']
        n = len(lines)
        for i, s in enumerate(lines):
            out.append(self.text(cx, cy - (n - 1) * 7 + i * 14 + 4, s, size=12,
                                 colour=c["title"], anchor="middle"))
        return "".join(out)

    def pill(self, cx, cy, text, *, tone="plain", pad=16, size=13):
        c = self.c
        w = len(text) * size * 0.58 + pad * 2
        h = 32
        fill, edge, col = c["card"], c["border"], c["title"]
        if tone == "accent":
            fill = edge = c["accent"]; col = c["on_accent"]
        elif tone == "soft":
            fill = c["soft"]
        return (f'<rect x="{cx - w/2:.1f}" y="{cy - h/2}" width="{w:.1f}" height="{h}" '
                f'rx="{h/2}" fill="{fill}" stroke="{edge}" stroke-width="1"/>'
                + self.text(cx, cy + 4.5, text, size=size, colour=col, anchor="middle",
                            weight="500")), w

    def edge(self, pts, *, label=None, dash=False, both=False, label_at=0.5,
             label_dy=-9, label_anchor="middle", mono=True):
        c = self.c
        d = ' stroke-dasharray="5 4"' if dash else ""
        path = " ".join(f"{x},{y}" for x, y in pts)
        out = [f'<polyline points="{path}" fill="none" stroke="{c["line"]}" '
               f'stroke-width="1.5"{d} marker-end="url(#a)"'
               + (' marker-start="url(#a)"' if both else "") + "/>"]
        if label:
            (x1, y1), (x2, y2) = pts[0], pts[-1]
            lx = x1 + (x2 - x1) * label_at
            ly = y1 + (y2 - y1) * label_at
            out.append(self.text(lx, ly + label_dy, label, size=11.5,
                                 colour=c["chip"], font=MONO if mono else SANS,
                                 anchor=label_anchor))
        return "".join(out)

    def group(self, x, y, w, h, title):
        c = self.c
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" '
                f'fill="{c["group"]}" stroke="{c["border"]}" stroke-width="1" '
                f'stroke-dasharray="6 5"/>'
                + self.text(x + 18, y + 24, title, size=12, colour=c["sub"],
                            weight="600"))

    def footer(self, note):
        return (f'<line x1="24" y1="{self.h - 52}" x2="{self.w - 24}" y2="{self.h - 52}" '
                f'stroke="{self.c["rule"]}" stroke-width="1"/>'
                + self.text(24, self.h - 26, note, size=12.5, colour=self.c["sub"]))

    def render(self) -> str:
        c = self.c
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'width="{self.w}" height="{self.h}" role="img" aria-label="{escape(self.label)}">'
            f'<defs>'
            f'<marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" '
            f'markerHeight="6" orient="auto-start-reverse">'
            f'<path d="M0 0 10 5 0 10z" fill="{c["line"]}"/></marker>'
            f'</defs>' + "".join(self.parts) + "</svg>"
        )


# ── the diagrams ──────────────────────────────────────────────────────────

def architecture(scheme):
    """Two Lambdas: one answers Slack at once, the other does the slow work."""
    k = Canvas(1180, 520, scheme,
               "A Slack user runs /newintro and submits the modal to the UI Lambda, which checks "
               "the email allowlist, acknowledges Slack and invokes the worker Lambda "
               "asynchronously. Both read their config from Secrets Manager. The worker syncs the "
               "Azure AD group, picks partners from DynamoDB, books slots in Google Calendar and "
               "posts progress to the Slack channel.")
    c = k.c
    top, H = 150, 84
    mid = top + H / 2
    ux, uw = 290, 230
    wx, ww = 652, 240
    k.add(
        k.box(440, 40, 280, 64, "Secrets Manager", ["one JSON config secret"], icon="key"),
        k.edge([(470, 104 + 8), (470, top - 8)], dash=True),
        k.edge([(690, 104 + 8), (690, top - 8)], dash=True),
        k.box(24, top, 170, H, "Slack user", ["fills in the modal", "and submits it"], icon="user"),
        k.box(ux, top, uw, H, "UI Lambda", ["checks the email allowlist,", "acks Slack within 3 s"],
              icon="bolt"),
        k.box(wx, top, ww, H, "Worker Lambda", ["books every intro, stops", "safely near 15 minutes"],
              icon="bolt", tone="accent"),
        k.edge([(194 + 8, mid), (ux - 8, mid)], label="/newintro"),
        k.edge([(ux + uw + 8, mid), (wx - 8, mid)], label="async invoke"),
    )
    # One trunk out of the worker, one branch per service it drives.
    by, bus = 330, 290
    xs = [290, 512, 734, 956]
    services = [
        ("Azure AD", ["group members in,", "departed pruned"], "users"),
        ("DynamoDB", ["partner weights,", "least-used first"], "database"),
        ("Google Calendar", ["FreeBusy search,", "event with both people"], "calendar"),
        ("Slack channel", ["progress and", "confirmations"], "chat"),
    ]
    trunk = wx + ww / 2
    for x, (title, subs, icon) in zip(xs, services):
        cx = x + 100
        k.add(k.edge([(trunk, top + H + 8), (trunk, bus), (cx, bus), (cx, by - 8)]),
              k.box(x, by, 200, 84, title, subs, icon=icon))
    k.add(k.footer("The UI Lambda answers inside Slack's three-second window and hands the whole "
                   "request over; the worker syncs the group once, then books intro by intro."))
    return k.render()


DIAGRAMS = {
    "architecture": architecture,
}


def main() -> None:
    out = ROOT / "docs" / "assets"
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in DIAGRAMS.items():
        for scheme in SCHEMES:
            path = out / f"{name}-{scheme}.svg"
            path.write_text(fn(scheme), encoding="utf-8")
    print(f"{len(DIAGRAMS)} diagrams x {len(SCHEMES)} schemes -> docs/assets/")


if __name__ == "__main__":
    main()
