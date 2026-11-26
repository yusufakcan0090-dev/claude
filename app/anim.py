"""AE tarzı dönüştürme (Konum/Ölçek/Döndürme/Opaklık) ve keyframe enterpolasyonu.

obj["tf"] = {"x": 0.5, "y": 0.5, "scale": 100, "rot": 0, "op": 100}   (x,y: kompozisyonda merkez, 0-1)
obj["kf"] = {"x": [{"t": 0.0, "v": 0.5, "ease": "lin"|"ease"|"in"|"out"|"hold"}], ...}
keyframe zamanı (t) katmanın başlangıcına göredir (saniye)."""
import math

TF_DEFAULT = {"x": 0.5, "y": 0.5, "scale": 100.0, "rot": 0.0, "op": 100.0}
PROPS = ("x", "y", "scale", "rot", "op")


def tf_of(obj, defaults=None):
    tf = dict(TF_DEFAULT)
    if defaults:
        tf.update(defaults)
    tf.update({k: float(v) for k, v in (obj.get("tf") or {}).items() if k in PROPS and v is not None})
    return tf


def keys(obj, prop):
    k = sorted((obj.get("kf") or {}).get(prop) or [], key=lambda x: x["t"])
    return k if len(k) >= 1 else []


def animated(obj):
    return any(len(keys(obj, p)) >= 2 for p in PROPS)


def _ease(u, a, b):
    """a: çıkan keyframe'in tipi, b: gelen keyframe'in tipi."""
    out_e = a in ("ease", "out")
    in_e = b in ("ease", "in")
    if out_e and in_e:
        return u * u * (3 - 2 * u)
    if out_e:
        return 1 - (1 - u) ** 2
    if in_e:
        return u * u
    return u


def value(obj, prop, t, defaults=None):
    ks = keys(obj, prop)
    if not ks:
        return tf_of(obj, defaults)[prop]
    if t <= ks[0]["t"]:
        return float(ks[0]["v"])
    for a, b in zip(ks, ks[1:]):
        if t <= b["t"]:
            if a.get("ease") == "hold":
                return float(a["v"])
            span = max(1e-6, b["t"] - a["t"])
            u = _ease((t - a["t"]) / span, a.get("ease", "lin"), b.get("ease", "lin"))
            return float(a["v"]) + (float(b["v"]) - float(a["v"])) * u
    return float(ks[-1]["v"])


def expr(obj, prop, tv="t", off=0.0, scale=1.0, add=0.0, defaults=None):
    """ffmpeg ifadesi: değer(tv - off) * scale + add (keyframe yoksa sabit)."""
    ks = keys(obj, prop)
    if len(ks) < 2:
        v = value(obj, prop, 0, defaults) * scale + add
        return f"{v:.4f}"
    T = f"({tv}-{off:.4f})"
    e = f"{float(ks[-1]['v']) * scale + add:.4f}"
    for a, b in reversed(list(zip(ks, ks[1:]))):
        va, vb = float(a["v"]) * scale + add, float(b["v"]) * scale + add
        if a.get("ease") == "hold":
            seg = f"{va:.4f}"
        else:
            u = f"(({T}-{a['t']:.4f})/{max(1e-4, b['t'] - a['t']):.4f})"
            oe, ie = a.get("ease", "lin") in ("ease", "out"), b.get("ease", "lin") in ("ease", "in")
            if oe and ie:
                uu = f"({u}*{u}*(3-2*{u}))"
            elif oe:
                uu = f"(1-(1-{u})*(1-{u}))"
            elif ie:
                uu = f"({u}*{u})"
            else:
                uu = u
            seg = f"({va:.4f}+({vb - va:.4f})*{uu})"
        e = f"if(lt({T},{b['t']:.4f}),{seg},{e})"
    first = float(ks[0]["v"]) * scale + add
    return f"if(lt({T},{ks[0]['t']:.4f}),{first:.4f},{e})"


def max_scale(obj, defaults=None):
    ks = keys(obj, "scale")
    vals = [float(k["v"]) for k in ks] or [tf_of(obj, defaults)["scale"]]
    return max(1.0, max(vals))


def has_rotation(obj, defaults=None):
    ks = keys(obj, "rot")
    return bool(ks and any(abs(float(k["v"])) > 0.01 for k in ks)) or abs(tf_of(obj, defaults)["rot"]) > 0.01


def has_opacity(obj, defaults=None):
    return len(keys(obj, "op")) >= 2


def static_op(obj, defaults=None):
    return max(0.0, min(1.0, value(obj, "op", 0, defaults) / 100))


def visual_chain(src_label, out_label, obj, base_w, OW, OH, inner_off, outer_off, defaults=None):
    """Resim / üst video için: ölçek + döndürme + opaklık. Dönüş: (filtreler, x_ifadesi, y_ifadesi)
    base_w: ölçek %100 iken piksel genişliği. inner_off: dal içindeki filtrelerde 't'den çıkarılacak süre,
    outer_off: overlay (konum) ifadelerinde çıkarılacak süre."""
    f = []
    off = inner_off
    sc = expr(obj, "scale", "t", off, base_w / 100.0, defaults=defaults)
    dyn_scale = len(keys(obj, "scale")) >= 2
    rot = has_rotation(obj, defaults)
    chain = f"[{src_label}]"
    if dyn_scale:
        chain += f"scale=w='max(2,trunc({sc}/2)*2)':h=-2:eval=frame,format=rgba"
    else:
        w = max(2, int(float(sc)) // 2 * 2)
        chain += f"scale={w}:-2,format=rgba"
    if rot or dyn_scale:
        # sabit tuval (dönerken/büyürken boyut değişmesin)
        C = int(math.ceil(base_w * max_scale(obj, defaults) / 100 * 1.5)) // 2 * 2 + 4
        chain += f",pad={C}:{C}:(ow-iw)/2:(oh-ih)/2:color=black@0:eval=frame"
        if rot:
            r = expr(obj, "rot", "t", off, math.pi / 180, defaults=defaults)
            chain += f",rotate=a='{r}':c=none:ow={C}:oh={C}"
    if has_opacity(obj, defaults):
        o = expr(obj, "op", "T", off, 0.01, defaults=defaults)
        chain += f",geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='alpha(X,Y)*clip({o},0,1)'"
    else:
        op = static_op(obj, defaults)
        if op < 0.995:
            chain += f",colorchannelmixer=aa={op:.3f}"
    f.append(chain + f"[{out_label}]")
    x = f"({expr(obj, 'x', 't', outer_off, OW, defaults=defaults)})-w/2"
    y = f"({expr(obj, 'y', 't', outer_off, OH, defaults=defaults)})-h/2"
    return f, x, y
