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
env = Environment(
    latitude=39.3897,
    longitude= -8.288963,
    date= (2024, 9, 21, 14 )
    )

env.set_elevation("Open-Elevation")

import datetime
tomorrow = datetime.date.today() + datetime.timedelta(days=14)

env.set_date(
    (tomorrow.year, tomorrow.month, tomorrow.day, 16)
)  # Hour given in UTC time

#env.set_atmospheric_model(type="Windy", file="GFS")
env.set_atmospheric_model(
    type="custom_atmosphere",
    pressure=None,
    temperature=None,
    wind_u=[        # Este oeste
        (0, -8*math.sin(math.radians(AzimutAngle))), # 5 m/s at 0 m from west to east
        (5000, -8*math.sin(math.radians(AzimutAngle))),
    ],
    wind_v=[        # Norte Sur
        (0, -8*math.cos(math.radians(AzimutAngle))), # 0 m/s at 0 m from south to north
        (5000, -8*math.cos(math.radians(AzimutAngle))),
   ]
)

# MOTOR DEFINITION
meteor_EUROC = SolidMotor(
    thrust_source="motorA_WCS.eng",
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

# ROCKET DEFINITION

URSA = Rocket(
    radius=158 / 2000,
    mass=12.148,
    inertia=(5.469, 5.469, 0.059),
    power_off_drag=r"C:\Users\joseh\PycharmProjects\modidinha del leem\CD_new.csv",
    power_on_drag=r"C:\Users\joseh\PycharmProjects\modidinha del leem\CD_new.csv",
    center_of_mass_without_motor= 1.31,
    coordinate_system_orientation= "tail_to_nose")
URSA.add_motor(meteor_EUROC, position=-PosCM_sinMotor - SeparTobera)

nose_cone = URSA.add_nose(
    length=0.6, kind="ogive", position= longURSA - PosCM_sinMotor,
)

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
    heading=AzimutAngle
)


# Crear una instancia de Kml
kml = Kml()

# Añadir un recorrido (línea) en el KML
linestring = kml.newlinestring(name="Rocket Trajectory")

# Asignar los puntos (latitud, longitud, altitud) a la línea
linestring.coords = [(lon, lat, alt) for lon, lat, alt in zip(test_flight.longitude.y_array, test_flight.latitude.y_array, test_flight.altitude.y_array)]

# Configurar el estilo de la línea (opcional)
linestring.altitudemode = "absoxlute"  # La altitud es absoluta respecto al nivel del suelo
linestring.extrude = 0                # Hace que la línea se conecte al suelo
linestring.style.linestyle.width = 3   # Grosor de la línea
linestring.style.linestyle.color = "ff0000ff"  # Color azul (en formato AABBGGRR)

# Guardar el archivo KML
kml.save("rocket_trajectory.kml")

print(test_flight.acceleration(test_flight.apogee_time))
#
print(test_flight.acceleration(test_flight.apogee_time + 20))
#
test_flight.prints.maximum_values()
#
test_flight.prints.impact_conditions()

test_flight.prints.apogee_conditions()

test_flight.prints.out_of_rail_conditions()

meteor_EUROC.plots.thrust()

test_flight.prints.events_registered()

test_flight.prints.burn_out_conditions()

URSA.all_info()

meteor_EUROC.plots.draw()

env.plots.atmospheric_model()

# Perform a Fourier Analysis
Fs = 1000.0
# sampling rate
Ts = 1.0 / Fs
# sampling interval
t = np.arange(0, 400, Ts)  # time vector
# frequency of the signal
y = test_flight.attitude_angle(t) #- np.mean(flight.attitude_angle(t))
# Create the plot
fig, ax = plt.subplots(2, 1)
ax[0].plot(t, y)
ax[0].set_xlabel("Time")
ax[0].set_ylabel("Pitch Angle")
ax[0].set_xlim((0, 20))
ax[0].grid()

test_flight.plots.trajectory_3d()

URSA.center_of_mass.plot(0, test_flight.apogee_time)
