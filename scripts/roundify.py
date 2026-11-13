"""
roundify — add a continuous roundness axis (ROND) to a TrueType variable font.

The engine works directly on compiled glyf/gvar variable fonts:

1. Every original master (each gvar region peak) is reconstructed exactly.
2. Each visible corner of every simple glyph is replaced, in *every* master, by a
   smooth (continuous-curvature leaning) cubic fillet, converted to compatible
   quadratic splines. Corners hidden inside overlapping contours are left alone
   so that junctions never get notched.
3. A "sharp" twin of every master is emitted with the identical point structure but
   zero-size fillets, which reproduces the original outlines exactly.
4. gvar is rebuilt from the (original masters x {sharp, round}) master set, the
   ROND axis is appended to fvar/avar/STAT and to every ItemVariationStore region,
   so kerning, HVAR and MVAR variations survive untouched.

Composite glyphs are untouched: they inherit the rounding from their base glyphs.
"""

from __future__ import annotations

import math
from array import array
from dataclasses import dataclass, field

from fontTools.cu2qu import curves_to_quadratic
from fontTools.misc.roundTools import otRound
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot
from fontTools.ttLib.tables import ttProgram
from fontTools.ttLib.tables._f_v_a_r import Axis
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.varLib.iup import iup_delta
from fontTools.varLib.models import VariationModel, supportScalar

# --------------------------------------------------------------------------------------
# Parameters
# --------------------------------------------------------------------------------------


@dataclass
class RoundParams:
    # Convex corner radius at ROND=max, as a fraction of the master's stem width.
    # 0.5 == "drawn with a round pen as wide as the stem" (fully rounded terminals).
    convex: float = 0.5
    # Concave (inner crotch) radius at ROND=max, as a fraction of stem width.
    concave: float = 0.11
    # 0 = circular fillets, 1 = handles on the corner (curvature-continuous ends).
    smoothing: float = 0.3
    # How much a smoothed corner reaches further along its edges (keeps optical size).
    reach: float = 0.2
    # Turning angle (degrees) above which an on-curve point counts as a corner.
    min_angle: float = 8.0
    # Never let a fillet eat more than this fraction of a segment it shares with
    # another rounded corner (0.5 == the two fillets can meet in the middle).
    shared_fraction: float = 0.5
    free_fraction: float = 0.92
    # cu2qu tolerance in font units.
    tolerance: float = 0.75
    # Glyph names never to touch (in addition to auto-detected connecting glyphs).
    skip: set = field(default_factory=set)
    # Unicode ranges never to touch (box drawing / block elements / powerline must tile).
    skip_ranges: tuple = ((0x2500, 0x259F), (0xE0A0, 0xE0D7), (0x1FB00, 0x1FBFF))
    # Monospace: corners lying on a cell boundary (x == k * advance) join the
    # neighbouring glyph (ligature pieces, underscores, arrows) and stay sharp.
    keep_cell_joins: bool = False
    # Glyph and relative height used to measure the stem width of each master.
    stem_probe: str = "l"
    stem_probe_height: float = 0.4


# --------------------------------------------------------------------------------------
# Small vector helpers
# --------------------------------------------------------------------------------------


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(a, s):
    return (a[0] * s, a[1] * s)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def norm(a):
    return math.hypot(a[0], a[1])


def unit(a):
    n = norm(a)
    return (a[0] / n, a[1] / n) if n > 1e-9 else (0.0, 0.0)


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def qpoint(p0, p1, p2, t):
    mt = 1 - t
    return (
        mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
        mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1],
    )


def qsplit(p0, p1, p2, t):
    a = lerp(p0, p1, t)
    b = lerp(p1, p2, t)
    m = lerp(a, b, t)
    return (p0, a, m), (m, b, p2)


def t_from_start(p0, p1, p2, d):
    """Parameter t where the chord distance from p0 equals d."""
    if norm(sub(p2, p0)) <= d:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if norm(sub(qpoint(p0, p1, p2, mid), p0)) < d:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def t_from_end(p0, p1, p2, d):
    if norm(sub(p2, p0)) <= d:
        return 0.0
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if norm(sub(qpoint(p0, p1, p2, mid), p2)) > d:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def turning_angle(u_in, u_out):
    c = max(-1.0, min(1.0, dot(u_in, u_out)))
    return math.acos(c)


# --------------------------------------------------------------------------------------
# Reading masters
# --------------------------------------------------------------------------------------


def master_locations(vf: TTFont):
    """Normalized locations of every master, default first."""
    peaks = set()
    for tvs in vf["gvar"].variations.values():
        for tv in tvs:
            loc = []
            for tag, (start, peak, end) in tv.axes.items():
                if peak not in (-1.0, 1.0):
                    raise NotImplementedError("intermediate masters not supported yet")
                loc.append((tag, peak))
            peaks.add(tuple(sorted(loc)))
    return [{}] + [dict(p) for p in sorted(peaks)]


def coords_at(vf: TTFont, glyph_name: str, loc: dict) -> GlyphCoordinates:
    """Exact glyph coordinates (including 4 phantom points) at a normalized location."""
    glyf = vf["glyf"]
    hmtx = vf["hmtx"].metrics
    vmtx = vf["vmtx"].metrics if "vmtx" in vf else None
    coords, control = glyf._getCoordinatesAndControls(glyph_name, hmtx, vmtx)
    out = GlyphCoordinates(coords)
    if not loc:
        return out
    ends = control[1] if control[0] >= 1 else list(range(len(control[1])))
    for tv in vf["gvar"].variations.get(glyph_name, []):
        s = supportScalar(loc, tv.axes)
        if not s:
            continue
        delta = tv.coordinates
        if None in delta:
            delta = iup_delta(delta, coords, ends)
        out += GlyphCoordinates(delta) * s
    return out


# --------------------------------------------------------------------------------------
# Contour structure
# --------------------------------------------------------------------------------------


@dataclass
class Segment:
    start: int  # index (in rotated contour) of the start on-curve
    offs: list  # indices of off-curve points
    end: int  # index of the end on-curve


@dataclass
class Corner:
    kind: str  # "convex" | "concave"


def split_contours(glyph: Glyph):
    ends = list(glyph.endPtsOfContours)
    start = 0
    out = []
    for e in ends:
        out.append(list(range(start, e + 1)))
        start = e + 1
    return out


def rotate_to_oncurve(idx, flags):
    for k, i in enumerate(idx):
        if flags[i] & 1:
            return idx[k:] + idx[:k]
    return None  # all off-curve contour (no corners possible)


def build_segments(idx, flags):
    """idx starts at an on-curve. Returns segments covering the closed contour."""
    n = len(idx)
    ons = [k for k in range(n) if flags[idx[k]] & 1]
    segs = []
    for a, oi in enumerate(ons):
        oj = ons[(a + 1) % len(ons)]
        offs = []
        k = (oi + 1) % n
        while k != oj:
            offs.append(k)
            k = (k + 1) % n
        if len(ons) == 1:  # single on-curve contour
            offs = [k for k in range(1, n)]
        segs.append(Segment(oi, offs, oj))
    return segs


def flatten_contour(pts, flags, idx, steps=8):
    """Polyline approximation of a closed quadratic contour."""
    rot = rotate_to_oncurve(idx, flags)
    if rot is None:
        # all off-curve: on-curves are implied midpoints
        rot = idx
        poly = []
        n = len(rot)
        for k in range(n):
            a = pts[rot[k]]
            b = pts[rot[(k + 1) % n]]
            c = pts[rot[(k + 2) % n]]
            p0, p2 = lerp(a, b, 0.5), lerp(b, c, 0.5)
            for s in range(steps):
                poly.append(qpoint(p0, b, p2, s / steps))
        return poly
    segs = build_segments(rot, flags)
    poly = []
    for seg in segs:
        p_start = pts[rot[seg.start]]
        p_end = pts[rot[seg.end]]
        if not seg.offs:
            poly.append(p_start)
            continue
        quads = spline_quads(p_start, [pts[rot[o]] for o in seg.offs], p_end)
        for q in quads:
            for s in range(steps):
                poly.append(qpoint(*q, s / steps))
    return poly


def spline_quads(p_start, offs, p_end):
    """Split a TrueType quadratic spline into explicit quadratic pieces."""
    quads = []
    cur = p_start
    for i, off in enumerate(offs):
        if i == len(offs) - 1:
            nxt = p_end
        else:
            nxt = lerp(off, offs[i + 1], 0.5)
        quads.append((cur, off, nxt))
        cur = nxt
    return quads


def winding(pt, poly):
    wn = 0
    x, y = pt
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if y0 <= y:
            if y1 > y and (x1 - x0) * (y - y0) - (x - x0) * (y1 - y0) > 0:
                wn += 1
        else:
            if y1 <= y and (x1 - x0) * (y - y0) - (x - x0) * (y1 - y0) < 0:
                wn -= 1
    return wn


def dist_to_poly(pt, poly):
    best = float("inf")
    n = len(poly)
    for i in range(n):
        a = poly[i]
        b = poly[(i + 1) % n]
        ab = sub(b, a)
        L2 = dot(ab, ab)
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, dot(sub(pt, a), ab) / L2))
        best = min(best, norm(sub(pt, lerp(a, b, t))))
    return best


# --------------------------------------------------------------------------------------
# Per-glyph analysis (structure shared by all masters)
# --------------------------------------------------------------------------------------


def tangent_in(pts, rot, k):
    """Unit direction of travel arriving at rot[k]."""
    n = len(rot)
    p = pts[rot[k]]
    for back in range(1, n):
        q = pts[rot[(k - back) % n]]
        if norm(sub(p, q)) > 1e-6:
            return unit(sub(p, q))
    return (0.0, 0.0)


def tangent_out(pts, rot, k):
    n = len(rot)
    p = pts[rot[k]]
    for fwd in range(1, n):
        q = pts[rot[(k + fwd) % n]]
        if norm(sub(q, p)) > 1e-6:
            return unit(sub(q, p))
    return (0.0, 0.0)


def classify_corners(masters_pts, flags, rot, segs, params: RoundParams):
    """Return {on_index_in_rot: Corner} for points that are corners in every master
    with a consistent convexity."""
    corners = {}
    min_a = math.radians(params.min_angle)
    for seg in segs:
        k = seg.start
        kinds = set()
        ok = True
        for pts in masters_pts:
            ui = tangent_in(pts, rot, k)
            uo = tangent_out(pts, rot, k)
            if ui == (0.0, 0.0) or uo == (0.0, 0.0):
                ok = False
                break
            a = turning_angle(ui, uo)
            if a < min_a:
                ok = False
                break
            kinds.add("convex" if cross(ui, uo) < 0 else "concave")
        if ok and len(kinds) == 1:
            corners[k] = Corner(kinds.pop())
    return corners


# --------------------------------------------------------------------------------------
# Geometry for one master / one roundness level
# --------------------------------------------------------------------------------------


def fillet_handles_kappa(phi, smoothing):
    # circular arc handle as a fraction of the tangent length
    phi = max(1e-3, min(phi, math.radians(175)))
    k_circle = (4.0 / 3.0) * math.tan(phi / 4) / math.tan(phi / 2)
    return k_circle + smoothing * (1.0 - k_circle)


def line_intersection(p, u, q, v):
    """Intersection of p + s*u and q + t*v. Returns (s, t) or None."""
    det = cross(u, v)
    if abs(det) < 1e-9:
        return None
    w = sub(q, p)
    s = cross(w, v) / det
    t = cross(w, u) / det
    return s, t


@dataclass
class Plan:
    """Rounding plan for one contour of one master: tangent lengths per corner."""

    d: dict  # corner on-index -> tangent length


def edge_samples(pts, rot, segs, k, side, n=24):
    """(point, travel tangent) along the segment leaving (side='out') or entering
    (side='in') the on-curve rot[k], ordered from the corner outward."""
    for seg in segs:
        if (side == "out" and seg.start == k) or (side == "in" and seg.end == k):
            break
    p0, p1 = pts[rot[seg.start]], pts[rot[seg.end]]
    if not seg.offs:
        q = (p0, lerp(p0, p1, 0.5), p1)
    else:
        quads = spline_quads(p0, [pts[rot[o]] for o in seg.offs], p1)
        q = quads[0] if side == "out" else quads[-1]
    ts = [(i + 1) / n for i in range(n)]
    if side == "in":
        ts = [1 - t for t in ts]
    out = []
    for t in ts:
        d = add(mul(sub(q[1], q[0]), 2 * (1 - t)), mul(sub(q[2], q[1]), 2 * t))
        out.append((qpoint(*q, t), unit(d)))
    return out


def winding_np(points, polys):
    """Total winding number of every point against a list of closed polylines."""
    import numpy as np

    P = np.asarray(points, dtype=float)
    px, py = P[:, 0:1], P[:, 1:2]
    total = np.zeros(len(P), dtype=int)
    for poly in polys:
        A = np.asarray(poly, dtype=float)
        B = np.roll(A, -1, axis=0)
        x0, y0, x1, y1 = A[:, 0], A[:, 1], B[:, 0], B[:, 1]
        cr = (x1 - x0) * (py - y0) - (px - x0) * (y1 - y0)
        up = (y0 <= py) & (y1 > py) & (cr > 0)
        dn = (y0 > py) & (y1 <= py) & (cr < 0)
        total += up.sum(axis=1) - dn.sum(axis=1)
    return total


def signed_area(poly):
    a = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return a / 2


def corner_is_clean(P, own_poly, all_polys, eps=3.0, n=16):
    """True when the ink around P is exactly what this contour alone would give:
    no other contour touches the corner (stacked identical corners are fine)."""
    ring = [(P[0] + eps * math.cos(2 * math.pi * i / n), P[1] + eps * math.sin(2 * math.pi * i / n)) for i in range(n)]
    total = winding_np(ring, all_polys) != 0
    own_w = winding_np(ring, [own_poly]) != 0
    outer = signed_area(own_poly) < 0  # clockwise in y-up == outer contour
    own_material = own_w if outer else ~own_w
    return bool((total == own_material).all())


def entry_limits(pts, rot, segs, corners, all_polys, own_index):
    """Distance from each corner to where its edges disappear into other ink, or
    where another contour starts running along the edge (stacked construction such
    as a bowl drawn flush with a stem). A fillet must stop there, otherwise the
    junction gets notched or the cut is filled back in by the other contour."""
    # Only ink-carrying (clockwise) contours can stack on one another; counters are
    # judged by the outside probe alone.
    own_outer = signed_area(all_polys[own_index]) < 0
    others = [p for i, p in enumerate(all_polys) if i != own_index and signed_area(p) < 0] if own_outer else []
    lim = {}
    for k in corners:
        C = pts[rot[k]]
        res = []
        for side in ("in", "out"):
            smp = edge_samples(pts, rot, segs, k, side)
            # material is on the right of travel; probe just outside (to the left)
            probes = [add(p, mul((-t[1], t[0]), 2.5)) for p, t in smp]
            filled = winding_np(probes, all_polys) != 0
            # ...and just inside, against the other contours only
            inner = [add(p, mul((t[1], -t[0]), 2.5)) for p, t in smp]
            if others:
                filled |= winding_np(inner, others) != 0
            if filled.any():
                first = int(filled.argmax())
                prev = smp[first - 1][0] if first > 0 else C
                res.append(norm(sub(prev, C)) * 0.85)
            else:
                res.append(float("inf"))
        lim[k] = tuple(res)
    return lim


def plan_contour(pts, rot, segs, corners, stem, rho, params: RoundParams, limits=None):
    """Tangent length for every corner in this master at roundness rho (0..1)."""
    d = {}
    if rho <= 0:
        return {k: 0.0 for k in corners}
    # available length on each side of every corner
    avail_out = {}
    avail_in = {}
    for seg in segs:
        p0 = pts[rot[seg.start]]
        p1 = pts[rot[seg.end]]
        both = seg.start in corners and seg.end in corners
        if not seg.offs:
            L = norm(sub(p1, p0))
            f = params.shared_fraction if both else params.free_fraction
            avail_out[seg.start] = L * f
            avail_in[seg.end] = L * f
        else:
            quads = spline_quads(p0, [pts[rot[o]] for o in seg.offs], p1)
            single = len(quads) == 1
            q_first, q_last = quads[0], quads[-1]
            f = params.shared_fraction if (both and single) else params.free_fraction
            avail_out[seg.start] = norm(sub(q_first[2], q_first[0])) * f
            avail_in[seg.end] = norm(sub(q_last[2], q_last[0])) * f
    for k, c in corners.items():
        ui = tangent_in(pts, rot, k)
        uo = tangent_out(pts, rot, k)
        phi = min(turning_angle(ui, uo), math.radians(165))
        r = (params.convex if c.kind == "convex" else params.concave) * stem * rho
        target = r * math.tan(phi / 2) * (1.0 + params.reach * params.smoothing)
        li, lo = limits.get(k, (math.inf, math.inf)) if limits else (math.inf, math.inf)
        d[k] = max(0.0, min(target, avail_in[k], avail_out[k], li, lo))
    return d


def render_contour(pts, rot, segs, corners, dvals, params: RoundParams):
    """Produce the new contour for one master as a list of items:
    ('on', pt) | ('off', pt) | ('fillet', cubic, corner_index)
    Structure depends only on (segs, corners), never on geometry."""
    # 1) trimmed segments
    seg_out = []  # per segment: (start_pt, list_of_items_between, end_pt)
    for seg in segs:
        p0 = pts[rot[seg.start]]
        p1 = pts[rot[seg.end]]
        ds = dvals.get(seg.start, 0.0) if seg.start in corners else None
        de = dvals.get(seg.end, 0.0) if seg.end in corners else None
        if not seg.offs:
            u = unit(sub(p1, p0))
            a = add(p0, mul(u, ds)) if ds is not None else p0
            b = sub(p1, mul(u, de)) if de is not None else p1
            seg_out.append((a, [], b, u, u))
            continue
        offs = [pts[rot[o]] for o in seg.offs]
        quads = [list(q) for q in spline_quads(p0, offs, p1)]
        items = []
        # trim start
        tan_start = unit(sub(quads[0][1], quads[0][0])) if norm(sub(quads[0][1], quads[0][0])) > 1e-9 else unit(sub(quads[0][2], quads[0][0]))
        tan_end = unit(sub(quads[-1][2], quads[-1][1])) if norm(sub(quads[-1][2], quads[-1][1])) > 1e-9 else unit(sub(quads[-1][2], quads[-1][0]))
        if len(quads) == 1 and ds is not None and de is not None:
            q = quads[0]
            t0 = t_from_start(*q, ds) if ds > 0 else 0.0
            t1 = t_from_end(*q, de) if de > 0 else 1.0
            t1 = max(t1, t0)
            _, right = qsplit(*q, t0)
            # map t1 into the right piece
            tt = 0.0 if t0 >= 1 else (t1 - t0) / (1 - t0)
            mid, _ = qsplit(*right, tt)
            quads[0] = list(mid)
        else:
            if ds is not None:
                q = quads[0]
                t0 = t_from_start(*q, ds) if ds > 0 else 0.0
                _, right = qsplit(*q, t0)
                quads[0] = list(right)
            if de is not None:
                q = quads[-1]
                t1 = t_from_end(*q, de) if de > 0 else 1.0
                left, _ = qsplit(*q, t1)
                quads[-1] = list(left)
        # tangents at the new ends
        q0 = quads[0]
        qn = quads[-1]
        ts = sub(q0[1], q0[0])
        tan_start = unit(ts) if norm(ts) > 1e-6 else tan_start
        te = sub(qn[2], qn[1])
        tan_end = unit(te) if norm(te) > 1e-6 else tan_end
        # emit offs; implied on-curves between quads become explicit if the
        # neighbouring quad was trimmed (so the untouched pieces keep their shape)
        n = len(quads)
        for i, q in enumerate(quads):
            items.append(("off", q[1]))
            if i < n - 1:
                explicit = (i == 0 and ds is not None) or (i == n - 2 and de is not None)
                if explicit:
                    items.append(("on", q[2]))
        seg_out.append((quads[0][0], items, quads[-1][2], tan_start, tan_end))

    # 2) assemble: corner block + segment interior
    out = []
    nseg = len(segs)
    for j, seg in enumerate(segs):
        k = seg.start
        prev = seg_out[(j - 1) % nseg]
        cur = seg_out[j]
        if k in corners:
            A = prev[2]
            B = cur[0]
            Ta = prev[4]
            Tb = cur[3]
            C = pts[rot[k]]
            if norm(sub(B, A)) < 1e-6:
                cubic = (C, C, C, C)
            else:
                hit = line_intersection(A, Ta, B, mul(Tb, -1))
                V = C
                if hit is not None:
                    s, t = hit
                    dlen = norm(sub(B, A))
                    if 0 < s < 3 * dlen and 0 < t < 3 * dlen:
                        V = add(A, mul(Ta, s))
                phi = turning_angle(Ta, Tb) if Ta != (0.0, 0.0) and Tb != (0.0, 0.0) else math.pi / 2
                kap = fillet_handles_kappa(phi, params.smoothing)
                cubic = (A, lerp(A, V, kap), lerp(B, V, kap), B)
            out.append(("on", A))
            out.append(("fillet", cubic, k))
            out.append(("on", B))
        else:
            out.append(("on", cur[0]))
        out.extend(cur[1])
    return out


# --------------------------------------------------------------------------------------
# Glyph processing across all masters
# --------------------------------------------------------------------------------------


@dataclass
class GlyphResult:
    contours_items: list  # [variant][contour] -> items
    flags_template: list


def connecting_glyphs(vf: TTFont):
    """Glyphs whose ink touches both sidebearings are meant to join (underscore...)."""
    out = set()
    glyf = vf["glyf"]
    hmtx = vf["hmtx"].metrics
    for gn in vf.getGlyphOrder():
        g = glyf[gn]
        if g.numberOfContours <= 0:
            continue
        g.recalcBounds(glyf)
        adv = hmtx[gn][0]
        if adv > 0 and g.xMin <= 0 and g.xMax >= adv:
            out.add(gn)
    return out


def stem_width(vf, loc, probe="l", height=0.4):
    """Horizontal stroke thickness of the probe glyph at a relative height."""
    glyf = vf["glyf"]
    pts = coords_at(vf, probe, loc)
    g = glyf[probe]
    contours = split_contours(g)
    ys = [p[1] for p in pts[:-4]]
    y = min(ys) + height * (max(ys) - min(ys))
    xs = []
    for idx in contours:
        poly = flatten_contour(pts, g.flags, idx, steps=16)
        n = len(poly)
        for i in range(n):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    xs.sort()
    return xs[1] - xs[0]


def contours_from_ends(ends):
    out, start = [], 0
    for e in ends:
        out.append(list(range(start, e + 1)))
        start = e + 1
    return out


def process_glyph(gn, flags, ends, master_pts, stems, rhos, params: RoundParams, stats, cell=None):
    """Returns (variants, flags, ends) or None if the glyph is unchanged.
    variants are indexed [master][rho]. `cell` is the advance width when corners on
    cell boundaries must stay sharp (monospace joins)."""
    contours = contours_from_ends(ends)

    rots, segss, cornerss = [], [], []
    polys = [[None] * len(contours) for _ in master_pts]
    for ci, idx in enumerate(contours):
        rot = rotate_to_oncurve(idx, flags)
        if rot is None:
            rots.append(None)
            segss.append(None)
            cornerss.append({})
            continue
        segs = build_segments(rot, flags)
        corners = classify_corners(master_pts, flags, rot, segs, params)
        if cell:
            for k in list(corners):
                for pts in master_pts:
                    x = pts[rot[k]][0]
                    r = x % cell
                    if min(r, cell - r) <= 2.0:
                        del corners[k]
                        stats["cell_joins"] = stats.get("cell_joins", 0) + 1
                        break
        rots.append(rot)
        segss.append(segs)
        cornerss.append(corners)

    if not any(cornerss):
        return None

    # hidden-corner test against the other contours (overlap construction)
    if len(contours) > 1:
        for mi, pts in enumerate(master_pts):
            for ci, idx in enumerate(contours):
                polys[mi][ci] = flatten_contour(pts, flags, idx)
        # A corner may only be rounded when, in every master, the union ink around
        # it is exactly what its own contour gives. That rejects corners buried in
        # other contours, T-junctions and abutting parts, and keeps counters and
        # stacked identical corners.
        hidden_set = []
        for ci, corners in enumerate(cornerss):
            for k in corners:
                for mi, pts in enumerate(master_pts):
                    P = pts[rots[ci][k]]
                    if not corner_is_clean(P, polys[mi][ci], polys[mi]):
                        hidden_set.append((ci, k))
                        break
        for ci, k in hidden_set:
            del cornerss[ci][k]
            stats["hidden"] += 1

    if not any(cornerss):
        return None
    stats["corners"] += sum(len(c) for c in cornerss)

    # how far each fillet may reach before running into other ink
    limits = None
    if len(contours) > 1:
        limits = []
        for mi, pts in enumerate(master_pts):
            per_c = []
            for ci in range(len(contours)):
                if not cornerss[ci]:
                    per_c.append({})
                    continue
                per_c.append(entry_limits(pts, rots[ci], segss[ci], cornerss[ci], polys[mi], ci))
            limits.append(per_c)

    # render every master x rho
    rendered = []  # [mi][ri][ci] -> items
    for mi, pts in enumerate(master_pts):
        per_rho = []
        for rho in rhos:
            per_contour = []
            for ci, idx in enumerate(contours):
                if rots[ci] is None:
                    per_contour.append([("raw", idx)])
                    continue
                if not cornerss[ci]:
                    per_contour.append([("rawrot", rots[ci])])
                    continue
                dvals = plan_contour(
                    pts, rots[ci], segss[ci], cornerss[ci], stems[mi], rho, params,
                    limits=limits[mi][ci] if limits else None,
                )
                per_contour.append(render_contour(pts, rots[ci], segss[ci], cornerss[ci], dvals, params))
            per_rho.append(per_contour)
        rendered.append(per_rho)

    # compatible cubic->quadratic conversion for every fillet, across all variants
    variants = [(mi, ri) for mi in range(len(master_pts)) for ri in range(len(rhos))]
    ncont = len(contours)
    for ci in range(ncont):
        items0 = rendered[0][0][ci]
        for ii, it in enumerate(items0):
            if it[0] != "fillet":
                continue
            cubics = [rendered[mi][ri][ci][ii][1] for mi, ri in variants]
            live = [i for i, c in enumerate(cubics) if norm(sub(c[3], c[0])) > 0.5]
            if live:
                splines = curves_to_quadratic([cubics[i] for i in live], [params.tolerance] * len(live))
                noffs = len(splines[0]) - 2
            else:
                splines, noffs = [], 1
            sp_by = dict(zip(live, splines))
            for vi, (mi, ri) in enumerate(variants):
                if vi in sp_by:
                    offs = sp_by[vi][1:-1]
                else:
                    c = cubics[vi]
                    # degenerate: place offs evenly on the chord (here: the corner)
                    offs = [lerp(c[0], c[3], (i + 1) / (noffs + 1)) if norm(sub(c[3], c[0])) > 0 else c[1] for i in range(noffs)]
                rendered[mi][ri][ci][ii] = ("offs", offs)

    # flatten to point lists
    out = {}
    template_flags = None
    template_ends = None
    for mi in range(len(master_pts)):
        pts = master_pts[mi]
        for ri in range(len(rhos)):
            coords = []
            fl = []
            ends = []
            for ci, idx in enumerate(contours):
                items = rendered[mi][ri][ci]
                if items and items[0][0] in ("raw", "rawrot"):
                    seq = items[0][1]
                    for i in seq:
                        coords.append(pts[i])
                        fl.append(flags[i] & 1)
                else:
                    for it in items:
                        if it[0] == "on":
                            coords.append(it[1])
                            fl.append(1)
                        elif it[0] == "off":
                            coords.append(it[1])
                            fl.append(0)
                        elif it[0] == "offs":
                            for p in it[1]:
                                coords.append(p)
                                fl.append(0)
                ends.append(len(coords) - 1)
            if template_flags is None:
                template_flags, template_ends = fl, ends
            else:
                assert fl == template_flags and ends == template_ends, f"incompatible {gn}"
            out[(mi, ri)] = [(otRound(x), otRound(y)) for x, y in coords]
    return out, template_flags, template_ends


# --------------------------------------------------------------------------------------
# Font assembly
# --------------------------------------------------------------------------------------


def decompose_at(vf, gn, loc):
    """Flatten a (possibly nested) composite at a master location.
    Returns (points, on-curve flags, endPts). Flipped components are reversed so
    every outer contour keeps TrueType's clockwise orientation."""
    glyf = vf["glyf"]
    g = glyf[gn]
    coords = coords_at(vf, gn, loc)
    if not g.isComposite():
        return list(coords[:-4]), [f & 1 for f in g.flags], list(g.endPtsOfContours)
    pts, fl, ends = [], [], []
    for ci, comp in enumerate(g.components):
        cp, cf, ce = decompose_at(vf, comp.glyphName, loc)
        dx, dy = coords[ci]
        a, b, c, d = 1.0, 0.0, 0.0, 1.0
        if hasattr(comp, "transform"):
            (a, b), (c, d) = comp.transform
        cp = [(a * x + c * y + dx, b * x + d * y + dy) for x, y in cp]
        flipped = (a * d - b * c) < 0
        start = 0
        for e in ce:
            seg_pts = cp[start : e + 1]
            seg_fl = cf[start : e + 1]
            if flipped:
                seg_pts = seg_pts[::-1]
                seg_fl = seg_fl[::-1]
            pts.extend(seg_pts)
            fl.extend(seg_fl)
            ends.append(len(pts) - 1)
            start = e + 1
    return pts, fl, ends


def _draw_quadratic(pen, pts, flags, ends):
    for idx in contours_from_ends(ends):
        ons = [i for i in idx if flags[i]]
        if not ons:
            pen.qCurveTo(*[pts[i] for i in idx], None)
            pen.closePath()
            continue
        k0 = idx.index(ons[0])
        rot = idx[k0:] + idx[:k0]
        pen.moveTo(pts[rot[0]])
        offs = []
        for i in rot[1:] + [rot[0]]:
            if flags[i]:
                if offs:
                    pen.qCurveTo(*offs, pts[i])
                else:
                    pen.lineTo(pts[i])
                offs = []
            else:
                offs.append(pts[i])
        pen.closePath()


def touching_composites(vf, locs):
    """Composites whose components overlap or abut in any master: their joins must
    be analysed on the decomposed outline, or rounding would notch them."""
    import pathops
    from fontTools.pens.areaPen import AreaPen

    glyf = vf["glyf"]
    out = set()
    for gn in vf.getGlyphOrder():
        g = glyf[gn]
        if not g.isComposite() or len(g.components) < 2:
            continue
        hit = False
        for loc in locs:
            coords = coords_at(vf, gn, loc)
            paths = []
            for ci, comp in enumerate(g.components):
                cp, cf, ce = decompose_at(vf, comp.glyphName, loc)
                dx, dy = coords[ci]
                a, b, c, d = 1.0, 0.0, 0.0, 1.0
                if hasattr(comp, "transform"):
                    (a, b), (c, d) = comp.transform
                cp = [(a * x + c * y + dx, b * x + d * y + dy) for x, y in cp]
                p = pathops.Path()
                if ce:
                    _draw_quadratic(p.getPen(), cp, cf, ce)
                paths.append(pathops.simplify(p, fix_winding=True))
            for i in range(len(paths)):
                for j in range(i + 1, len(paths)):
                    inter = pathops.op(paths[i], paths[j], pathops.PathOp.INTERSECTION)
                    ap = AreaPen()
                    inter.draw(ap)
                    if abs(ap.value) > 1:
                        hit = True
                        break
                    uni = pathops.op(paths[i], paths[j], pathops.PathOp.UNION)
                    if len(list(uni.contours)) < len(list(paths[i].contours)) + len(list(paths[j].contours)):
                        hit = True
                        break
                if hit:
                    break
            if hit:
                break
        if hit:
            out.add(gn)
    return out


def _new_simple_glyph(coords, flags, ends):
    g = Glyph()
    g.numberOfContours = len(ends)
    g.coordinates = GlyphCoordinates(coords)
    g.flags = array("B", flags)
    g.endPtsOfContours = list(ends)
    g.program = ttProgram.Program()
    g.program.fromBytecode(b"")
    return g


def _append_axis_to_varstore(store, axis_count):
    if store is None:
        return
    rl = store.VarRegionList
    for region in rl.Region:
        while len(region.VarRegionAxis) < axis_count:
            ra = ot.VarRegionAxis()
            ra.StartCoord, ra.PeakCoord, ra.EndCoord = 0.0, 0.0, 0.0
            region.VarRegionAxis.append(ra)
    rl.RegionAxisCount = axis_count


def add_roundness_axis(
    vf: TTFont,
    params: RoundParams = RoundParams(),
    axis_tag="ROND",
    axis_min=0.0,
    axis_default=100.0,
    axis_max=100.0,
    axis_name="Roundness",
    log=print,
):
    """Mutates vf in place and returns stats."""
    assert axis_default in (axis_min, axis_max), "default must be at an extreme for now"
    locs = master_locations(vf)
    log(f"  masters: {locs}")
    stems = [stem_width(vf, loc, params.stem_probe, params.stem_probe_height) for loc in locs]
    log(f"  stem widths: {[round(s) for s in stems]}")

    # roundness masters, normalized; rho is the physical rounding amount 0..1
    if axis_default == axis_max:
        rond_locs = [(0.0, 1.0), (-1.0, 0.0)]  # (normalized, rho)
    else:
        rond_locs = [(0.0, 0.0), (1.0, 1.0)]
    rhos = [r for _, r in rond_locs]

    glyf = vf["glyf"]
    gvar = vf["gvar"]
    # proportional fonts: whole glyphs that span their cell are joiners (underscore);
    # monospace fonts handle joins per corner instead (see keep_cell_joins)
    skip = set(params.skip) | (set() if params.keep_cell_joins else connecting_glyphs(vf))
    cmap = vf.getBestCmap()
    for cp, gn in cmap.items():
        if any(a <= cp <= b for a, b in params.skip_ranges):
            skip.add(gn)
    log(f"  skipping {len(skip)} connecting/tiling glyphs")

    axis_tags = [a.axisTag for a in vf["fvar"].axes] + [axis_tag]
    full_locs = []
    for loc in locs:
        for nrm, _ in rond_locs:
            l2 = dict(loc)
            if nrm:
                l2[axis_tag] = nrm
            full_locs.append(l2)
    model = VariationModel(full_locs, axisOrder=axis_tags)

    stats = {"glyphs": 0, "corners": 0, "hidden": 0, "decomposed": 0}
    hmtx = vf["hmtx"].metrics
    new_glyphs = {}
    new_vars = {}
    touching = touching_composites(vf, locs)
    log(f"  decomposing {len(touching)} composites whose parts touch")
    for gn in vf.getGlyphOrder():
        g = glyf[gn]
        if g.numberOfContours == 0 or gn in skip:
            continue
        if g.isComposite() and gn not in touching:
            continue
        all_pts = [coords_at(vf, gn, loc) for loc in locs]
        phantoms = [list(p[-4:]) for p in all_pts]
        if g.isComposite():
            dec = [decompose_at(vf, gn, loc) for loc in locs]
            master_pts = [d[0] for d in dec]
            flags, ends = dec[0][1], dec[0][2]
        else:
            master_pts = [list(p[:-4]) for p in all_pts]
            flags, ends = [f & 1 for f in g.flags], list(g.endPtsOfContours)
        cell = hmtx[gn][0] if params.keep_cell_joins and hmtx[gn][0] > 0 else None
        res = process_glyph(gn, flags, ends, master_pts, stems, rhos, params, stats, cell=cell)
        if res is None:
            continue
        variants, flags, ends = res
        stats["glyphs"] += 1
        if g.isComposite():
            stats["decomposed"] += 1
        master_values = []
        for mi in range(len(locs)):
            for ri in range(len(rhos)):
                pts = variants[(mi, ri)] + [(otRound(x), otRound(y)) for x, y in phantoms[mi]]
                master_values.append(GlyphCoordinates(pts))
        deltas = model.getDeltas(master_values)
        supports = model.supports
        # VariationModel sorts masters; deltas[0] is the default master's coordinates
        base = deltas[0]
        new_g = _new_simple_glyph([tuple(p) for p in base[:-4]], flags, ends)
        new_glyphs[gn] = new_g
        tvs = []
        endpts = list(ends)
        for sup, delta in zip(supports[1:], deltas[1:]):
            dl = [(otRound(x), otRound(y)) for x, y in delta]
            if not any(x or y for x, y in dl):
                continue
            tv = TupleVariation(sup, dl)
            tv.optimize(base, endpts, tolerance=0.5)
            tvs.append(tv)
        new_vars[gn] = tvs

    for gn, ng in new_glyphs.items():
        glyf[gn] = ng
        gvar.variations[gn] = new_vars[gn]
    # refresh bounds + lsb everywhere (composites may have changed too)
    for gn in vf.getGlyphOrder():
        g = glyf[gn]
        if g.numberOfContours == 0:
            continue
        g.recalcBounds(glyf)
        adv, _ = hmtx[gn]
        hmtx[gn] = (adv, g.xMin)

    # ---- tables that know about axes ----
    fvar = vf["fvar"]
    name = vf["name"]
    ax = Axis()
    ax.axisTag = axis_tag
    ax.minValue, ax.defaultValue, ax.maxValue = axis_min, axis_default, axis_max
    ax.axisNameID = name.addMultilingualName({"en": axis_name}, vf, minNameID=256)
    ax.flags = 0
    fvar.axes.append(ax)
    for inst in fvar.instances:
        inst.coordinates[axis_tag] = axis_default
    if "avar" in vf:
        vf["avar"].segments[axis_tag] = {-1.0: -1.0, 0.0: 0.0, 1.0: 1.0}
    n_axes = len(fvar.axes)
    for tag in ("GDEF", "HVAR", "VVAR", "MVAR"):
        if tag in vf:
            store = getattr(vf[tag].table, "VarStore", None)
            _append_axis_to_varstore(store, n_axes)
    stats["masters"] = len(full_locs)
    return stats
