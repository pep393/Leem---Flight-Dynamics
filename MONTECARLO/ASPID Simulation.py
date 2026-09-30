import os

import numpy as np

from rocketpy import (
    Environment,
    SolidMotor,
    Rocket,
    Flight,
    StochasticEnvironment,
    StochasticSolidMotor,
    StochasticRocket,
    StochasticNoseCone,
    StochasticTrapezoidalFins,
    StochasticParachute,
    StochasticFlight,
    MonteCarlo,
    StochasticAirBrakes
)
from MONTECARLO.airbrakes_control import AirbrakesController, plot_airbrakes

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # RESOURCES paths work from any working directory

G0 = 9.80665  # m/s^2, para pasar de aceleracion a "g's"

chamber_height = 0.923
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.896

enable_airbrakes = False
enable_weather = False

# Airbrakes controller
ACTIVATION_ALTITUDE = 1500  # m AGL, airbrakes only act above it and while ascending
SAMPLING_RATE = 5  # Hz
KP = 0.005  # (m/s^2) of commanded deceleration per m of apogee error (>= 0.02 chatters)
KI = 0.1  # (m/s^2) per m*s of apogee error

if enable_weather:
    env = Environment(date=(2026, 9, 13, 15)) 
    env.set_location(latitude=39.44580338814086, longitude=-8.29626628763608)
    env.set_elevation("Open-Elevation")
    env.set_atmospheric_model(type="Windy", file="GFS")

    env.all_info()

    stochastic_env = StochasticEnvironment(
    environment=env,
    elevation=(env.elevation, 5),                 # +/- 5 m de incertidumbre de elevación
    wind_velocity_x_factor=(1, 0.10),               # +/- 10% sobre el perfil de viento u
    wind_velocity_y_factor=(1, 0.10),               # +/- 10% sobre el perfil de viento v
    )
else:
    env = Environment()

# NOTA: el controlador del aerofreno guarda una referencia fija a "env" para
# calcular la altitud AGL de activacion (state[2] - env.elevation). En un
# Montecarlo, StochasticEnvironment puede generar entornos con distinta
# elevacion en cada simulacion, pero el controlador seguira usando la
# elevacion de este "env" base. Si enable_weather=False (elevacion 0) esto
# no supone ningun problema; si activas el clima estocastico y quieres que
# el controlador use la elevacion real de cada simulacion, habria que
# exponer el entorno de cada vuelo al controlador (por ejemplo mediante un
# atributo que MonteCarlo actualice antes de cada simulacion).

TARGET_APOGEE = 3000 + env.elevation  # Target apogee in meters above sea level



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

stochastic_motor = StochasticSolidMotor(
    solid_motor=TIMANFAYA,
    total_impulse=(TIMANFAYA.total_impulse, 0.03 * TIMANFAYA.total_impulse),  # +/- 2%
    burn_out_time=(TIMANFAYA.burn_out_time, 0.03 * TIMANFAYA.burn_out_time),   # +/- 2%
    grain_density=(1793, 15),
)

ASPID = Rocket(
    radius=RADIO_ASPID,
    mass=14,
    inertia=(6.175, 6.175, 0.05),
    power_off_drag=r"RESOURCES\mach_cd_prot_cono_cola.csv",
    power_on_drag=r"RESOURCES\mach_cd_prot_cono_cola_power_on.csv",
    center_of_mass_without_motor=1.4607,
    coordinate_system_orientation="nose_to_tail",
)

ASPID.add_motor(TIMANFAYA, position=LONGITUD_ASPID - chamber_height)

nose_cone = ASPID.add_nose(length=0.40, kind="ogive", position=0)

fin_set = ASPID.add_trapezoidal_fins(
    n=4,
    root_chord=0.2,
    tip_chord=0.100,
    span=0.12,
    position=LONGITUD_ASPID - 0.2 - 0.03,
)

drogue = ASPID.add_parachute(
    "drogue",
    cd_s=0.51586,
    trigger="apogee",
    radius=0.523,
    lag=1,
)

main = ASPID.add_parachute(
    "main",
    cd_s=6.126,
    trigger=450,
    radius=1.8027,
    lag=1,
)

stochastic_rocket = StochasticRocket(
    rocket=ASPID,
    center_of_mass_without_motor=(1.4607, 0.01),
    power_off_drag_factor=(1, 0.05),    # +/- 5% sobre la curva de Cd
    power_on_drag_factor=(1, 0.05),
)

stochastic_nosecone = StochasticNoseCone(nosecone=nose_cone)
stochastic_fins = StochasticTrapezoidalFins(trapezoidal_fins=fin_set)
stochastic_drogue = StochasticParachute(parachute=drogue)
stochastic_main = StochasticParachute(parachute=main)

stochastic_rocket.add_motor(stochastic_motor)
stochastic_rocket.add_nose(stochastic_nosecone)
stochastic_rocket.add_trapezoidal_fins(stochastic_fins)
stochastic_rocket.add_parachute(stochastic_drogue)
stochastic_rocket.add_parachute(stochastic_main)

controller = AirbrakesController(ASPID, env, TARGET_APOGEE, KP, KI, SAMPLING_RATE)


def make_controller_function(nominal_rocket, nominal_env, target_apogee, kp, ki, sampling_rate):
    state = {"controller": None, "last_time": None}
 
    def controller_function(time, sampling_rate_, flight_state, state_history, observed_variables, air_brakes):
        if state["last_time"] is None or time <= state["last_time"]:
            state["controller"] = AirbrakesController(
                nominal_rocket, nominal_env, target_apogee, kp, ki, sampling_rate
            )
        state["last_time"] = time
 
        active = (
            enable_airbrakes
            and flight_state[2] - nominal_env.elevation > ACTIVATION_ALTITUDE
            and flight_state[5] > 0
        )
        air_brakes.deployment_level, log = state["controller"].update(
            time, flight_state, air_brakes, active
        )
        return log
 
    return controller_function


controller_function = make_controller_function(ASPID, env, TARGET_APOGEE, KP, KI, SAMPLING_RATE)
 
aerofreno, aerofreno_controller = ASPID.add_air_brakes(
    drag_coefficient_curve=r"RESOURCES\airbrakes.csv",
    override_rocket_drag=False,
    controller_function=controller_function,
    sampling_rate=SAMPLING_RATE,
    return_controller=True,  # necesario para poder usarlo luego en StochasticRocket.add_air_brakes
)

stochastic_rocket.add_air_brakes(aerofreno, aerofreno_controller)


test_flight = Flight(
    environment=env,
    rocket=ASPID,
    rail_length=12,
    inclination=84.0,
    terminate_on_apogee=False,
)

stochastic_flight = StochasticFlight(
    flight=test_flight,
    inclination=(84.0, 1.0),   # +/- 1 grado
)


# ------------------------------------------------------------------
#  Funciones del data collector para el Montecarlo
# ------------------------------------------------------------------

def get_trajectory(flight):
    """x, y, z (AGL) en funcion del tiempo, para graficar en 3D."""
    times = np.linspace(0, flight.t_final, 200)
    x = [flight.x(t) for t in times]
    y = [flight.y(t) for t in times]
    z_agl = [flight.z(t) - flight.env.elevation for t in times]
    return {"time": times.tolist(), "x": x, "y": y, "z_agl": z_agl}


def get_stability(flight):
    """Margen de estabilidad en funcion del tiempo."""
    times = np.linspace(0, flight.t_final, 200)
    stability = [flight.stability_margin(t) for t in times]
    return {"time": times.tolist(), "stability": stability}


def get_out_of_rail_stability(flight):
    return flight.stability_margin(flight.out_of_rail_time)


def get_min_stability(flight):
    return flight.min_stability_margin


def get_max_stability(flight):
    return flight.max_stability_margin


def get_out_of_rail_angle_of_attack(flight):
    return flight.angle_of_attack(flight.out_of_rail_time)


def get_out_of_rail_velocity(flight):
    return flight.out_of_rail_velocity


def get_impact_position(flight):
    return (flight.x_impact, flight.y_impact)


def get_impact_velocity(flight):
    return flight.impact_velocity


def get_burnout_altitude(flight):
    # Altitud AGL en el instante de apagado del motor
    return flight.z(flight.rocket.motor.burn_out_time) - flight.env.elevation


def get_apogee_time(flight):
    return flight.apogee_time


def get_apogee(flight):
    return flight.apogee - flight.env.elevation


def get_flight_time(flight):
    return flight.t_final


def get_max_velocity(flight):
    return flight.max_speed


def get_max_mach_number(flight):
    return flight.max_mach_number


def get_max_dynamic_pressure(flight):
    return flight.max_dynamic_pressure


def get_max_acceleration_burn(flight):
    return flight.max_acceleration


def get_max_g_burn(flight):
    return get_max_acceleration_burn(flight) / G0


custom_data_collector = {
    # Funciones (series temporales)
    "trajectory": get_trajectory,
    "stability_vs_time": get_stability,

    # Datos numericos en la salida del rail
    "out_of_rail_stability": get_out_of_rail_stability,
    "out_of_rail_angle_of_attack": get_out_of_rail_angle_of_attack,
    "out_of_rail_velocity_mine": get_out_of_rail_velocity,

    # Estabilidad
    "min_stability": get_min_stability,
    "max_stability": get_max_stability,

    # Impacto
    "impact_position": get_impact_position,
    "impact_v": get_impact_velocity,

    # Burnout / apogeo / duracion de vuelo
    "burnout_altitude": get_burnout_altitude,
    "apogee_t": get_apogee_time,
    "apogee_mine": get_apogee,
    "flight_time": get_flight_time,

    # Maximos globales
    "max_velocity": get_max_velocity,
    "max_mach": get_max_mach_number,
    "max_dynamic": get_max_dynamic_pressure,

    # Maximos durante el quemado del motor
    "max_acceleration_burn": get_max_acceleration_burn,
    "max_g_burn": get_max_g_burn,
}


aspid_dispersion = MonteCarlo(
    filename="aspidMonteCarlo3",
    environment=stochastic_env,
    rocket=stochastic_rocket,
    flight=stochastic_flight,
    data_collector=custom_data_collector,
)

if __name__ == "__main__":
    aspid_dispersion.simulate(
        number_of_simulations=10000,
        append=True,
        include_function_data=False
    )

    aspid_dispersion.plots.ellipses()
    aspid_dispersion.all_info()