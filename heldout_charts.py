"""Inline SVG chart builders for Heldout Labs articles.

Each function returns an <svg class="chart"> string styled by the site's .chart CSS classes
(gridlines, ticks, labels and marks use theme tokens, so charts follow light and dark mode).
"""
import html

esc = html.escape


def _ticks(lo, hi, step, x, top, bottom, fmt):
    out = []
    t = lo
    while t <= hi + 1e-9:
        cls = "zero" if abs(t) < 1e-9 else "grid"
        out.append(f'<line class="{cls}" x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top}" y2="{bottom}"/>'
                   f'<text class="tick" x="{x(t):.1f}" y="{bottom + 16}" text-anchor="middle">{fmt(t)}</text>')
        t += step
    return out


def dot_ci(rows, lo, hi, step, fmt, title, W=640, label_w=200, value_w=110, rowh=34, groups=None):
    """Horizontal dot + 95% interval per row. rows: dicts with label, sub (optional), value, low, high,
    strong (bool: interval excludes zero), tip. groups: optional {row_index: group heading} inserted above rows."""
    left, right, top = label_w, W - value_w, 6
    x = lambda v: left + (min(max(v, lo), hi) - lo) / (hi - lo) * (right - left)
    heads = groups or {}
    H = top + rowh * len(rows) + 24 * len(heads) + 28
    out = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">']
    out += _ticks(lo, hi, step, x, top, H - 26, fmt)
    y = top
    for i, r in enumerate(rows):
        if i in heads:
            out.append(f'<text class="row-sub" x="0" y="{y + 17}">{esc(heads[i])}</text>')
            y += 24
        cy = y + rowh / 2
        if r.get("sub"):
            out.append(f'<text class="row-label" x="0" y="{cy - 2:.1f}">{esc(r["label"])}</text>'
                       f'<text class="row-sub" x="0" y="{cy + 13:.1f}">{esc(r["sub"])}</text>')
        else:
            out.append(f'<text class="row-label" x="0" y="{cy + 4:.1f}">{esc(r["label"])}</text>')
        out.append(f'<line class="ci" x1="{x(r["low"]):.1f}" x2="{x(r["high"]):.1f}" y1="{cy:.1f}" y2="{cy:.1f}"/>')
        cls = "dot-new" if r.get("strong") else "dot-old"
        out.append(f'<g class="pt" tabindex="0"><title>{esc(r.get("tip", ""))}</title>'
                   f'<circle class="hit" cx="{x(r["value"]):.1f}" cy="{cy:.1f}" r="12"/>'
                   f'<circle class="{cls}" cx="{x(r["value"]):.1f}" cy="{cy:.1f}" r="5.5"/></g>')
        vcls = "val" if r.get("strong") else "val-muted"
        out.append(f'<text class="{vcls}" x="{W}" y="{cy + 4:.1f}" text-anchor="end">{esc(r["text"])}</text>')
        y += rowh
    out.append("</svg>")
    return "\n".join(out)


def dumbbell(rows, lo, hi, step, fmt, title, W=640, label_w=230, rowh=50):
    """Two values per row: rows have label, sub, a (gray, context), b (accent, the subject), a_text, b_text, tip_a, tip_b."""
    left, right, top = label_w, W - 40, 6
    x = lambda v: left + (v - lo) / (hi - lo) * (right - left)
    H = top + rowh * len(rows) + 28
    out = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">']
    out += _ticks(lo, hi, step, x, top, H - 26, fmt)
    for i, r in enumerate(rows):
        cy = top + rowh * i + rowh / 2
        out.append(f'<text class="row-label" x="0" y="{cy - 2:.1f}">{esc(r["label"])}</text>'
                   f'<text class="row-sub" x="0" y="{cy + 13:.1f}">{esc(r["sub"])}</text>')
        a, b = x(r["a"]), x(r["b"])
        out.append(f'<line class="link" x1="{min(a, b):.1f}" x2="{max(a, b):.1f}" y1="{cy:.1f}" y2="{cy:.1f}"/>')
        for v, cls, tip in ((a, "dot-old", r["tip_a"]), (b, "dot-new", r["tip_b"])):
            out.append(f'<g class="pt" tabindex="0"><title>{esc(tip)}</title><circle class="hit" cx="{v:.1f}" cy="{cy:.1f}" r="12"/>'
                       f'<circle class="{cls}" cx="{v:.1f}" cy="{cy:.1f}" r="5.5"/></g>')
        # value labels on the outer side of each dot
        ra, rb = (a >= b), (b > a)
        out.append(f'<text class="val-muted" x="{a + (11 if ra else -11):.1f}" y="{cy + 4:.1f}" text-anchor="{"start" if ra else "end"}">{esc(r["a_text"])}</text>')
        out.append(f'<text class="val" x="{b + (11 if rb else -11):.1f}" y="{cy + 4:.1f}" text-anchor="{"start" if rb else "end"}">{esc(r["b_text"])}</text>')
    out.append("</svg>")
    return "\n".join(out)


def bars(rows, hi, step, fmt, title, W=640, label_w=200, rowh=30, bar=14):
    """Horizontal bars from zero. rows: label, value, text, tip, strong (accent vs muted)."""
    left, right, top = label_w, W - 60, 6
    x = lambda v: left + v / hi * (right - left)
    H = top + rowh * len(rows) + 28
    out = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}">']
    out += _ticks(0, hi, step, x, top, H - 26, fmt)
    for i, r in enumerate(rows):
        cy = top + rowh * i + rowh / 2
        w = max(x(r["value"]) - left, 0)
        if r.get("sub"):
            out.append(f'<text class="row-label" x="0" y="{cy - 2:.1f}">{esc(r["label"])}</text>'
                       f'<text class="row-sub" x="0" y="{cy + 13:.1f}">{esc(r["sub"])}</text>')
        else:
            out.append(f'<text class="row-label" x="0" y="{cy + 4:.1f}">{esc(r["label"])}</text>')
        cls = "bar" if r.get("strong", True) else "bar-muted"
        if w > 0:
            rx = min(4, w / 2)
            out.append(f'<g class="pt" tabindex="0"><title>{esc(r["tip"])}</title>'
                       f'<path class="{cls}" d="M{left},{cy - bar / 2:.1f} h{w - rx:.1f} a{rx},{rx} 0 0 1 {rx},{rx} v{bar - 2 * rx:.1f} '
                       f'a{rx},{rx} 0 0 1 -{rx},{rx} h-{w - rx:.1f} z"/></g>')
        out.append(f'<text class="val" x="{left + w + 8:.1f}" y="{cy + 4:.1f}">{esc(r["text"])}</text>')
    out.append("</svg>")
    return "\n".join(out)
