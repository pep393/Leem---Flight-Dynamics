from rocketpy import Environment, GenericMotor, Rocket, Flight, Function
from math import pi
import numpy as np
import matplotlib.pyplot as plt


LONGITUD = 2.462

env = Environment()

MOTOR = GenericMotor(
    thrust_source="RECURSOS/FR_Vulkan.eng",
    reshape_thrust_curve=[3.4, 2547],
    burn_time=3.4,
    chamber_radius = 0.065,
    chamber_height = 0.7,   
    chamber_position=0.51,
    dry_mass=7.02,
    propellant_initial_mass=7.98,
    dry_inertia=(0.5, 0.5, 0.005),
    nozzle_radius=0.065 / 2,
)



COHETE = Rocket(
    radius=0.065,
    mass=11.7,
    inertia=(3.613, 3.613, 0.041),
    power_off_drag=r"RECURSOS/CD_OFF_ASPID.csv",
    power_on_drag=r"RECURSOS/CD_ON_ASPID.csv",
    center_of_mass_without_motor= 1.1575,
    coordinate_system_orientation= "nose_to_tail"
    )

COHETE.add_motor(MOTOR, position=LONGITUD)      # MOTOR

COHETE.add_nose(length=0.6, kind="ogive", position=0)

COHETE.add_trapezoidal_fins(
            n=4,
            root_chord=0.20,
            tip_chord=0.07,
            span=0.20,
            position=LONGITUD - 0.2
        )

flight = Flight(
    environment=env,
    rocket=COHETE,
    rail_length=6,
    inclination=86.0,
    heading=0
)

print(flight.apogee)