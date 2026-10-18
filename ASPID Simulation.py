# ROCKETPY SIMULATION 

import os
from rocketpy import Environment, SolidMotor, Rocket, Flight, RailButtons
from rocketpy.utilities import fin_flutter_analysis
from LANZAMIENTO.airbrakes_control import AirbrakesController, plot_airbrakes

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # RESOURCES paths work from any working directory

chamber_height = 0.923
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.95

enable_airbrakes = True
enable_weather = False

# Airbrakes controller
ACTIVATION_ALTITUDE = 1500 
SAMPLING_RATE = 20  # Hz
KP = 0.005  # (m/s^2) of commanded deceleration per m of apogee error
KI = 0.1  # (m/s^2) per m*s of apogee error

if enable_weather:
    env = Environment(
        date=(2026, 10, 19, 9),    
        latitude=39.392547, 
        longitude=-8.289517,
    )
    env.set_atmospheric_model(type="forecast", file="GFS")
    env.set_elevation(160)



else:
    env = Environment()
        # Viento constante de 8 m/s (puedes ajustar la dirección con wind_v si quieres componente en otro eje)
    env.set_atmospheric_model(
        type="custom_atmosphere",
        wind_u=8,   # componente del viento en el eje Este-Oeste (m/s)
        wind_v=0,   # componente del viento en el eje Norte-Sur (m/s)
    )


TARGET_APOGEE = 3000  + env.elevation  # Target apogee in meters above sea level


TIMANFAYA = SolidMotor(
    thrust_source=r"RESOURCES\ASPIDTHRUST.csv", 
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



ASPID = Rocket(
    radius=RADIO_ASPID,
    mass=14.6,      #14.6 normal
    inertia=(6.175, 6.175, 0.05),
    power_off_drag=r"RESOURCES\mach_cd_sin_chaflan_preciso.csv",
    power_on_drag=r"RESOURCES\mach_cd_sin_chaflan_preciso_power_on.csv",
    center_of_mass_without_motor=1.438,
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
    # heading=145,    #145  90->Este 0->Norte
    heading = 90, 
    terminate_on_apogee=False)       


test_flight.plots.attitude_data()
test_flight.plots.trajectory_3d()
test_flight.plots.aerodynamic_angles()
# plot_airbrakes(test_flight, test_flight, ACTIVATION_ALTITUDE, TARGET_APOGEE)
print(test_flight.altitude(test_flight.apogee_time))
print(test_flight.out_of_rail_velocity)
# test_flight.stability_margin()
# test_flight.angle_of_attack()
# test_flight.plots.animate_rotate()



