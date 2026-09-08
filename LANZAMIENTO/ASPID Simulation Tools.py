# Código para sacar la fuerza de los aerofrenos. 

import matplotlib.pyplot as plt
import numpy as np
from rocketpy import AirBrakes, Environment, Flight, Rocket, SolidMotor
from rocketpy.utilities import fin_flutter_analysis

chamber_height = 0.923
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.896

enable_airbrakes = True
enable_weather = True

if enable_weather:
  env = Environment(date=(2026, 10, 17, 15))  # Date:(2026,10,17,16)
  env.set_location(latitude=39.44580338814086, longitude=-8.29626628763608)
  env.set_elevation("Open-Elevation")
  env.set_atmospheric_model(type="Windy", file="GFS")
elif not enable_weather:
  env = Environment()

TARGET_APOGEE = 3000 + env.elevation  # Target apogee in meters above sea level


airbrakes_deployment_history = []
apogee_prediction_history = []
# --- NUEVA LISTA PARA GUARDAR LA FUERZA DE LOS AEROFRENOS ---
airbrakes_force_history = []
cd_monitor_diagnostics = {}

TIMANFAYA = SolidMotor(
    thrust_source=r"RESOURCES\ASPIDTHRUST.csv",
    dry_mass=7.1,
    dry_inertia=(5.168, 5.168, 0.017),
    nozzle_radius=60 / 2000,
    grain_number=4,
    grain_density=1793,
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


ASPID = Rocket(
    radius=RADIO_ASPID,
    mass=14.2,
    inertia=(6.175, 6.175, 0.05),
    power_off_drag=r"RESOURCES\CD_OFF_ASPID.csv",
    power_on_drag=r"RESOURCES\CD_ON_ASPID.csv",
    center_of_mass_without_motor=1.4607,
    coordinate_system_orientation="nose_to_tail",
)

ASPID.add_motor(TIMANFAYA, position=LONGITUD_ASPID - chamber_height)
ASPID.add_nose(length=0.40, kind="ogive", position=0)
ASPID.add_trapezoidal_fins(
    n=4,
    root_chord=0.2,
    tip_chord=0.100,
    span=0.12,
    position=LONGITUD_ASPID - 0.2 - 0.03,
)


ASPID.add_parachute(
    "drogue",
    cd_s=0.51586,
    trigger="apogee",
    radius=0.523,
    lag=1,
)

ASPID.add_parachute(
    "main",
    cd_s=6.126,
    trigger=300,
    radius=1.8027,
    lag=1,
)


# Apogee predictor values.
DT_PREDICT = 0.05
N_MAX = 20000
TGO_DIVISOR = 2.0


def _apogee_simple_vertical(
    altitude, vz, *, mass, cd, ref_area, g, env, dt=DT_PREDICT, n_max=N_MAX
):
  k_drag = 0.5 * ref_area * cd / mass
  h = altitude
  w = vz
  t = 0.0

  if w <= 0.0:
    return altitude, 0.0

  for _ in range(int(n_max)):
    rho = env.density(h)
    sp = abs(w)

    a_up = -g - (k_drag * rho * sp) * w
    w_next = w + a_up * dt
    h_next = h + w * dt

    if w_next <= 0.0:
      frac = w / (w - w_next)
      apogee = h + w * dt * frac
      return apogee, t + frac * dt

    w, h, t = w_next, h_next, t + dt

  return h, t


def _invert_cd_to_deployment(air_brakes, cd_total, mach, n_grid=21):
  d_grid = np.linspace(0.0, 1.0, n_grid)
  cd_grid = np.array([air_brakes.drag_coefficient(d, mach) for d in d_grid])
  return float(np.interp(cd_total, cd_grid, d_grid))


def cd_monitor_strategy(altitude, vz, mach_number, env, rocket, target_apogee):
  air_brakes = rocket.air_brakes[0]

  mass = rocket.dry_mass
  ref_area = np.pi * rocket.radius**2
  cd_closed = air_brakes.drag_coefficient(0.0, mach_number)
  g = env.gravity(altitude)
  rho = env.density(altitude)

  apogee_est, t_go = _apogee_simple_vertical(
      altitude,
      vz,
      mass=mass,
      cd=cd_closed,
      ref_area=ref_area,
      g=g,
      env=env,
      dt=DT_PREDICT,
      n_max=N_MAX,
  )

  if t_go > 1e-4:
    error = apogee_est - target_apogee
    f_cmd = error * 2.0 * mass / (t_go / TGO_DIVISOR) ** 2
  else:
    f_cmd = 0.0

  speed_sq = vz * vz
  cd_cmd = (
      2.0 * f_cmd / (rho * speed_sq * ref_area) if speed_sq > 1e-6 else 0.0
  )

  cd_monitor_diagnostics["last_apogee_est"] = apogee_est
  cd_monitor_diagnostics["last_t_go"] = t_go
  cd_monitor_diagnostics["last_cd_cmd"] = cd_cmd

  if cd_cmd <= 0.0:
    return 0.0

  return _invert_cd_to_deployment(air_brakes, cd_closed + cd_cmd, mach_number)


def controller_function(
    time, sampling_rate, state, state_history, observed_variables, aerofreno
):
  def close_and_log():
    aerofreno.deployment_level = 0
    airbrakes_deployment_history.append((time, aerofreno.deployment_level))
    airbrakes_force_history.append((time, 0.0))  # Fuerza 0 si está cerrado
    return aerofreno.deployment_level

  if enable_airbrakes is False:
    return close_and_log()

  if time < TIMANFAYA.burn_out_time:
    return close_and_log()

  altitude_ASL = state[2]
  vx, vy, vz = state[3], state[4], state[5]

  wind_x = env.wind_velocity_x(altitude_ASL)
  wind_y = env.wind_velocity_y(altitude_ASL)
  free_stream_speed = (
      (wind_x - vx) ** 2 + (wind_y - vy) ** 2 + vz**2
  ) ** 0.5
  mach_number = free_stream_speed / env.speed_of_sound(altitude_ASL)

  if vz < 0 or altitude_ASL < 1500 + env.elevation:
    return close_and_log()

  deployment_level = cd_monitor_strategy(
      altitude_ASL, vz, mach_number, env, ASPID, TARGET_APOGEE
  )
  deployment_level = float(np.clip(deployment_level, 0.0, 1.0))

  # --- CÁLCULO DE LA FUERZA DEL AEROFRENO ---
  rho = env.density(altitude_ASL)
  ref_area = np.pi * ASPID.radius**2

  # Obtenemos Cd actual desplegado y Cd cerrado (0%)
  cd_current = aerofreno.drag_coefficient(deployment_level, mach_number)
  cd_closed = aerofreno.drag_coefficient(0.0, mach_number)

  # La fuerza extra debida exclusivamente al aerofreno (Delta Cd)
  cd_delta = cd_current - cd_closed
  fuerza_aerofreno = 0.5 * rho * (free_stream_speed**2) * ref_area * cd_delta

  # Guardar registros
  aerofreno.deployment_level = deployment_level
  airbrakes_deployment_history.append((time, deployment_level))
  airbrakes_force_history.append((time, fuerza_aerofreno))
  apogee_prediction_history.append(
      (time, cd_monitor_diagnostics.get("last_apogee_est", altitude_ASL))
  )

  return deployment_level


aerofreno = ASPID.add_air_brakes(
    drag_coefficient_curve=r"RESOURCES\airbrakes.csv",
    override_rocket_drag=True,
    controller_function=controller_function,
    sampling_rate=100,  # 100 Hz
)

# Flight Simulation
test_flight = Flight(
    environment=env,
    rocket=ASPID,
    rail_length=12,
    inclination=84.0,
    terminate_on_apogee=True,
)

# --- PROCESAMIENTO Y PRESENTACIÓN DE RESULTADOS ---
times_f, forces = zip(*airbrakes_force_history)
fuerza_maxima = max(forces)

print(f"Fuerza máxima ejercida por los aerofrenos: {fuerza_maxima:.2f} N")

# Gráfica de la fuerza ejercida por los aerofrenos
plt.figure(figsize=(10, 5))
plt.plot(times_f, forces, label="Fuerza del Aerofreno (N)", color="red")
plt.xlabel("Tiempo (s)")
plt.ylabel("Fuerza (N)")
plt.title("Fuerza Aerodinámica Producida por los Aerofrenos")
plt.grid(True)
plt.legend()
plt.show()