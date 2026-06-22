from rocketpy import Environment, SolidMotor, Rocket, Flight

import numpy as np
#from scipy import stats
from datetime import datetime
import math
from simplekml import Kml
import matplotlib.pyplot as plt
from rocketpy.plots.compare import CompareFlights

# Logitud del cohete
longURSA= 2.54
# Poscion del CM cohete sin motor(carcasa+tapa+tobera+tornillos_motor)
PosCM_sinMotor= 1.31
# Distancia que sale la tobera del cohete
SeparTobera= 0.04765
# Azimut angle
AzimutAngle=133


# ENVIROMENT DEFINITION
env = Environment()

# MOTOR DEFINITION
meteor_EUROC = SolidMotor(
    thrust_source=r"SM12_Aethon_Ensayo_16_09_24.eng",
    reshape_thrust_curve=[2.3,9500],
    dry_mass=7.95,
    dry_inertia=(1.206, 1.205, 0.023),
    nozzle_radius=30 / 1000,
    grain_number=4,
    grain_density=1841,
    grain_outer_radius=49 / 1000,
    grain_initial_inner_radius=32.5 / 2000,
    grain_initial_height=170 / 1000,
    grain_separation=15 / 1000,
    grains_center_of_mass_position= 451.75 / 1000,
    center_of_dry_mass_position= 502 / 1000,
    nozzle_position=0,
    throat_radius=12.5 / 1000,
    coordinate_system_orientation="nozzle_to_combustion_chamber",
)
meteor_EUROC.thrust()

# ROCKET DEFINITION

URSA = Rocket(
    radius=158 / 2000,
    mass=12.148,
    inertia=(5.469, 5.469, 0.059),
    power_off_drag=r"RECURSOS/CD_OFF_ASPID.csv",
    power_on_drag=r"RECURSOS/CD_ON_ASPID.csv",
    center_of_mass_without_motor= 1.31,
    coordinate_system_orientation= "tail_to_nose")
URSA.add_motor(meteor_EUROC, position=-PosCM_sinMotor - SeparTobera)

nose_cone = URSA.add_nose(
    length=0.6, kind="ogive", position= longURSA - PosCM_sinMotor,
)
"""
main = URSA.add_parachute(
    name="main",
    cd_s=1.85*(2.2*2.2),
    trigger=500,
    lag=0,
    noise=(0, 8.3, 0.5),
    sampling_rate=1000
)
drogue = URSA.add_parachute(
    name="Drogue",
    cd_s=1.85*1,
    trigger="apogee" ,
    lag =1,
    noise=(0, 8.3, 0.5),
    sampling_rate=600
)
"""
fin_set = URSA.add_trapezoidal_fins(
    n=4,
    root_chord=0.2,
    tip_chord=0.01,
    span=0.16,
    position=-PosCM_sinMotor+ 0.2,
    sweep_angle= 0
)

test_flight = Flight(
    environment=env,
    rocket=URSA,
    rail_length=12,
    inclination=84.0,
    heading=AzimutAngle,

)

