"""
surface_metrics.py — how to measure a surface feature on this project without fooling yourself.

Four metrics have been used here and three of them gave wrong answers that survived until someone
measured the same thing a second way. They are written down because the cost is repeatable: each
one produced a "finding" that was acted on before it was caught.

    max-minus-min depth                 WRONG for a channel on a falling flank.
        It reads zero whenever the surface behind the void is itself narrowing, which is most of
        this car. It reported "no channel" where there was one, and said nothing where a boolean
        had silently done nothing. Replaced by chord_depth.

    depth from 30 mm Z-binned profiles  WRONG by about +-15 mm.
        The bucket boundary lands differently at each station, so the noise looks like a feature.
        It invented an 80/66/65/80 "dip" in the door channel that did not exist.

    angle between adjacent samples      WRONG for anything, at any resolution.
        It measures where the samples happened to land relative to the feature. The same buttress
        crest measured 55, 56, 38 and 21 degrees at 60, 120, 240 and 480 points per half-section,
        and the same rocker measured 0.3, 3.5, 4.7 and 53. Do not use it to judge an edge.

    crease between the two flanks       RIGHT for a direction change, BLIND to a step.
        Fit the surface direction in a band well above the feature and well below it, excluding
        the feature itself, and take the angle between. Stable across resolutions: the channel
        reads 65.2 at both 120 and 240 points. But a pure offset — a step whose flanks stay
        parallel, which is exactly what the rocker tuck is — has no direction change at all and
        this metric reports zero for a perfectly visible edge.

So: crease_angle answers "does the surface change direction here". step_height answers "is there
an offset here". A feature needs whichever question actually describes it, and sometimes both.

And the last resort is not a metric. docs/16 defines surface character by how light behaves, so
the final check is a hard-light render, looked at. Numbers say whether an edge exists; only the
render says whether it reads.
"""

import math


def profile_half(ring):
    """The outboard half of a section, as (y, z) with y >= 0."""
    return [(y, z) for y, z in ring if y >= 0]


def _direction(half, z0, z1):
    """Least-squares dy/dz over a Z band, in degrees. None if the band is too thin."""
    pts = [(y, z) for y, z in half if z0 <= z <= z1]
    if len(pts) < 2:
        return None
    n = len(pts)
    mz = sum(p[1] for p in pts) / n
    my = sum(p[0] for p in pts) / n
    den = sum((p[1] - mz) ** 2 for p in pts)
    if den == 0:
        return None
    return math.degrees(math.atan(sum((p[1] - mz) * (p[0] - my) for p in pts) / den))


def crease_angle(ring, zc, near=25.0, far=75.0):
    """Angle between the flank above the feature and the flank below it. Resolution-independent.
    Returns None when either band is too thin to fit — raise `far` or the section resolution."""
    half = profile_half(ring)
    a = _direction(half, zc + near, zc + far)
    b = _direction(half, zc - far, zc - near)
    return None if a is None or b is None else abs(a - b)


def step_height(ring, zc, near=8.0, far=40.0):
    """Offset across the feature: the half-width just above minus the half-width just below, both
    extrapolated to zc along their own flank. Catches a parallel step, which crease_angle cannot."""
    half = profile_half(ring)
    out = {}
    for tag, (z0, z1) in (("up", (zc + near, zc + far)), ("dn", (zc - far, zc - near))):
        pts = [(y, z) for y, z in half if z0 <= z <= z1]
        if len(pts) < 2:
            return None
        n = len(pts)
        mz = sum(p[1] for p in pts) / n
        my = sum(p[0] for p in pts) / n
        den = sum((p[1] - mz) ** 2 for p in pts)
        slope = 0.0 if den == 0 else sum((p[1] - mz) * (p[0] - my) for p in pts) / den
        out[tag] = my + slope * (zc - mz)
    return out["dn"] - out["up"]


def chord_depth(ring, zc, span=115.0, step=6.0):
    """How far the surface sits inside the straight line joining its own two shoulders. The measure
    that does not go to zero just because the flank behind the void is falling."""
    half = profile_half(ring)

    def y_at(z):
        hits = [y0 + (z - z0) / (z1 - z0) * (y1 - y0)
                for (y0, z0), (y1, z1) in zip(half, half[1:])
                if min(z0, z1) <= z <= max(z0, z1) and z1 != z0]
        return max(hits) if hits else None

    ya, yb = y_at(zc - span), y_at(zc + span)
    if ya is None or yb is None:
        return None
    vals = []
    k = -span + step
    while k < span - step:
        y = y_at(zc + k)
        if y is not None:
            vals.append((ya + (k + span) / (2 * span) * (yb - ya)) - y)
        k += step
    return max(vals) if vals else None
