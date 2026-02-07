### CONFIGURACION DE LEEMUR COHETE DE PRUEBA 1KM ###
import datetime
from rocketpy import Environment, SolidMotor, Rocket, Flight, StochasticRocket, StochasticSolidMotor, MonteCarlo, StochasticEnvironment, StochasticFlight, StochasticNoseCone, StochasticTrapezoidalFins, Function, StochasticParachute
import numpy as np
import matplotlib.pyplot as plt
from math import pi

LONGITUD = 1.74                 #Longitud [m]
RADIO = 0.065                   # Radio [m]

SIMULATION_TIME =300

env =Environment()

stochastic_environment = StochasticEnvironment(
    environment=env
)
"""
env = Environment(latitude=40.0, longitude=-3.0)
env.set_elevation(elevation="Open-Elevation")
env.set_date((2025, 11, 1, 15))
env.set_atmospheric_model(type="Ensemble", file="GEFS")

stochastic_environment = StochasticEnvironment(
    environment=env,
    ensemble_member=list(range(env.num_ensemble_members))
)
"""
env.all_info()
stochastic_environment.visualize_attributes()
MOTOR = SolidMotor(
    thrust_source="RECURSOS\FR_Vulkan.eng",
    dry_mass=5.00,                              # CHECK
    dry_inertia=(3.081, 3.081, 0.02569),
    nozzle_radius=30 / 1000,                        
    grain_number=1,                             # CHECK
    grain_density=1841,                         # CHECK
    grain_outer_radius=91 / 2000,               # CHECK
    grain_initial_inner_radius=36 / 2000,       # CHECK
    grain_initial_height=200 / 1000,            # CHECK
    grain_separation=15 / 1000,                 
    grains_center_of_mass_position= 0.185,       
    center_of_dry_mass_position= 0.185,
    nozzle_position=0,  
    throat_radius=18 / 2000,                    # CHECK
    coordinate_system_orientation="nozzle_to_combustion_chamber",
)

stochastic_motor = StochasticSolidMotor(
    solid_motor=MOTOR,
    total_impulse=80
)


###  COHETE ###
ROCKET = Rocket(
    radius=RADIO,
    mass=5.144,                 # Masa sin motor [kg]  
    inertia=(3.081, 3.081, 0.02569),
    power_off_drag="RECURSOS\CD_new.csv",
    power_on_drag="RECURSOS\CD_new.csv",
    center_of_mass_without_motor= 0.716,
    coordinate_system_orientation= "nose_to_tail")
ROCKET.add_motor(MOTOR, position=LONGITUD)

nose_cone = ROCKET.add_nose(
    length=0.33, kind="ogive", position=0
)

fin_set = ROCKET.add_trapezoidal_fins(
    n=4,
    root_chord=0.20,
    tip_chord=0.07,
    span=0.20,
    position=1.53
)


Main = ROCKET.add_parachute(
    name = "Main",
    cd_s=5.97,
    trigger="apogee",
    lag=1   
)




stochastic_rocket = StochasticRocket(
    rocket=ROCKET
)
stochastic_nosecone = StochasticNoseCone(
    nosecone = nose_cone
)

stochastic_fins = StochasticTrapezoidalFins(
    trapezoidal_fins=fin_set
)
stochastic_main = StochasticParachute(
    parachute=Main,
    cd_s=0.15497,
    lag=0.2,
)



stochastic_rocket.add_motor(stochastic_motor)
stochastic_rocket.add_nose(stochastic_nosecone)
stochastic_rocket.add_trapezoidal_fins(stochastic_fins)
stochastic_rocket.add_parachute(stochastic_main)



flight = Flight(
    environment=env,
    rocket=ROCKET,
    rail_length=6,
    inclination=84.0
)
stochastic_flight = StochasticFlight(
    flight=flight,
    inclination=1
)






def get_trajectory(flight):             
    times = np.linspace(0, SIMULATION_TIME ,num=1000)
    trajectory = []
    for time in times:
        trajectory_data = flight.z(time)
        trajectory.append(trajectory_data)
    return trajectory


def get_acceleration(flight):             
    times = np.linspace(0, SIMULATION_TIME ,num=1000)
    acceleration = []
    for time in times:
        acceleration_data = flight.acceleration(time)
        acceleration.append(acceleration_data)
    return acceleration


def get_max_acceleration(flight):
    return flight.max_acceleration


def get_stability(flight):             
    times = np.linspace(0, SIMULATION_TIME ,num=1000)
    stability = []
    for time in times:
        stability_data = flight.stability_margin(time)
        stability.append(stability_data)
    return stability

def get_min_stability(flight):
    return flight.min_stability_margin

def get_max_stability(flight):
    return flight.max_stability_margin

def get_min_stability_time(flight):
    return flight.min_stability_margin_time

def get_dynamic_pressure(flight):             
    times = np.linspace(0, SIMULATION_TIME ,num=1000)
    dynamic = []
    for time in times:
        dynamic_data = flight.dynamic_pressure(time)
        dynamic.append(dynamic_data)
    return dynamic

def get_max_q(flight):
    return flight.max_dynamic_pressure


def get_impact_v(flight):
    return flight.impact_velocity

def get_velocity(flight):             
    times = np.linspace(0, SIMULATION_TIME ,num=1000)
    velocity = []
    for time in times:
        velocity_data = flight.vz(time)
        velocity.append(velocity_data)
    return velocity

def get_zoom_velocity(flight):             
    times = np.linspace(0, 30 ,num=60)
    velocity = []
    for time in times:
        velocity_data = flight.vz(time)
        velocity.append(velocity_data)
    return velocity



custom_data_collector = {
                        "min_stability" : get_min_stability,
                        "max_stability" :get_max_stability,
                        "min_stability_time" : get_min_stability_time,
                        "max_stability_time": get_max_stability,
                        "stability": get_stability,

                        "max_acceleration": get_max_acceleration,
                        "acceleration": get_acceleration,
                        
                        "trajectory": get_trajectory,       # Solo eje z

                        "max_dynamic_pressure": get_max_q,
                        "dynamic_pressure": get_dynamic_pressure,

                        "impact_v" : get_impact_v,
                        "velocity" : get_velocity,

                        "zoom_velocity" : get_zoom_velocity,
                        

                        
}    


test_dispersion = MonteCarlo(
    filename= "pruebaMonteCarlo",
    environment =stochastic_environment,
    rocket = stochastic_rocket,
    flight=stochastic_flight,
    data_collector=custom_data_collector
)


test_dispersion.simulate(
    number_of_simulations = 10,
)

test_dispersion.plots.ellipses()
