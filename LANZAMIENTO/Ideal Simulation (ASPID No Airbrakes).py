# Código ideal, configuración ASPID

from rocketpy import Environment, Rocket, Flight, SolidMotor, utilities
import numpy as np
import rocketpy.utilities as _rpu
from rocketpy.mathutils import Function
import matplotlib.pyplot as plt

chamber_height = 0.923
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.7

env = Environment()




aspid_engine = SolidMotor(
    thrust_source=r"RECURSOS\ASPIDTHRUST.csv",
    dry_mass=7.423,
    dry_inertia=(1.206, 1.205, 0.023),
    nozzle_radius=0.065,
    grain_number=4,
    grain_density=1730,
    grain_outer_radius=49 / 1000,
    grain_initial_inner_radius=32.5 / 2000,
    grain_initial_height=170 / 1000,
    grain_separation=15 / 1000,
    grains_center_of_mass_position=0.433,
    center_of_dry_mass_position=0.481,
    nozzle_position=chamber_height,
    throat_radius=12.5 / 1000,
    coordinate_system_orientation="combustion_chamber_to_nozzle",
)

aspid_engine.thrust()
aspid_engine.burn_rate()


ASPID = Rocket(
    radius=RADIO_ASPID,
    mass=15.32,  
    inertia=(3.613, 3.613, 0.041),
    power_off_drag=r"RECURSOS\datos_convertidos.csv",
    power_on_drag=r"RECURSOS\CD_ON_ASPID.csv",
    center_of_mass_without_motor=1.7,    # 1.1575
    coordinate_system_orientation="nose_to_tail"
)

ASPID.add_motor(aspid_engine, position=LONGITUD_ASPID - chamber_height)
ASPID.add_nose(length=0.40, kind="ogive", position=0)
ASPID.add_trapezoidal_fins(
    n=4,
    root_chord=0.2,
    tip_chord=0.072,
    span=0.15,
    position=LONGITUD_ASPID - 0.2 - 0.01
)



"""
ASPID.add_parachute(
    "drogue",
    cd_s=0.516,  
    trigger="apogee",
    radius=0.52,
    lag=1,
)

ASPID.add_parachute(
    "main",
    cd_s=6.171,
    trigger=300,
    radius=1.78,
    lag=1,
)
"""

test_flight = Flight(
    environment=env,
    rocket=ASPID,
    rail_length=10,
    inclination=84.0,    
    terminate_on_apogee=True,
)


# print(test_flight.out_of_rail_stability_margin)
# print(test_flight.out_of_rail_velocity)
# test_flight.stability_margin()


