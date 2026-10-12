# ROCKETPY SIMULATION - Fin cant angle error sweep (roll angular velocity)

import os
import numpy as np
import matplotlib.pyplot as plt
from rocketpy import Environment, SolidMotor, Rocket, Flight

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # RESOURCES paths work from any working directory

chamber_height = 0.923
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.943

enable_weather = False

# Cant angles to simulate: 0 to 5 degrees, 1 degree step
CANT_ANGLES = np.arange(0, 6, 1)

# ---------------------------------------------------------------- Environment
if enable_weather:
    env = Environment(date=(2026, 10, 17, 15))
    env.set_location(latitude=39.392377, longitude=-8.290826)
    env.set_elevation("Open-Elevation")
    env.set_atmospheric_model(type="forecast", file="GFS")
else:
    env = Environment()
    env.set_atmospheric_model(
        type="custom_atmosphere",
        wind_u=-8,  # East-West wind component (m/s)
        wind_v=0,  # North-South wind component (m/s)
    )


# ---------------------------------------------------------------------- Motor
def build_motor():
    return SolidMotor(
        thrust_source=os.path.join("RESOURCES", "ASPIDTHRUST.csv"),
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


# --------------------------------------------------------------------- Rocket
def build_rocket(cant_angle):
    rocket = Rocket(
        radius=RADIO_ASPID,
        mass=13,
        inertia=(6.175, 6.175, 0.05),
        power_off_drag=os.path.join("RESOURCES", "mach_cd_prot_cono_cola.csv"),
        power_on_drag=os.path.join("RESOURCES", "mach_cd_prot_cono_cola_power_on.csv"),
        center_of_mass_without_motor=1.4607,
        coordinate_system_orientation="nose_to_tail",
    )
    rocket.add_motor(build_motor(), position=LONGITUD_ASPID - chamber_height)
    rocket.add_nose(length=0.40, kind="ogive", position=0)
    rocket.add_trapezoidal_fins(
        n=4,
        root_chord=0.2,
        tip_chord=0.100,
        span=0.12,
        position=LONGITUD_ASPID - 0.2 - 0.03,
        cant_angle=float(cant_angle),
    )
    rocket.add_parachute(
        "drogue", cd_s=0.51586, trigger="apogee", radius=0.523, lag=1
    )
    rocket.add_parachute(
        "main", cd_s=6.126, trigger=450, radius=1.8027, lag=1
    )
    return rocket


# ----------------------------------------------------------------- Simulation
results = {}
for cant in CANT_ANGLES:
    print(f"Simulating cant angle = {cant:.0f} deg ...")
    flight = Flight(
        environment=env,
        rocket=build_rocket(cant),
        rail_length=12,
        inclination=84.0,
        terminate_on_apogee=True,
    )
    t = np.linspace(0, flight.t_final, 1000)
    w3 = np.array([flight.w3(ti) for ti in t])  # roll rate (rad/s)
    results[cant] = (t, w3)

# --------------------------------------------------------------------- Plot
fig, ax = plt.subplots(figsize=(10, 6))
colors = plt.cm.viridis(np.linspace(0, 0.9, len(CANT_ANGLES)))

for color, cant in zip(colors, CANT_ANGLES):
    t, w3 = results[cant]
    ax.plot(t, w3, color=color, linewidth=2, label=f"Cant angle = {cant:.0f}°")

ax.set_title("Roll Angular Velocity vs Time for Different Fin Cant Angles")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Roll angular velocity, ω₃ (rad/s)")
ax.grid(True, alpha=0.3)
ax.legend(title="Fin cant angle error")
fig.tight_layout()
fig.savefig("roll_rate_vs_cant_angle.png", dpi=200)
plt.show()