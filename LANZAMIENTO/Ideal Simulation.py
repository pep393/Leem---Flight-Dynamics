from rocketpy import Environment, SolidMotor, Rocket, Flight, Function
from math import pi
import numpy as np
import matplotlib.pyplot as plt


LONGITUD = 2.83

env = Environment(

)

"""env.set_atmospheric_model(
    type="custom_atmosphere",
    pressure=None,
    wind_v=[
        (0, -6), # 5 m/s at 0 m
        (3000, -6) # 10 m/s at 1000 m
    ],
)"""


MOTOR = SolidMotor(
    thrust_source=r"RECURSOS/motorA_WCS.eng",
    reshape_thrust_curve=[4, 9000],    # Escala el thrust para que de un impulso total quemando durante x tiempo
    dry_mass=5.00,                              # CHECK
    dry_inertia=(3.081, 3.081, 0.02569),
    nozzle_radius=30 / 1000,                        
    grain_number=4,                             # CHECK
    grain_density=1841,                         # CHECK
    grain_outer_radius=91 / 2000,               # CHECK
    grain_initial_inner_radius=36 / 2000,       # CHECK
    grain_initial_height=200 / 1000,            # CHECK
    grain_separation=15 / 1000,                 
    grains_center_of_mass_position= 0.185,       # CHECK
    center_of_dry_mass_position= 0.185,
    nozzle_position=0,  
    throat_radius=18 / 2000,                    # CHECK
    coordinate_system_orientation="nozzle_to_combustion_chamber",
)


COHETE = Rocket(
    radius=0.065,
    mass=13,
    inertia=(0.5, 0.5, 0.005),
    power_off_drag=r"RECURSOS/CD_new.csv",
    power_on_drag=r"RECURSOS/CD_new.csv",
    center_of_mass_without_motor= 0.716,
    coordinate_system_orientation= "nose_to_tail"
    )

COHETE.add_motor(MOTOR, position=LONGITUD)      # MOTOR

COHETE.add_nose(length=0.330, kind="ogive", position=0)

COHETE.add_trapezoidal_fins(
            n=4,
            root_chord=0.20,
            tip_chord=0.07,
            span=0.20,
            position=1.53
        )


flight = Flight(
    environment=env,
    rocket=COHETE,
    rail_length=6,
    inclination=84.0,
    heading=0
)



flight.mach_number()

"""

tiempos = np.linspace(0,5,1000)
function = Function(COHETE.evaluate_center_of_mass())

y_data = []
for t in tiempos:
    y = function.get_value(t)
    y_data.append(y)

plt.plot(tiempos, y_data)
plt.grid()
plt.xlabel("Tiempo [s]")
plt.ylabel("Posición CM [m]")
plt.title("Posición del centro de masas desde la punta (Cohete + Motor)")
plt.show()
"""

"""
tiempos = np.linspace(0,60,1000)
function = Function(COHETE.evaluate_center_of_pressure())

y_data = []
for t in tiempos:
    y = function.get_value(t)
    y_data.append(y)

plt.plot(tiempos, y_data)
plt.grid()
plt.title("Presion")
plt.show()"""