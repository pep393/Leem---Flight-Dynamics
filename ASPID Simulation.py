import os

from rocketpy import Environment, SolidMotor, Rocket, Flight
from rocketpy.utilities import fin_flutter_analysis
from airbrakes_control import AirbrakesController, plot_airbrakes

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # RESOURCES paths work from any working directory

chamber_height = 0.923
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.896

enable_airbrakes = True 
enable_weather = False

# Airbrakes controller
ACTIVATION_ALTITUDE = 1500  # m AGL, airbrakes only act above it and while ascending
SAMPLING_RATE = 100  # Hz
KP = 0.005  # (m/s^2) of commanded deceleration per m of apogee error (>= 0.02 chatters)
KI = 0.1  # (m/s^2) per m*s of apogee error

if enable_weather:
    env = Environment(date=(2026,10,17,15)) #Date:(2026,10,17,16)
    env.set_location(latitude=39.44580338814086, longitude=-8.29626628763608)
    env.set_elevation("Open-Elevation")
    env.set_atmospheric_model(type="Windy", file="GFS")
else:
    env = Environment()


TARGET_APOGEE = 3000  + env.elevation  # Target apogee in meters above sea level


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
    mass=14,
    inertia=(6.175, 6.175, 0.05),
    power_off_drag=r"RESOURCES\mach_cd_prot_cono_cola.csv",
    power_on_drag=r"RESOURCES\mach_cd_prot_cono_cola_power_on.csv",
    center_of_mass_without_motor=1.4607,
    coordinate_system_orientation="nose_to_tail"
)

ASPID.add_motor(TIMANFAYA, position=LONGITUD_ASPID - chamber_height)
ASPID.add_nose(length=0.40, kind="ogive", position=0)
ASPID.add_trapezoidal_fins(
    n=4,
    root_chord=0.2,
    tip_chord=0.100,
    span=0.12,
    position=LONGITUD_ASPID - 0.2 - 0.03
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
    trigger=450,
    radius=1.8027,
    lag=1,
)


controller = AirbrakesController(ASPID, env, TARGET_APOGEE, KP, KI, SAMPLING_RATE)


def controller_function(time, sampling_rate, state, state_history, observed_variables, air_brakes):
    # Airbrakes only act if enabled, above ACTIVATION_ALTITUDE (AGL) and while ascending
    active = enable_airbrakes and state[2] - env.elevation > ACTIVATION_ALTITUDE and state[5] > 0
    air_brakes.deployment_level, log = controller.update(time, state, air_brakes, active)
    return log


aerofreno = ASPID.add_air_brakes(
    drag_coefficient_curve=r"RESOURCES\airbrakes.csv",
    override_rocket_drag=False,
    controller_function=controller_function,
    sampling_rate=SAMPLING_RATE,
)

test_flight = Flight(
    environment=env,
    rocket=ASPID,
    rail_length=12, 
    inclination=84.0,
    terminate_on_apogee=False)



