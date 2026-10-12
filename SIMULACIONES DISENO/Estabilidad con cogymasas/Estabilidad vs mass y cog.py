# ROCKETPY SIMULATION - BARRIDO PARAMÉTRICO (masa y CG del cuerpo)

import os
import numpy as np
import matplotlib.pyplot as plt
from rocketpy import Environment, SolidMotor, Rocket, Flight

# ------------------------------------------------------------------
# DATOS BASE
# ------------------------------------------------------------------
chamber_height = 0.923
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.943

enable_airbrakes = False
enable_weather = False

if enable_weather:
    env = Environment(date=(2026, 10, 17, 15))
    env.set_location(latitude=39.392377, longitude=-8.290826)
    env.set_elevation("Open-Elevation")
    env.set_atmospheric_model(type="forecast", file="GFS")
else:
    env = Environment()
    env.set_atmospheric_model(
    type="custom_atmosphere",
    wind_u=-8,   # componente del viento en el eje Este-Oeste (m/s)
    wind_v=0,   # componente del viento en el eje Norte-Sur (m/s)
)

TARGET_APOGEE = 3000 + env.elevation  # m sobre el nivel del mar

# ------------------------------------------------------------------
# PARÁMETROS DEL BARRIDO (ajusta rangos y resolución)
# ------------------------------------------------------------------
MASA_NOMINAL = 14.0
CG_NOMINAL = 1.4607

N_MASA = 8
N_CG = 12
masas = np.linspace(12, 15, N_MASA)       # kg (cuerpo, sin motor)
cgs = np.linspace(1.10, 1.80, N_CG)           # m desde la punta (nose_to_tail)

T_AOA = 15.0  # s, instante donde se mide el ángulo de ataque

# ------------------------------------------------------------------
# MOTOR (no cambia entre simulaciones)
# ------------------------------------------------------------------
TIMANFAYA = SolidMotor(
    thrust_source=r"RESOURCES\ASPIDTHRUST.csv",
    dry_mass=6.98,
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


# ------------------------------------------------------------------
# FUNCIONES
# ------------------------------------------------------------------
def build_rocket(mass, cg):
    """Construye el cohete con la masa y el CG (sin motor) indicados."""
    rocket = Rocket(
        radius=RADIO_ASPID,
        mass=mass,
        inertia=(6.175, 6.175, 0.05),
        power_off_drag=r"RESOURCES\mach_cd_prot_cono_cola.csv",
        power_on_drag=r"RESOURCES\mach_cd_prot_cono_cola_power_on.csv",
        center_of_mass_without_motor=cg,
        coordinate_system_orientation="nose_to_tail",
    )
    rocket.add_motor(TIMANFAYA, position=LONGITUD_ASPID - chamber_height)
    rocket.add_nose(length=0.40, kind="ogive", position=0)
    rocket.add_trapezoidal_fins(
        n=4,
        root_chord=0.2,
        tip_chord=0.100,
        span=0.12,
        position=LONGITUD_ASPID - 0.2 - 0.03,
    )
    rocket.add_parachute("drogue", cd_s=0.51586, trigger="apogee",
                         radius=0.523, lag=1)
    rocket.add_parachute("main", cd_s=6.126, trigger=450,
                         radius=1.8027, lag=1)
    return rocket


def run_case(mass, cg):
    """Simula un caso y devuelve las 4 métricas."""
    rocket = build_rocket(mass, cg)
    flight = Flight(
        environment=env,
        rocket=rocket,
        rail_length=12,
        inclination=84.0,
        terminate_on_apogee=True,
        verbose=False,
    )

    stab_rail = flight.out_of_rail_stability_margin
    stab_max = flight.max_stability_margin
    v_rail = flight.out_of_rail_velocity

    # Ángulo de ataque a los 15 s (NaN si el vuelo termina antes)
    if flight.t_final >= T_AOA:
        aoa = float(flight.angle_of_attack(T_AOA))
    else:
        aoa = np.nan

    return stab_rail, stab_max, v_rail, aoa


# ------------------------------------------------------------------
# BARRIDO
# ------------------------------------------------------------------
shape = (N_MASA, N_CG)
STAB_RAIL = np.full(shape, np.nan)
STAB_MAX = np.full(shape, np.nan)
V_RAIL = np.full(shape, np.nan)
AOA = np.full(shape, np.nan)

total = N_MASA * N_CG
count = 0
for i, m in enumerate(masas):
    for j, cg in enumerate(cgs):
        count += 1
        print(f"[{count}/{total}] masa = {m:.2f} kg | CG = {cg:.3f} m")
        try:
            (STAB_RAIL[i, j], STAB_MAX[i, j],
             V_RAIL[i, j], AOA[i, j]) = run_case(m, cg)
        except Exception as e:
            print(f"   -> fallo en la simulación: {e}")
# ------------------------------------------------------------------
# PLOTS
# ------------------------------------------------------------------
plots = [
    (STAB_RAIL, "Stability margin at rail exit", "Stability margin [cal]", "viridis"),
    (STAB_MAX, "Maximum stability margin", "Stability margin [cal]", "viridis"),
    (V_RAIL, "Rail exit velocity", "Velocity [m/s]", "plasma"),
    (AOA, f"Angle of attack at t = {T_AOA:.0f} s", "Angle of attack [°]", "magma"),
]

fig, axs = plt.subplots(2, 2, figsize=(13, 10))
CG_GRID, M_GRID = np.meshgrid(cgs, masas)

for ax, (Z, title, cbar_label, cmap) in zip(axs.ravel(), plots):
    if np.all(np.isnan(Z)):
        ax.set_title(title + " (no data)")
        continue
    cf = ax.contourf(CG_GRID, M_GRID, Z, levels=20, cmap=cmap)
    cs = ax.contour(CG_GRID, M_GRID, Z, levels=8, colors="k",
                    linewidths=0.5, alpha=0.6)
    ax.clabel(cs, inline=True, fontsize=7, fmt="%.2f")
    ax.plot(CG_NOMINAL, MASA_NOMINAL, "r*", markersize=14,
            label="Nominal design")
    fig.colorbar(cf, ax=ax, label=cbar_label)
    ax.set_title(title)
    ax.set_xlabel("Body CG position from nose tip [m]")
    ax.set_ylabel("Body mass (without motor) [kg]")
    ax.legend(loc="upper right")

# Reference line for minimum recommended stability (1.5 cal) on the first plot
try:
    axs[0, 0].contour(CG_GRID, M_GRID, STAB_RAIL, levels=[1.5],
                      colors="white", linewidths=2, linestyles="--")
except Exception:
    pass

fig.suptitle("Parametric sweep: body mass vs. body CG position with 8m/s wind (West->East) ", fontsize=14)
plt.tight_layout()
plt.savefig("mass_cg_sweep.png", dpi=200)
plt.show()

# ------------------------------------------------------------------
# Simulación nominal (como en tu script original)
# ------------------------------------------------------------------
ASPID = build_rocket(MASA_NOMINAL, CG_NOMINAL)
test_flight = Flight(
    environment=env,
    rocket=ASPID,
    rail_length=12,
    inclination=84.0,
    terminate_on_apogee=True,
)