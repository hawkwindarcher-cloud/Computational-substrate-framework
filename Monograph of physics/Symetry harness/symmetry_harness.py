
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import pandas as pd

# -----------------------------
# Core combiners (on slowness)
# -----------------------------

def combined_slowness(slownesses: List[float], p: float) -> float:
    """
    Generalized mean of order p applied to slownesses.
    p=1 -> arithmetic mean (L1 kernel on slowness)
    p=2 -> RMS (L2 kernel on slowness)
    """
    m = len(slownesses)
    if m == 0:
        raise ValueError("Need at least one slowness value")
    if p == 0:
        # Geometric mean limit, not used here, but included for completeness
        prod = 1.0
        for s in slownesses:
            prod *= max(s, 1e-30)
        return prod ** (1.0/m)
    # Standard generalized mean
    acc = sum((s ** p) for s in slownesses) / m
    return acc ** (1.0 / p)

def predict_diagonal_speed_from_axes(vx: float, vy: float, vz: float,
                                     which: str = "face_xy",
                                     p: int = 1) -> float:
    """
    Predict diagonal speed using generalized-mean combiner on slowness.
      which: 'face_xy','face_yz','face_zx','body_xyz'
      p: 1 for L1 (mean), 2 for L2 (RMS) on slowness
    """
    # slowness
    sx, sy, sz = (1.0/max(vx,1e-30), 1.0/max(vy,1e-30), 1.0/max(vz,1e-30))
    if which == "face_xy":
        s = combined_slowness([sx, sy], p)
    elif which == "face_yz":
        s = combined_slowness([sy, sz], p)
    elif which == "face_zx":
        s = combined_slowness([sz, sx], p)
    elif which == "body_xyz":
        s = combined_slowness([sx, sy, sz], p)
    else:
        raise ValueError("Unknown direction")
    return 1.0 / max(s, 1e-30)

# -----------------------------
# Symmetry classes & checks
# -----------------------------

Direction = Tuple[int,int,int]  # components in {-1,0,1}

AXES: List[Direction] = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
FACES: List[Direction] = [
    (1,1,0), (1,-1,0), (-1,1,0), (-1,-1,0),
    (1,0,1), (1,0,-1), (-1,0,1), (-1,0,-1),
    (0,1,1), (0,1,-1), (0,-1,1), (0,-1,-1),
]
BODIES: List[Direction] = [
    (1,1,1),(1,1,-1),(1,-1,1),(1,-1,-1),
    (-1,1,1),(-1,1,-1),(-1,-1,1),(-1,-1,-1)
]

def opposite(d: Direction) -> Direction:
    return (-d[0], -d[1], -d[2])

def reldiff(a: float, b: float) -> float:
    denom = 0.5*(abs(a)+abs(b))
    if denom == 0.0:
        return 0.0
    return abs(a-b)/denom

@dataclass
class SymmetryResult:
    parity_pass: bool
    perm_pass_axes: bool
    perm_pass_faces: bool
    perm_pass_bodies: bool
    eps: float
    # diagnostics
    worst_parity: float
    worst_axes: float
    worst_faces: float
    worst_bodies: float

def check_symmetry(measured_speeds: Dict[Direction,float], eps: float = 0.02) -> SymmetryResult:
    # Parity checks
    worst_par = 0.0
    for d, v in measured_speeds.items():
        dneg = opposite(d)
        if dneg in measured_speeds:
            rd = reldiff(v, measured_speeds[dneg])
            worst_par = max(worst_par, rd)
    parity_pass = worst_par <= eps

    # Permutation within classes
    def worst_within(dirs: List[Direction]) -> float:
        vals = [measured_speeds[d] for d in dirs if d in measured_speeds]
        worst = 0.0
        for i in range(len(vals)):
            for j in range(i+1, len(vals)):
                worst = max(worst, reldiff(vals[i], vals[j]))
        return worst if len(vals) >= 2 else 0.0

    worst_axes = worst_within(AXES)
    worst_faces = worst_within(FACES)
    worst_bodies = worst_within(BODIES)
    return SymmetryResult(
        parity_pass = parity_pass,
        perm_pass_axes = worst_axes <= eps,
        perm_pass_faces = worst_faces <= eps,
        perm_pass_bodies = worst_bodies <= eps,
        eps = eps,
        worst_parity = worst_par,
        worst_axes = worst_axes,
        worst_faces = worst_faces,
        worst_bodies = worst_bodies
    )

# -----------------------------
# Fit L1 vs L2 from diagonals
# -----------------------------

def classify_kernel(vx: float, vy: float, vz: float,
                    measured: Dict[str, float]) -> pd.DataFrame:
    """
    measured: mapping of {'face_xy','face_yz','face_zx','body_xyz'} -> measured diagonal speeds
    Returns a dataframe with predictions and residuals.
    """
    rows = []
    for which in ['face_xy','face_yz','face_zx','body_xyz']:
        meas = measured.get(which, math.nan)
        pred_L1 = predict_diagonal_speed_from_axes(vx, vy, vz, which, p=1)
        pred_L2 = predict_diagonal_speed_from_axes(vx, vy, vz, which, p=2)
        rows.append({
            'direction': which,
            'measured_v': meas,
            'pred_L1_v': pred_L1,
            'pred_L2_v': pred_L2,
            'abs_err_L1': abs(meas - pred_L1) if not math.isnan(meas) else math.nan,
            'abs_err_L2': abs(meas - pred_L2) if not math.isnan(meas) else math.nan,
        })
    df = pd.DataFrame(rows)
    # Compute simple MSEs (ignoring NaNs)
    mse_L1 = ((df['abs_err_L1']**2).mean(skipna=True))
    mse_L2 = ((df['abs_err_L2']**2).mean(skipna=True))
    verdict = "L1-like" if (mse_L1 < mse_L2) else "L2-like"
    df.attrs['mse_L1'] = mse_L1
    df.attrs['mse_L2'] = mse_L2
    df.attrs['verdict'] = verdict
    return df

# -----------------------------
# CSV IO helpers
# -----------------------------

CSV_TEMPLATE = """direction,v_measured
+X,1.00
-X,1.00
+Y,0.80
-Y,0.80
+Z,0.50
-Z,0.50
+XY,0.888   # example: face diagonal speed
-XY,0.888
+YZ,0.615
-YZ,0.615
+ZX,0.667
-ZX,0.667
+XYZ,0.714  # example: body diagonal speed
-XYZ,0.714
"""

DIRECTION_MAP: Dict[str, Direction] = {
    "+X": (1,0,0), "-X": (-1,0,0),
    "+Y": (0,1,0), "-Y": (0,-1,0),
    "+Z": (0,0,1), "-Z": (0,0,-1),
    "+XY": (1,1,0), "-XY": (-1,-1,0),
    "+YZ": (0,1,1), "-YZ": (0,-1,-1),
    "+ZX": (1,0,1), "-ZX": (-1,0,-1),
    "+XYZ": (1,1,1), "-XYZ": (-1,-1,-1),
}

def read_measurements_csv(path: str) -> Dict[Direction, float]:
    # Parse CSV with potential comments
    raw = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # remove inline comments after '#'
            if "#" in line:
                line = line[:line.index("#")].strip()
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 2:
                continue
            lab, val = parts
            if lab not in DIRECTION_MAP:
                continue
            try:
                v = float(val)
            except ValueError:
                continue
            raw.append((DIRECTION_MAP[lab], v))
    return dict(raw)

def to_diag_key(d: Direction) -> Optional[str]:
    x,y,z = d
    if (x!=0)+(y!=0)+(z!=0) == 1:
        return None  # axis, not a diagonal combiner target
    if z == 0 and x!=0 and y!=0:
        return "face_xy"
    if x == 0 and y!=0 and z!=0:
        return "face_yz"
    if y == 0 and z!=0 and x!=0:
        return "face_zx"
    if x!=0 and y!=0 and z!=0:
        return "body_xyz"
    return None

# -----------------------------
# Demo / Example
# -----------------------------
if __name__ == "__main__":
    # Example axis speeds (user should replace with real data)
    vx, vy, vz = 1.00, 0.80, 0.50
    # Save a CSV template for convenience
    with open("/mnt/data/example_measurements.csv", "w", encoding="utf-8") as f:
        f.write(CSV_TEMPLATE)
    print("Wrote template: /mnt/data/example_measurements.csv")

    # Build a synthetic measurement dict consistent with L1 on slowness
    # (So the classifier should pick L1-like)
    sx, sy, sz = 1.0/vx, 1.0/vy, 1.0/vz
    synth = {
        (1,0,0): vx, (-1,0,0): vx,
        (0,1,0): vy, (0,-1,0): vy,
        (0,0,1): vz, (0,0,-1): vz,
    }
    # L1 predictions for diagonals used as synthetic 'measured' values
    l1_face_xy = 1.0 / ((sx+sy)/2.0)
    l1_face_yz = 1.0 / ((sy+sz)/2.0)
    l1_face_zx = 1.0 / ((sz+sx)/2.0)
    l1_body = 1.0 / ((sx+sy+sz)/3.0)
    synth.update({
        (1,1,0): l1_face_xy, (-1,-1,0): l1_face_xy,
        (0,1,1): l1_face_yz, (0,-1,-1): l1_face_yz,
        (1,0,1): l1_face_zx, (-1,0,-1): l1_face_zx,
        (1,1,1): l1_body, (-1,-1,-1): l1_body,
    })

    # Symmetry check
    sym = check_symmetry(synth, eps=0.02)
    print(f"Parity pass: {sym.parity_pass} (worst={sym.worst_parity:.4f})")
    print(f"Axes perm pass: {sym.perm_pass_axes} (worst={sym.worst_axes:.4f})")
    print(f"Faces perm pass: {sym.perm_pass_faces} (worst={sym.worst_faces:.4f})")
    print(f"Bodies perm pass: {sym.perm_pass_bodies} (worst={sym.worst_bodies:.4f})")

    # Kernel classification from diagonals
    measured_diags = {
        "face_xy": synth[(1,1,0)],
        "face_yz": synth[(0,1,1)],
        "face_zx": synth[(1,0,1)],
        "body_xyz": synth[(1,1,1)],
    }
    df = classify_kernel(vx, vy, vz, measured_diags)
    print(f"Verdict: {df.attrs['verdict']} (MSE L1={df.attrs['mse_L1']:.6g}, MSE L2={df.attrs['mse_L2']:.6g})")
    print(df.to_string(index=False))

    # Save a nice CSV of predictions vs measurements
    out = df.copy()
    out.to_csv("/mnt/data/diagonal_predictions_vs_measurements.csv", index=False)
    print("Saved: /mnt/data/diagonal_predictions_vs_measurements.csv")
