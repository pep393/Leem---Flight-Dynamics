"""
Rocket Flight Simulation Analysis (Monte Carlo).

Reads a .txt file where EACH LINE is an independent JSON object (a simulation),
with keys potentially in different order between lines, but following the same schema.

Generates interactive HTML plots:
  1. 3D Plot of all trajectories (x, y, z_agl / z).
  2. Impact Map (x_impact, y_impact) with 1-sigma and 2-sigma covariance ellipses
     and small scatter markers.
  3. Frequency histograms for scalar variables with Mean and Mean ± Std Dev lines.
  4. CSV statistical summary report.

Usage:
    python analisis_simulaciones.py path_to_file.txt [--outdir output_folder]
"""

import json
import argparse
import os
import numpy as np
import plotly.graph_objects as go


# ----------------------------------------------------------------------
# 1. FILE READING
# ----------------------------------------------------------------------
def read_simulations(path):
    """Reads the .txt file line-by-line and returns a list of dictionaries."""
    simulations = []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    decoder = json.JSONDecoder()
    idx = 0
    n = len(content)
    while idx < n:
        while idx < n and content[idx] in " \t\r\n":
            idx += 1
        if idx >= n:
            break
        obj, end = decoder.raw_decode(content, idx)
        simulations.append(obj)
        idx = end

    if not simulations:
        raise ValueError("Could not read any valid simulation JSON from the file.")
    return simulations


# ----------------------------------------------------------------------
# 2. INTERACTIVE 3D TRAJECTORIES
# ----------------------------------------------------------------------
def plot_3d_trajectories(simulations, outdir):
    fig = go.Figure()

    for i, sim in enumerate(simulations):
        traj = sim.get("trajectory")
        if not traj:
            continue
        x = traj.get("x")
        y = traj.get("y")
        z = traj.get("z_agl", traj.get("z"))
        if x is None or y is None or z is None:
            continue

        fig.add_trace(
            go.Scatter3d(
                x=x,
                y=y,
                z=z,
                mode="lines",
                line=dict(width=2),
                opacity=0.4,
                name=f"Sim {i+1}",
                showlegend=False
            )
        )

    fig.update_layout(
        title=dict(
            text=f"3D Flight Trajectories ({len(simulations)} simulations)",
            font=dict(size=22)
        ),
        font=dict(size=16),
        scene=dict(
            xaxis=dict(title=dict(text="X Position (m)", font=dict(size=16)), tickfont=dict(size=14)),
            yaxis=dict(title=dict(text="Y Position (m)", font=dict(size=16)), tickfont=dict(size=14)),
            zaxis=dict(title=dict(text="Altitude AGL (m)", font=dict(size=16)), tickfont=dict(size=14))
        ),
        margin=dict(l=0, r=0, b=0, t=50)
    )

    output_path = os.path.join(outdir, "3d_trajectories.html")
    fig.write_html(output_path)
    print(f"Saved: {output_path}")


# ----------------------------------------------------------------------
# 3. IMPACT MAP WITH COVARIANCE ELLIPSES (1σ AND 2σ)
# ----------------------------------------------------------------------
def calculate_covariance_ellipse(x, y, n_std=1, num_points=200):
    """Calculates coordinates of a covariance ellipse for standard deviation n_std."""
    cov = np.cov(x, y)
    mean_x, mean_y = np.mean(x), np.mean(y)

    vals, vecs = np.linalg.eigh(cov)
    order = vals.argsort()[::-1]
    vals, vecs = vals[order], vecs[:, order]

    rx = n_std * np.sqrt(vals[0])
    ry = n_std * np.sqrt(vals[1])

    theta = np.linspace(0, 2 * np.pi, num_points)
    ellipse_coords = np.array([rx * np.cos(theta), ry * np.sin(theta)])
    rotated_coords = np.dot(vecs, ellipse_coords)

    x_ellipse = rotated_coords[0, :] + mean_x
    y_ellipse = rotated_coords[1, :] + mean_y
    return x_ellipse, y_ellipse


def plot_impact_map(simulations, outdir):
    x_impact = np.array([s["x_impact"] for s in simulations if "x_impact" in s])
    y_impact = np.array([s["y_impact"] for s in simulations if "y_impact" in s])

    if len(x_impact) == 0 or len(y_impact) == 0:
        print("Warning: No impact coordinates ('x_impact', 'y_impact') found.")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x_impact,
            y=y_impact,
            mode="markers",
            marker=dict(size=4, color="steelblue", opacity=0.7),
            name="Impact Points"
        )
    )

    mean_x, mean_y = np.mean(x_impact), np.mean(y_impact)
    fig.add_trace(
        go.Scatter(
            x=[mean_x],
            y=[mean_y],
            mode="markers",
            marker=dict(size=12, color="crimson", symbol="x"),
            name=f"Mean ({mean_x:.2f}, {mean_y:.2f})"
        )
    )

    e1_x, e1_y = calculate_covariance_ellipse(x_impact, y_impact, n_std=1)
    fig.add_trace(
        go.Scatter(
            x=e1_x,
            y=e1_y,
            mode="lines",
            line=dict(color="darkorange", width=2, dash="dash"),
            name="1σ Ellipse"
        )
    )

    e2_x, e2_y = calculate_covariance_ellipse(x_impact, y_impact, n_std=2)
    fig.add_trace(
        go.Scatter(
            x=e2_x,
            y=e2_y,
            mode="lines",
            line=dict(color="firebrick", width=2, dash="dashdot"),
            name="2σ Ellipse"
        )
    )

    fig.update_layout(
        title=dict(text="Impact Dispersion Map", font=dict(size=22)),
        font=dict(size=16),
        xaxis=dict(title=dict(text="Impact X (m)", font=dict(size=18)), tickfont=dict(size=14)),
        yaxis=dict(title=dict(text="Impact Y (m)", font=dict(size=18)), tickfont=dict(size=14), scaleanchor="x", scaleratio=1),
        legend=dict(font=dict(size=14)),
        template="plotly_white"
    )

    output_path = os.path.join(outdir, "impact_map.html")
    fig.write_html(output_path)
    print(f"Saved: {output_path}")


# ----------------------------------------------------------------------
# 4. FREQUENCY HISTOGRAMS FOR SCALAR VARIABLES
# ----------------------------------------------------------------------
EXCLUDED_KEYS = {
    "trajectory",
    "stability_vs_time",
    "x_impact",
    "y_impact",
    "impact_position",
    "index",
}

ACCELERATION_KEYWORDS = ("accel", "max_g", "acceleration")
ACCELERATION_THRESHOLD = 100.0


def get_scalar_variables(simulations):
    """Extracts scalar numerical variables, filtering out excessive acceleration values (>100)."""
    all_keys = set()
    for sim in simulations:
        all_keys.update(sim.keys())

    variables = {}
    for key in sorted(all_keys):
        if key in EXCLUDED_KEYS:
            continue
        values = []
        is_accel = any(kw in key.lower() for kw in ACCELERATION_KEYWORDS)
        
        for sim in simulations:
            v = sim.get(key)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if is_accel and v > ACCELERATION_THRESHOLD:
                    continue
                values.append(v)

        if len(values) > 0:
            variables[key] = np.array(values, dtype=float)
    return variables


def plot_histograms(simulations, outdir):
    variables = get_scalar_variables(simulations)

    hist_folder = os.path.join(outdir, "histograms")
    os.makedirs(hist_folder, exist_ok=True)

    for name, values in variables.items():
        mean_val = np.mean(values)
        std_val = np.std(values)

        fig = go.Figure()
        fig.add_trace(
            go.Histogram(
                x=values,
                marker_color="steelblue",
                opacity=0.75,
                name="Frequency"
            )
        )

        # Lines with larger text size for labels
        fig.add_vline(
            x=mean_val,
            line_width=2.5,
            line_color="crimson",
            annotation_text=f"Mean: {mean_val:.4g}",
            annotation_position="top left",
            annotation_font=dict(size=16, color="crimson")
        )
        fig.add_vline(
            x=mean_val + std_val,
            line_width=2,
            line_dash="dash",
            line_color="darkorange",
            annotation_text=f"+1σ: {(mean_val + std_val):.4g}",
            annotation_position="top right",
            annotation_font=dict(size=15, color="darkorange")
        )
        fig.add_vline(
            x=mean_val - std_val,
            line_width=2,
            line_dash="dash",
            line_color="darkorange",
            annotation_text=f"-1σ: {(mean_val - std_val):.4g}",
            annotation_position="top left",
            annotation_font=dict(size=15, color="darkorange")
        )

        fig.update_layout(
            title=dict(text=f"Distribution of {name} (N = {len(values)})", font=dict(size=22)),
            font=dict(size=16),
            xaxis=dict(title=dict(text=name, font=dict(size=18)), tickfont=dict(size=14)),
            yaxis=dict(title=dict(text="Simulation Count", font=dict(size=18)), tickfont=dict(size=14)),
            template="plotly_white",
            bargap=0.05
        )

        output_path = os.path.join(hist_folder, f"{name}.html")
        fig.write_html(output_path)

    print(f"Saved {len(variables)} interactive histograms in: {hist_folder}")

    summary_path = os.path.join(outdir, "statistical_summary.csv")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("variable,mean,std_dev,min,max\n")
        for name, values in variables.items():
            f.write(
                f"{name},{np.mean(values)},{np.std(values)},"
                f"{np.min(values)},{np.max(values)}\n"
            )
    print(f"Saved: {summary_path}")


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Monte Carlo Rocket Flight Simulation Analysis.")
    parser.add_argument("file", help="Path to the .txt file containing simulation JSON objects.")
    parser.add_argument("--outdir", default="analysis_results",
                        help="Output directory (default: analysis_results).")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    simulations = read_simulations(args.file)
    print(f"Successfully loaded {len(simulations)} simulations.")

    plot_3d_trajectories(simulations, args.outdir)
    plot_impact_map(simulations, args.outdir)
    plot_histograms(simulations, args.outdir)

    print("\nAnalysis completed! Output folder:", os.path.abspath(args.outdir))


if __name__ == "__main__":
    main()