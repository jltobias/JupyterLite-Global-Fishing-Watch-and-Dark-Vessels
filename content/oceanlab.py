"""Transparent, browser-compatible teaching models and visualizations.

Real data: Paolo et al. 2024 (CC BY 4.0), Natural Earth (public domain).
Every synthetic result is labeled. No function establishes illegality or disease.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import plotly.graph_objects as go
from scipy.ndimage import uniform_filter, maximum_filter
from scipy.optimize import linear_sum_assignment

DATA = Path(__file__).resolve().parent / "data"
NAVY, TEAL, AMBER, GRAY = "#081f32", "#27c7b8", "#ffc66a", "#8ba5b5"
SOURCE = "Paolo et al. (2024) · 2017–2021 study · CC BY 4.0"


def style():
    plt.rcParams.update({"figure.figsize": (11, 5.8), "figure.dpi": 110,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titleweight": "bold", "axes.labelcolor": "#203e54",
        "font.size": 10, "savefig.bbox": "tight"})


def activity(full=False):
    if full:
        with np.load(DATA / "sar_activity_2017_2021.npz") as a:
            return pd.DataFrame({k: a[k] for k in a.files})
    return pd.read_csv(DATA / "sar_activity_1deg.csv")


def coastline():
    d = json.loads((DATA / "coastline.geojson").read_text(encoding="utf-8"))
    lines = []
    for feature in d["features"]:
        g = feature["geometry"]
        if g["type"] == "LineString":
            lines.append(np.array(g["coordinates"]))
        elif g["type"] == "MultiLineString":
            lines.extend(np.array(c) for c in g["coordinates"])
    return lines


def map2d(field="tot_fishing", bbox=(-180, -60, 180, 80)):
    style()
    d = activity()
    west, south, east, north = bbox
    d = d[d.lon.between(west, east) & d.lat.between(south, north)]
    d = d[np.isfinite(d[field]) & (d[field] > 0)]
    if d.empty:
        raise ValueError("No positive observations in this region; choose a wider bounding box.")
    fig, ax = plt.subplots(facecolor=NAVY)
    ax.set_facecolor(NAVY)
    for line in coastline():
        ax.plot(line[:, 0], line[:, 1], color="#668997", lw=.45)
    vmin = max(float(d[field].quantile(.02)), 1e-5)
    vmax = max(float(d[field].max()), vmin * 1.01)
    p = ax.scatter(d.lon, d.lat, c=d[field], s=9, marker="s", cmap="viridis", norm=LogNorm(vmin=vmin, vmax=vmax))
    ax.set(xlim=(west, east), ylim=(south, north), xlabel="Longitude (°)", ylabel="Latitude (°)")
    labels={"tot_fishing":"Fishing vessel activity", "dark_fishing":"Unmatched fishing component", "AIS_fishing":"AIS-matched fishing component"}
    ax.set_title("The observed ocean | " + labels.get(field,field), color="white", pad=16)
    ax.tick_params(colors="#b1ccd7")
    ax.xaxis.label.set_color("#b1ccd7"); ax.yaxis.label.set_color("#b1ccd7")
    cb = fig.colorbar(p, ax=ax, pad=.02, shrink=.8)
    cb.set_label("Sum of normalized activity in 1° bin\n(expected detections per overpass across source cells)", color="#b1ccd7")
    cb.ax.tick_params(colors="#b1ccd7")
    fig.text(.08, -.01, SOURCE + " | Coastline: Natural Earth | Equirectangular | Empty ≠ zero", color="#a4c0ce", fontsize=8)
    return fig


def interactive_map(bbox=(-20, 40, 35, 70)):
    d = activity()
    w, s, e, n = bbox
    d = d[d.lon.between(w, e) & d.lat.between(s, n)].copy()
    d = d[d.tot_fishing > 0]
    fig = go.Figure()
    for line in coastline():
        fig.add_trace(go.Scattergl(x=line[:, 0], y=line[:, 1], mode="lines", line=dict(color=GRAY, width=.6), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scattergl(x=d.lon, y=d.lat, mode="markers",
        customdata=d[["tot_fishing", "dark_fishing"]].to_numpy(),
        marker=dict(size=9, color=np.log10(d.tot_fishing), colorscale="Viridis", colorbar=dict(title="log10<br>activity proxy")),
        hovertemplate="%{x:.1f}°E, %{y:.1f}°N<br>Activity proxy: %{customdata[0]:.3f}<br>Unmatched component: %{customdata[1]:.3f}<extra></extra>", showlegend=False))
    fig.update_layout(template="plotly_dark", paper_bgcolor=NAVY, plot_bgcolor=NAVY,
        title="Zoom into the evidence | observed SAR activity, 2017–2021", height=580,
        xaxis=dict(title="Longitude (°)", range=[w, e]), yaxis=dict(title="Latitude (°)", range=[s, n]),
        margin=dict(l=45, r=20, t=65, b=70),
        annotations=[dict(text=SOURCE + "<br>1° bin sums; not fishing hours or unique vessels. Coastline: Natural Earth.",
                          x=0, y=-.17, xref="paper", yref="paper", showarrow=False, align="left", font=dict(size=10))])
    return fig


def sphere(lon, lat, radius=1):
    lo, la = np.deg2rad(lon), np.deg2rad(lat)
    return radius * np.cos(la) * np.cos(lo), radius * np.cos(la) * np.sin(lo), radius * np.sin(la)


def globe():
    d = activity()
    d = d[d.tot_fishing > 0].copy()
    lo, la = np.meshgrid(np.linspace(-180, 180, 100), np.linspace(-90, 90, 60))
    x, y, z = sphere(lo, la)
    fig = go.Figure(go.Surface(x=x, y=y, z=z, surfacecolor=np.zeros_like(x),
        colorscale=[[0, "#0d384e"], [1, "#0d384e"]], showscale=False, hoverinfo="skip", opacity=.96))
    for line in coastline():
        x, y, z = sphere(line[:, 0], line[:, 1], 1.005)
        fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode="lines", line=dict(color="#8daeb7", width=2), showlegend=False, hoverinfo="skip"))
    x, y, z = sphere(d.lon.to_numpy(), d.lat.to_numpy(), 1.012)
    fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode="markers", customdata=d[["lon", "lat", "tot_fishing"]].to_numpy(),
        marker=dict(size=2.5, color=np.log10(d.tot_fishing), colorscale="Viridis", colorbar=dict(title="log10<br>activity proxy")),
        hovertemplate="%{customdata[0]:.1f}°, %{customdata[1]:.1f}°<br>Proxy: %{customdata[2]:.3f}<extra></extra>", showlegend=False))
    fig.update_layout(template="plotly_dark", paper_bgcolor=NAVY, title="An ocean without map edges | drag to rotate",
        height=650, scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
                              aspectmode="data", bgcolor=NAVY, camera=dict(eye=dict(x=1.4, y=.8, z=.6))),
        margin=dict(l=0, r=20, t=65, b=55),
        annotations=[dict(text=SOURCE + " | Coastline: Natural Earth<br>Color = summed normalized activity; marker altitude is illustrative.", x=0, y=0, xref="paper", yref="paper", showarrow=False, align="left", font=dict(size=10))])
    return fig


def ocean_scene():
    x, y = np.meshgrid(np.linspace(-10, 10, 55), np.linspace(-10, 10, 55))
    depth = -0.5 - 2 / (1 + np.exp(-(x - 1))) + .12 * np.sin(y)
    fig = go.Figure(go.Surface(x=x, y=y, z=depth, colorscale="Teal", showscale=False, name="Seafloor", hovertemplate="Synthetic seafloor<extra></extra>"))
    fig.add_trace(go.Surface(x=x, y=y, z=x * 0, opacity=.25, colorscale=[[0, TEAL], [1, TEAL]], showscale=False, hoverinfo="skip"))
    for target in [(-3, -1), (1, 2), (4, -2)]:
        fig.add_trace(go.Scatter3d(x=[-4, target[0]], y=[-5, target[1]], z=[8, 0], mode="lines", line=dict(color=AMBER, width=3), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(x=[-4, -3, 1, 4, 6], y=[-5, -1, 2, -2, 5], z=[8, 0, 0, 0, -.5], mode="markers+text",
        text=["Radar satellite", "Vessel A", "Vessel B", "Vessel C", "Coastal ecosystem"], textposition="top center",
        marker=dict(size=[8, 5, 5, 5, 8], color=[AMBER, TEAL, AMBER, TEAL, TEAL]), showlegend=False))
    fig.update_layout(title="From orbit to ecosystem | conceptual 3D scene", template="plotly_dark", paper_bgcolor=NAVY,
        height=650, scene=dict(xaxis_title="Illustrative distance", yaxis_title="Illustrative distance", zaxis_title="Illustrative height / depth", aspectratio=dict(x=1.3, y=1.3, z=1)),
        annotations=[dict(text="SYNTHETIC SCENE · Heights, beam geometry and bathymetry are not measurements.<br>SAR observes surface backscatter; it does not see through seawater to fish or seabed.", x=0, y=0, xref="paper", yref="paper", showarrow=False, align="left", font=dict(size=11))], margin=dict(l=0, r=0, t=60, b=60))
    return fig


def haversine_km(lon1, lat1, lon2, lat2):
    lo1, la1, lo2, la2 = map(np.deg2rad, [lon1, lat1, lon2, lat2])
    a = np.sin((la2-la1)/2)**2 + np.cos(la1)*np.cos(la2)*np.sin((lo2-lo1)/2)**2
    return 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def match_points(detections, ais, max_km=3, max_minutes=15):
    """One-to-one minimum cost assignment with explicit unmatched choices.

    Positions are assumed already projected to acquisition time. This exercise
    uses a simple distance/time score, not GFW's production matching algorithm.
    """
    if max_km <= 0 or max_minutes <= 0:
        raise ValueError("Both matching gates must be positive")
    out = detections.copy().reset_index(drop=True)
    out["match"] = pd.Series([None] * len(out), dtype="object")
    out["distance_km"] = np.nan
    if out.empty or ais.empty:
        return out
    a = ais.reset_index(drop=True)
    dist = haversine_km(out.lon.to_numpy()[:, None], out.lat.to_numpy()[:, None],
                        a.lon.to_numpy()[None, :], a.lat.to_numpy()[None, :])
    dt = np.abs(out.minute.to_numpy()[:, None] - a.minute.to_numpy()[None, :])
    valid = (dist <= max_km) & (dt <= max_minutes)
    score = np.where(valid, dist / max_km + dt / max_minutes, 1e6)
    # A large unmatched penalty first maximizes valid matches, then minimizes
    # their total score. Dummy columns prevent a forced invalid assignment.
    cost = np.column_stack([score, np.full((len(out), len(out)), 10 * (len(out) + 1))])
    rows, cols = linear_sum_assignment(cost)
    for row, col in zip(rows, cols):
        if col < len(a) and valid[row, col]:
            out.loc[row, "match"] = str(a.loc[col, "id"])
            out.loc[row, "distance_km"] = float(dist[row, col])
    return out


def matching_demo():
    rng = np.random.default_rng(31)
    ais = pd.DataFrame({"id": [f"demo-{n}" for n in range(10)],
        "lon": 12 + rng.uniform(0, .45, 10), "lat": 54.5 + rng.uniform(0, .22, 10), "minute": rng.uniform(-8, 8, 10)})
    sar = ais.iloc[:7][["lon", "lat"]].copy()
    sar += rng.normal(0, .003, sar.shape)
    sar["minute"] = 0.
    sar = pd.concat([sar, pd.DataFrame({"lon": [12.42, 12.08, 12.25], "lat": [54.72, 54.51, 54.70], "minute": [0., 0., 0.]})], ignore_index=True)
    return sar, ais


def radar(seed=7, size=160):
    """Single-look exponential speckle with injected Gaussian bright targets."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[:size, :size]
    land = x < 18 + 4 * np.sin(y / 15)
    mean = .012 * (1 + .5 * x / size)
    intensity = rng.exponential(mean)
    truth = np.array([[45, 42], [75, 110], [116, 65], [132, 131]])  # y, x
    for ty, tx in truth:
        intensity += .8 * np.exp(-((x-tx)**2 + (y-ty)**2) / 1.4)
    intensity[land] += rng.exponential(.7, int(land.sum()))
    return intensity, land, truth


def radar_detect(intensity, land, alpha=7, outer=15, guard=5):
    """Toy CA-CFAR-like local contrast, in linear intensity (not dB)."""
    if intensity.shape != land.shape or intensity.ndim != 2:
        raise ValueError("Intensity and land mask must be matching 2D arrays")
    if outer <= guard or outer % 2 != 1 or guard % 2 != 1 or alpha <= 0:
        raise ValueError("Use positive alpha and odd outer > guard windows")
    ocean = ~land & np.isfinite(intensity)
    values = np.where(ocean, intensity, 0.)
    outer_sum = uniform_filter(values, outer, mode="constant") * outer**2
    inner_sum = uniform_filter(values, guard, mode="constant") * guard**2
    count = (uniform_filter(ocean.astype(float), outer, mode="constant") * outer**2 -
             uniform_filter(ocean.astype(float), guard, mode="constant") * guard**2)
    background = np.maximum(outer_sum-inner_sum, 0) / np.maximum(count, 1)
    valid = ocean & (count >= .85 * (outer**2-guard**2))
    edge = outer // 2
    valid[:edge] = valid[-edge:] = False
    valid[:, :edge] = valid[:, -edge:] = False
    candidate = valid & (intensity > alpha * background) & (intensity == maximum_filter(values, size=5))
    return np.argwhere(candidate), background


def detection_metrics(points, truth, tolerance=3):
    if len(points) == 0:
        return {"tp": 0, "fp": 0, "fn": len(truth), "precision": 0., "recall": 0.}
    if len(truth) == 0:
        return {"tp": 0, "fp": len(points), "fn": 0, "precision": 0., "recall": 0.}
    dist = np.linalg.norm(points[:, None, :] - truth[None, :, :], axis=2)
    costs = np.column_stack([np.where(dist <= tolerance, dist, 1e6), np.full((len(points), len(points)), 1000.)])
    r, c = linear_sum_assignment(costs)
    tp = sum(col < len(truth) and dist[row, col] <= tolerance for row, col in zip(r, c))
    return {"tp": int(tp), "fp": len(points)-int(tp), "fn": len(truth)-int(tp), "precision": tp/len(points), "recall": tp/len(truth)}


def radar_plot(alpha=7):
    image, land, truth = radar()
    points, background = radar_detect(image, land, alpha=alpha)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    for ax, array, title in zip(axes, [10*np.log10(image), land, image / np.maximum(background, 1e-9)],
                                ["Backscatter (dB)", "Land exclusion mask", f"Local contrast; α = {alpha}"]):
        p = ax.imshow(array, cmap="viridis", vmin=-30 if ax is axes[0] else None, vmax=0 if ax is axes[0] else None)
        ax.set_title(title); ax.set_xlabel("Pixel column"); ax.set_ylabel("Pixel row")
        fig.colorbar(p, ax=ax, shrink=.7)
    axes[2].scatter(truth[:, 1], truth[:, 0], facecolors="none", edgecolors=TEAL, s=90, label="Injected target")
    if len(points):
        axes[2].scatter(points[:, 1], points[:, 0], marker="x", c="#cc572a", label="Candidate")
    axes[2].legend(fontsize=7)
    fig.suptitle("SYNTHETIC RADAR | bright does not necessarily mean vessel", fontweight="bold")
    return fig


def radar_surface():
    image, _, _ = radar()
    crop = 10 * np.log10(image[30:60, 28:58])
    fig = go.Figure(go.Surface(z=crop, colorscale="Viridis", colorbar=dict(title="dB")))
    fig.update_layout(title="SYNTHETIC RADAR | a target rising above speckle", template="plotly_dark", paper_bgcolor=NAVY,
        scene=dict(xaxis_title="Pixel column", yaxis_title="Pixel row", zaxis_title="Backscatter (dB)"), height=580,
        annotations=[dict(text="Height represents backscatter, not vessel height. Injected target; no satellite pixels.", x=0, y=0, xref="paper", yref="paper", showarrow=False)], margin=dict(l=0, r=0, t=60, b=50))
    return fig


def stock_model(fishing_mortality=.25, r=.4, K=1000., B0=600., years=40, dt=.05):
    """Schaefer logistic biomass model, dimensionless educational stock."""
    if min(r, K, B0, years, dt) <= 0 or fishing_mortality < 0:
        raise ValueError("Positive r, K, B0, years, dt and nonnegative mortality required")
    t = np.arange(0, years+dt/2, dt)
    b = np.empty(len(t)); b[0] = B0
    for i in range(1, len(t)):
        b[i] = max(0., b[i-1] + dt * (r*b[i-1]*(1-b[i-1]/K) - fishing_mortality*b[i-1]))
    return t, b


def stock_slider():
    fig = go.Figure()
    rates = [.1, .2, .3, .4, .5]
    for i, rate in enumerate(rates):
        t, b = stock_model(fishing_mortality=rate)
        fig.add_trace(go.Scatter(x=t, y=b, visible=i == 1, line=dict(color=TEAL, width=3), name=f"F = {rate}"))
    steps = [dict(method="update", args=[{"visible": [i == j for j in range(len(rates))]}], label=str(rate)) for i, rate in enumerate(rates)]
    fig.update_layout(title="SYNTHETIC STOCK | changing fishing mortality changes the trajectory", template="plotly_dark", paper_bgcolor=NAVY,
        xaxis_title="Model year", yaxis=dict(title="Biomass (illustrative units)", range=[0, 1050]), height=600,
        sliders=[dict(active=1, currentvalue=dict(prefix="Fishing mortality F (year⁻¹): "), steps=steps)],
        annotations=[dict(text="r = 0.4 year⁻¹; K = 1000; B₀ = 600. No calibration to any real fishery.", x=0, y=1.05, xref="paper", yref="paper", showarrow=False)], margin=dict(b=120))
    fig.add_hline(y=500, line_dash="dot", annotation_text="BMSY = K/2 in this model only")
    return fig


def environment(seed=42):
    rng = np.random.default_rng(seed)
    month = np.arange(120)
    season = np.sin(2*np.pi*month/12)
    sst = 16 + 6*season + .02*month + rng.normal(0, .6, len(month))
    chl = np.exp(.2 + .5*np.sin(2*np.pi*(month-2)/12) + rng.normal(0, .22, len(month)))
    effort = 80 + 20*season + .3*month + rng.normal(0, 8, len(month))
    return pd.DataFrame({"month": month, "sst_c": sst, "chlorophyll_mg_m3": chl, "effort_hours": effort})


def food_scenario(retention=.45, edible_fraction=.65, loss=.15, catch_tonnes=1000, population=100000):
    if not all(0 <= v <= 1 for v in [retention, edible_fraction, loss]) or catch_tonnes < 0 or population <= 0:
        raise ValueError("Fractions must be in [0,1], catch nonnegative, population positive")
    edible = catch_tonnes * 1000 * retention * edible_fraction * (1-loss)
    return {"edible_kg": edible, "grams_per_person_per_day": edible*1000/population/365,
            "illustrative_protein_g_day": edible*1000/population/365*.20}


def show(fig):
    """Isolate scripts in an iframe so JupyterLab waits for Plotly to load."""
    import html
    import sys
    from IPython.display import display
    script="../plotly.min.js" if sys.platform=="emscripten" else "cdn"
    document=fig.to_html(full_html=True, include_plotlyjs=script,
                         config={"responsive": True, "displaylogo": False})
    title=html.escape(str(fig.layout.title.text or "Interactive figure"),quote=True)
    markup=(f'<iframe title="{title}" srcdoc="{html.escape(document,quote=True)}" '
            'style="width:100%;height:700px;border:0" loading="eager"></iframe>')
    display({"text/html":markup},raw=True)


style()
