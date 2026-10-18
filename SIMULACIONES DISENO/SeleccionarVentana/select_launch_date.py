# ANÁLISIS DE VENTANAS DE LANZAMIENTO - ASPID (RocketPy)
#
# Para cada ventana:
#   - Perfil de viento (magnitud y dirección) de 0 a 4000 m AGL
#   - Simulación CON y SIN aerofrenos
#   - Apogeo, ángulo de ataque, downrange (apogeo y aterrizaje)
# Resultados: tabla (CSV) + figuras PNG en la carpeta RESULTADOS/

import os
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # no abre ventanas, solo guarda las imágenes
import matplotlib.pyplot as plt
from rocketpy import Environment, SolidMotor, Rocket, Flight
import sys

# Busca hacia arriba la carpeta raíz del proyecto (la que contiene LANZAMIENTO y RESOURCES),
# la añade al path de Python y trabaja desde ella. Funciona estés donde estés en el árbol.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def find_project_root(start):
    d = start
    while True:
        if os.path.isdir(os.path.join(d, "LANZAMIENTO")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            raise FileNotFoundError(
                "No se encontró la carpeta LANZAMIENTO en ningún directorio superior a " + start)
        d = parent


PROJECT_ROOT = find_project_root(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)  # así las rutas RESOURCES/... funcionan

from LANZAMIENTO.airbrakes_control import AirbrakesController

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

# Ventanas de lanzamiento: (año, mes, día, hora UTC). Edita / añade / quita las que quieras.
LAUNCH_WINDOWS = [
    (2026, 10, 19, 9),
    (2026, 10, 19, 12),
    (2026, 10, 19, 15),
    (2026, 10, 20, 9),
    (2026, 10, 20, 12),
    (2026, 10, 20, 15)
]


# Heading de la rampa: azimut desde el Norte, sentido horario (90 = Este, 145 = Sudeste).
# Cámbialo según la plataforma de lanzamiento; se usa en la simulación y en la línea de los mapas.
HEADING = 145.0
SHOW_HEADING_LINE = True     # dibuja en los mapas la línea del heading desde la rampa

# Mapa de fondo bajo las trayectorias (requiere internet y: pip install contextily)
USE_BASEMAP = True
MAP_STYLE = "satellite"      # "satellite" (Esri) o "osm" (OpenStreetMap)

FULL_FLIGHT = True           # True: simula hasta el aterrizaje (downrange de recuperación). False: termina en apogeo
WIND_MAX_ALTITUDE_AGL = 4000  # m, límite del perfil de viento
AOA_MIN_AIRSPEED = 20         # m/s, el AoA solo se evalúa si la velocidad respecto al aire supera esto

# Lanzamiento
RAIL_LENGTH = 12
INCLINATION = 84.0

# Cohete
chamber_height = 0.923
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.95

# Controlador de aerofrenos
ACTIVATION_ALTITUDE = 1500   # m AGL
SAMPLING_RATE = 20           # Hz
KP = 0.005
KI = 0.1
TARGET_APOGEE_AGL = 3000     # m sobre el suelo

OUTPUT_DIR = os.path.join(SCRIPT_DIR, "RESULTADOS")  # junto a select_launch_date.py
os.makedirs(OUTPUT_DIR, exist_ok=True)


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def window_label(w):
    y, m, d, h = w
    return f"{d:02d}/{m:02d}/{y} {h:02d}:00 UTC"


def build_environment(window):
    """
    Crea el entorno para una ventana.
    OJO: el forecast GFS sobrescribe env.elevation con la altura de su propia rejilla,
    así que la elevación real de la rampa se fija DESPUÉS del modelo atmosférico.
    """
    env = Environment(
        date=window,
        latitude=39.392547, 
        longitude=-8.289517,
    )
    env.set_atmospheric_model(type="forecast", file="GFS")
    env.set_elevation(160)
    return env


def build_rocket(env, with_airbrakes):
    """
    Construye motor + cohete desde cero (cada simulación necesita su propio objeto
    Rocket para no acumular aerofrenos ni estado del controlador).
    """
    motor = SolidMotor(
        thrust_source=os.path.join("RESOURCES", "ASPIDTHRUST.csv"),
        dry_mass=6.342,
        dry_inertia=(5.168, 5.168, 0.017),
        nozzle_radius=60 / 2000,
        grain_number=4,
        grain_density=1842,
        grain_outer_radius=45.5 / 1000,
        grain_initial_inner_radius=18 / 1000,
        grain_initial_height=200 / 1000,
        grain_separation=7 / 1000,
        grains_center_of_mass_position=0.433,
        center_of_dry_mass_position=0.481,
        nozzle_position=chamber_height,
        throat_radius=28.546 / 2000,
        coordinate_system_orientation="combustion_chamber_to_nozzle",
    )

    rocket = Rocket(
    radius=RADIO_ASPID,
    mass=14.6,     
    inertia=(6.175, 6.175, 0.05),
    power_off_drag=r"RESOURCES\mach_cd_sin_chaflan_preciso.csv",
    power_on_drag=r"RESOURCES\mach_cd_sin_chaflan_preciso_power_on.csv",
    center_of_mass_without_motor=1.438,
    coordinate_system_orientation="nose_to_tail"
    )

    rocket.add_motor(motor, position=LONGITUD_ASPID - chamber_height)
    rocket.add_nose(length=0.40, kind="ogive", position=0)
    rocket.add_trapezoidal_fins(
        n=4,
        root_chord=0.2,
        tip_chord=0.100,
        span=0.12,
        position=LONGITUD_ASPID - 0.2 - 0.03,
    )

    rocket.add_parachute("drogue", cd_s=0.51586, trigger="apogee", radius=0.523, lag=1)
    rocket.add_parachute("main", cd_s=6.126, trigger=450, radius=1.8027, lag=1)

    if with_airbrakes:
        target_apogee = TARGET_APOGEE_AGL + env.elevation  # ASL
        controller = AirbrakesController(rocket, env, target_apogee, KP, KI, SAMPLING_RATE)

        def controller_function(time, sampling_rate, state, state_history,
                                observed_variables, air_brakes):
            active = (state[2] - env.elevation > ACTIVATION_ALTITUDE) and (state[5] > 0)
            air_brakes.deployment_level, log = controller.update(time, state, air_brakes, active)
            return log

        rocket.add_air_brakes(
            drag_coefficient_curve=os.path.join("RESOURCES", "airbrakes.csv"),
            override_rocket_drag=False,
            controller_function=controller_function,
            sampling_rate=SAMPLING_RATE,
        )
    # Sin aerofrenos: el cohete no lleva el objeto air_brakes (sin ninguna influencia en el drag)
    return rocket


def run_flight(env, with_airbrakes):
    rocket = build_rocket(env, with_airbrakes)
    return Flight(
        environment=env,
        rocket=rocket,
        rail_length=RAIL_LENGTH,
        inclination=INCLINATION,
        heading=HEADING,
        terminate_on_apogee=not FULL_FLIGHT,
    )


def wind_profile(env, n=101):
    """Devuelve (altitud AGL, magnitud viento, dirección de procedencia) de 0 a WIND_MAX_ALTITUDE_AGL."""
    z_agl = np.linspace(0, WIND_MAX_ALTITUDE_AGL, n)
    speed = np.array([env.wind_speed(z + env.elevation) for z in z_agl])
    direction = np.array([env.wind_direction(z + env.elevation) for z in z_agl])
    return z_agl, speed, direction


def flight_series(flight, env):
    """Extrae las series necesarias de un vuelo."""
    t_x, x = flight.x.source[:, 0], flight.x.source[:, 1]
    y = np.interp(t_x, flight.y.source[:, 0], flight.y.source[:, 1])
    z_agl = np.interp(t_x, flight.z.source[:, 0], flight.z.source[:, 1]) - env.elevation
    downrange = np.hypot(x, y)

    aoa_t = flight.angle_of_attack.source[:, 0]
    aoa = flight.angle_of_attack.source[:, 1]
    # Cerca del apogeo la velocidad respecto al aire tiende a 0 y el AoA deja de tener sentido
    # (puede dar decenas de grados sin que haya ningún problema), así que se descarta ese tramo.
    fs = flight.free_stream_speed.source
    v_air = np.interp(aoa_t, fs[:, 0], fs[:, 1])
    mask = ((aoa_t >= flight.out_of_rail_time) & (aoa_t <= flight.apogee_time)
            & (v_air >= AOA_MIN_AIRSPEED))

    return {
        "t": t_x, "x": x, "y": y, "z_agl": z_agl, "downrange": downrange,
        "aoa_t": aoa_t[mask], "aoa": aoa[mask],
        "apogee_xy": (flight.apogee_x, flight.apogee_y),
    }


# =============================================================================
# SIMULACIONES
# =============================================================================

results = []   # filas de la tabla
data = {}      # datos para las gráficas

for w in LAUNCH_WINDOWS:
    label = window_label(w)
    print(f"\n=== Ventana {label} ===")
    try:
        env = build_environment(w)
        LAUNCH_LAT, LAUNCH_LON = env.latitude, env.longitude  # para el mapa de fondo
        z_w, v_w, d_w = wind_profile(env)
        data[label] = {"wind": (z_w, v_w, d_w), "con": None, "sin": None}

        for tag, brakes in (("sin", False), ("con", True)):
            print(f"  Simulando {'CON' if brakes else 'SIN'} aerofrenos...")
            flight = run_flight(env, brakes)
            s = flight_series(flight, env)
            data[label][tag] = s

            apogee_agl = flight.apogee - env.elevation
            results.append({
                "Ventana": label,
                "Aerofrenos": "CON" if brakes else "SIN",
                "Apogeo AGL [m]": apogee_agl,
                "Error vs objetivo [m]": apogee_agl - TARGET_APOGEE_AGL,
                "t apogeo [s]": flight.apogee_time,
                "Vel. salida rampa [m/s]": flight.out_of_rail_velocity,
                "Vel. máx [m/s]": flight.max_speed,
                "AoA máx [°]": float(np.max(s["aoa"])) if len(s["aoa"]) else np.nan,
                "AoA medio [°]": float(np.mean(s["aoa"])) if len(s["aoa"]) else np.nan,
                "Downrange apogeo [m]": math.hypot(flight.apogee_x, flight.apogee_y),
                "Downrange final [m]": float(s["downrange"][-1]),
                "Viento medio 0-4km [m/s]": float(np.mean(v_w)),
                "Viento máx 0-4km [m/s]": float(np.max(v_w)),
            })
    except Exception as e:
        print(f"  [ERROR] Ventana {label}: {e}")
        data.pop(label, None)

if not results:
    raise SystemExit("No se completó ninguna simulación.")

df = pd.DataFrame(results)
print("\n" + "=" * 100)
print(df.round(1).to_string(index=False))
df.to_csv(os.path.join(OUTPUT_DIR, "resultados_ventanas.csv"), index=False)

# Resumen CON vs SIN
pivot = df.pivot(index="Ventana", columns="Aerofrenos", values="Apogeo AGL [m]")
pivot = pivot.reindex([window_label(w) for w in LAUNCH_WINDOWS if window_label(w) in pivot.index])
pivot["Reducción [m]"] = pivot["SIN"] - pivot["CON"]
print("\nResumen de apogeo (AGL):")
print(pivot.round(1).to_string())

labels = list(pivot.index)
n = len(labels)
if n <= 20:
    colors = [plt.cm.tab20(i) for i in range(n)]
else:
    colors = list(plt.cm.turbo(np.linspace(0.05, 0.95, n)))
ncols = 3
nrows = math.ceil(n / ncols)
c_con, c_sin = "tab:red", "tab:blue"


def save(fig, name):
    fig.savefig(os.path.join(OUTPUT_DIR, name), dpi=150, bbox_inches="tight")
    plt.close(fig)


# --- Mapa de fondo -----------------------------------------------------------
R_EARTH = 6378137.0
COS_LAT = math.cos(math.radians(LAUNCH_LAT))
MERC_X0 = R_EARTH * math.radians(LAUNCH_LON)
MERC_Y0 = R_EARTH * math.log(math.tan(math.pi / 4 + math.radians(LAUNCH_LAT) / 2))

# Límites comunes (metros locales, origen en la rampa) para todos los mapas
_all_x = np.concatenate([data[l][t]["x"] for l in labels for t in ("con", "sin")] + [np.array([0.0])])
_all_y = np.concatenate([data[l][t]["y"] for l in labels for t in ("con", "sin")] + [np.array([0.0])])
_cx, _cy = (_all_x.max() + _all_x.min()) / 2, (_all_y.max() + _all_y.min()) / 2
_half = max(_all_x.max() - _all_x.min(), _all_y.max() - _all_y.min()) / 2 * 1.25 + 300
MAP_XLIM = (_cx - _half, _cx + _half)
MAP_YLIM = (_cy - _half, _cy + _half)

_basemap_warned = False


def draw_heading(ax):
    """Línea desde la rampa en la dirección del heading de lanzamiento (azimut desde el Norte)."""
    if not SHOW_HEADING_LINE:
        return
    h = math.radians(HEADING)
    length = (MAP_XLIM[1] - MAP_XLIM[0]) * 1.5  # más larga que el mapa; los límites de ejes la recortan
    ax.plot([0, length * math.sin(h)], [0, length * math.cos(h)],
            color="magenta", ls="-.", lw=2.2, zorder=4, label=f"Heading rampa ({HEADING:.0f}°)")


def add_basemap(ax):
    """Dibuja un mapa 2D (satélite u OSM) bajo la trayectoria. Ejes en metros locales (Este/Norte)."""
    global _basemap_warned
    if not USE_BASEMAP:
        return False
    try:
        import contextily as ctx
        source = (ctx.providers.Esri.WorldImagery if MAP_STYLE == "satellite"
                  else ctx.providers.OpenStreetMap.Mapnik)
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        w, e = MERC_X0 + xmin / COS_LAT, MERC_X0 + xmax / COS_LAT
        s, n_ = MERC_Y0 + ymin / COS_LAT, MERC_Y0 + ymax / COS_LAT
        img, ext = ctx.bounds2img(w, s, e, n_, ll=False, source=source)
        extent_local = ((ext[0] - MERC_X0) * COS_LAT, (ext[1] - MERC_X0) * COS_LAT,
                        (ext[2] - MERC_Y0) * COS_LAT, (ext[3] - MERC_Y0) * COS_LAT)
        ax.imshow(img, extent=extent_local, zorder=0, interpolation="bilinear")
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        return True
    except Exception as err:
        if not _basemap_warned:
            print(f"[AVISO] No se pudo cargar el mapa de fondo ({err}). "
                  f"Instala contextily (pip install contextily) y comprueba la conexión.")
            _basemap_warned = True
        return False


# =============================================================================
# FIGURA 1: Viento (magnitud) 0-4000 m, todas las ventanas superpuestas
# =============================================================================
fig1, ax = plt.subplots(figsize=(7, 8))
for lab, c in zip(labels, colors):
    z, v, _ = data[lab]["wind"]
    ax.plot(v, z, color=c, lw=2, label=lab)
ax.axhline(ACTIVATION_ALTITUDE, color="gray", ls="--", lw=1)
ax.text(ax.get_xlim()[1] * 0.98, ACTIVATION_ALTITUDE + 40, "Activación aerofrenos",
        ha="right", fontsize=8, color="gray")
ax.set_xlabel("Velocidad del viento [m/s]")
ax.set_ylabel("Altitud AGL [m]")
ax.set_ylim(0, WIND_MAX_ALTITUDE_AGL)
ax.set_title("Perfil de viento por ventana de lanzamiento")
ax.grid(alpha=0.3)
ax.legend(fontsize=8)
fig1.tight_layout()
save(fig1, "1_viento_superpuesto.png")

#    =============================================================================
# FIGURA 2: Viento por ventana (magnitud + dirección)
# =============================================================================
fig2, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4.5 * nrows), squeeze=False, sharey=True)
for i, lab in enumerate(labels):
    a = axes[i // ncols][i % ncols]
    z, v, d = data[lab]["wind"]
    a.plot(v, z, color="tab:blue", lw=2)
    a.set_xlabel("Viento [m/s]", color="tab:blue")
    a.set_title(lab, fontsize=10)
    a.grid(alpha=0.3)
    a.set_ylim(0, WIND_MAX_ALTITUDE_AGL)
    a2 = a.twiny()
    a2.plot(d, z, color="tab:orange", lw=1.2, ls="--")
    a2.set_xlim(0, 360)
    a2.set_xticks([0, 90, 180, 270, 360])
    a2.set_xlabel("Procedencia [°]", color="tab:orange", fontsize=8)
    if i % ncols == 0:
        a.set_ylabel("Altitud AGL [m]")
for j in range(n, nrows * ncols):
    axes[j // ncols][j % ncols].axis("off")
fig2.suptitle("Magnitud (azul) y dirección de procedencia (naranja) del viento", y=1.00)
fig2.tight_layout()
save(fig2, "2_viento_por_ventana.png")

# =============================================================================
# FIGURA 3: Apogeo CON vs SIN aerofrenos
# =============================================================================
fig3, (a1, a2) = plt.subplots(2, 1, figsize=(max(8, 1.3 * n), 9), sharex=True)
xpos = np.arange(n)
w_bar = 0.38
b1 = a1.bar(xpos - w_bar / 2, pivot["SIN"], w_bar, label="SIN aerofrenos", color=c_sin)
b2 = a1.bar(xpos + w_bar / 2, pivot["CON"], w_bar, label="CON aerofrenos", color=c_con)
a1.axhline(TARGET_APOGEE_AGL, color="k", ls="--", lw=1.5, label=f"Objetivo ({TARGET_APOGEE_AGL} m)")
a1.bar_label(b1, fmt="%.0f", fontsize=8, padding=2)
a1.bar_label(b2, fmt="%.0f", fontsize=8, padding=2)
lo = min(pivot["SIN"].min(), pivot["CON"].min(), TARGET_APOGEE_AGL)
hi = max(pivot["SIN"].max(), pivot["CON"].max(), TARGET_APOGEE_AGL)
a1.set_ylim(lo - 0.15 * (hi - lo) - 50, hi + 0.12 * (hi - lo) + 50)
a1.set_ylabel("Apogeo AGL [m]")
a1.set_title("Apogeo por ventana")
a1.legend()
a1.grid(axis="y", alpha=0.3)

err_sin = pivot["SIN"] - TARGET_APOGEE_AGL
err_con = pivot["CON"] - TARGET_APOGEE_AGL
a2.bar(xpos - w_bar / 2, err_sin, w_bar, color=c_sin, label="SIN")
a2.bar(xpos + w_bar / 2, err_con, w_bar, color=c_con, label="CON")
a2.axhline(0, color="k", lw=1)
a2.set_ylabel("Error respecto al objetivo [m]")
a2.set_title("Error de apogeo (positivo = por encima del objetivo)")
a2.set_xticks(xpos)
a2.set_xticklabels([l.replace(" ", "\n") for l in labels], fontsize=8)
a2.legend()
a2.grid(axis="y", alpha=0.3)
fig3.tight_layout()
save(fig3, "3_apogeo_con_sin.png")

# =============================================================================
# FIGURA 4: Ángulo de ataque vs tiempo (ascenso)
# =============================================================================
fig4, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 3.8 * nrows), squeeze=False, sharey=True)
for i, lab in enumerate(labels):
    a = axes[i // ncols][i % ncols]
    for tag, c, name in (("sin", c_sin, "SIN"), ("con", c_con, "CON")):
        s = data[lab][tag]
        a.plot(s["aoa_t"], s["aoa"], color=c, lw=1.5, label=name)
    a.set_title(lab, fontsize=10)
    a.grid(alpha=0.3)
    if i // ncols == nrows - 1:
        a.set_xlabel("Tiempo [s]")
    if i % ncols == 0:
        a.set_ylabel("Ángulo de ataque [°]")
    if i == 0:
        a.legend()
for j in range(n, nrows * ncols):
    axes[j // ncols][j % ncols].axis("off")
fig4.suptitle(f"Ángulo de ataque desde salida de rampa hasta apogeo (solo con velocidad aerodinámica > {AOA_MIN_AIRSPEED} m/s)", y=1.00)
fig4.tight_layout()
save(fig4, "4_angulo_ataque.png")

# =============================================================================
# FIGURA 5: Downrange (trayectoria en planta + altitud vs downrange)
# =============================================================================
fig5, (p1, p2) = plt.subplots(1, 2, figsize=(17, 8))
p1.set_xlim(MAP_XLIM)
p1.set_ylim(MAP_YLIM)
p1.set_aspect("equal", adjustable="box")
add_basemap(p1)
for lab, c in zip(labels, colors):
    for tag, ls in (("sin", "--"), ("con", "-")):
        s = data[lab][tag]
        p1.plot(s["x"], s["y"], color=c, ls=ls, lw=1.8, zorder=3,
                label=lab if tag == "con" else None)
        p1.plot(s["x"][-1], s["y"][-1], "x", color=c, ms=8, mew=2, zorder=4)  # final / aterrizaje
        p2.plot(s["downrange"], s["z_agl"], color=c, ls=ls, lw=1.6)
p1.plot(0, 0, "^", color="white", mec="k", ms=13, zorder=5, label="Despegue")
draw_heading(p1)
p1.set_xlabel("Este [m]")
p1.set_ylabel("Norte [m]")
p1.set_title("Trayectoria en planta (continuo: CON, discontinuo: SIN, x: final)")
p1.grid(alpha=0.3, color="white")
p1.legend(fontsize=7, loc="upper left", framealpha=0.85)
p2.set_xlabel("Downrange [m]")
p2.set_ylabel("Altitud AGL [m]")
p2.set_title("Altitud vs downrange (continuo: CON, discontinuo: SIN)")
p2.grid(alpha=0.3)
fig5.tight_layout()
save(fig5, "5_downrange_trayectorias.png")

# =============================================================================
# FIGURA 6: Downrange en apogeo y en aterrizaje
# =============================================================================
fig6, (d1, d2) = plt.subplots(1, 2, figsize=(max(12, 2.2 * n), 5.5))
for ax_, col, title in ((d1, "Downrange apogeo [m]", "Downrange en apogeo"),
                        (d2, "Downrange final [m]",
                         "Downrange final (aterrizaje)" if FULL_FLIGHT else "Downrange final (apogeo)")):
    p = df.pivot(index="Ventana", columns="Aerofrenos", values=col).reindex(labels)
    ax_.bar(xpos - w_bar / 2, p["SIN"], w_bar, color=c_sin, label="SIN")
    ax_.bar(xpos + w_bar / 2, p["CON"], w_bar, color=c_con, label="CON")
    ax_.set_xticks(xpos)
    ax_.set_xticklabels([l.replace(" ", "\n") for l in labels], fontsize=8)
    ax_.set_ylabel("Distancia [m]")
    ax_.set_title(title)
    ax_.grid(axis="y", alpha=0.3)
    ax_.legend()
fig6.tight_layout()
save(fig6, "6_downrange_barras.png")

# =============================================================================
# FIGURA 7: Relación viento vs apogeo / AoA / downrange (ayuda a elegir ventana)
# =============================================================================
fig7, axs = plt.subplots(1, 3, figsize=(16, 4.8))
dfw = df.copy()
for tag, c in (("SIN", c_sin), ("CON", c_con)):
    sub = dfw[dfw["Aerofrenos"] == tag]
    axs[0].scatter(sub["Viento medio 0-4km [m/s]"], sub["Apogeo AGL [m]"], color=c, label=tag, s=50)
    axs[1].scatter(sub["Viento medio 0-4km [m/s]"], sub["AoA máx [°]"], color=c, label=tag, s=50)
    axs[2].scatter(sub["Viento medio 0-4km [m/s]"], sub["Downrange final [m]"], color=c, label=tag, s=50)
axs[0].axhline(TARGET_APOGEE_AGL, color="k", ls="--", lw=1)
for a, yl in zip(axs, ("Apogeo AGL [m]", "AoA máximo [°]", "Downrange final [m]")):
    a.set_xlabel("Viento medio 0-4 km [m/s]")
    a.set_ylabel(yl)
    a.grid(alpha=0.3)
    a.legend()
fig7.suptitle("Sensibilidad al viento", y=1.02)
fig7.tight_layout()
save(fig7, "7_sensibilidad_viento.png")

# =============================================================================
# FIGURA 8: Mapa 2D por ventana (despegue, apogeo y aterrizaje sobre el mapa)
# =============================================================================
fig8, axes = plt.subplots(nrows, ncols, figsize=(6.5 * ncols, 6.5 * nrows), squeeze=False)
for i, lab in enumerate(labels):
    a = axes[i // ncols][i % ncols]
    a.set_xlim(MAP_XLIM)
    a.set_ylim(MAP_YLIM)
    a.set_aspect("equal", adjustable="box")
    add_basemap(a)
    land_txt = []
    for tag, c, name in (("sin", "cyan", "SIN"), ("con", "yellow", "CON")):
        s = data[lab][tag]
        a.plot(s["x"], s["y"], color=c, lw=2, zorder=3, label=name)
        a.plot(*s["apogee_xy"], "*", color=c, mec="k", ms=14, zorder=4)
        a.plot(s["x"][-1], s["y"][-1], "X", color=c, mec="k", ms=11, zorder=4)
        land_txt.append(f"{name}: {s['downrange'][-1]:.0f} m")
    a.plot(0, 0, "^", color="white", mec="k", ms=13, zorder=5, label="Despegue")
    draw_heading(a)
    a.set_title(f"{lab}\nDownrange final  " + " | ".join(land_txt), fontsize=9)
    a.grid(alpha=0.3, color="white")
    if i // ncols == nrows - 1:
        a.set_xlabel("Este [m]")
    if i % ncols == 0:
        a.set_ylabel("Norte [m]")
    if i == 0:
        a.legend(fontsize=8, loc="upper left", framealpha=0.85)
for j in range(n, nrows * ncols):
    axes[j // ncols][j % ncols].axis("off")
fig8.suptitle("Despegue (▲), apogeo (★), final de vuelo (X) y heading de rampa (línea magenta)", y=1.00)
fig8.tight_layout()
save(fig8, "8_mapa_por_ventana.png")

print(f"\nResultados y figuras guardados en: {os.path.abspath(OUTPUT_DIR)}")