import matplotlib.pyplot as plt
import numpy as np

from matplotlib import cm


from rocketpy import Environment, SolidMotor, Rocket, Flight

from math import sqrt
############### DEFINICIÓN DEL COHETE y SIMULACIÓN ##################
LONGITUD = 1.74

# env = Environment()     # ISA

env = Environment(
    date=(2025, 11, 20, 16),          # Año, Mes, Día, Hora
    latitude=40.44552575443143,
    longitude= -3.7302877778310006,
    )


env.set_elevation("Open-Elevation")
env.set_atmospheric_model(type="forecast", file="GFS")   # Se pueden cambiar a otros...

motor_teorico = SolidMotor(
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



COHETE = Rocket(
    radius=0.065,
    mass=5.144,
    inertia=(0.5, 0.5, 0.005),
    power_off_drag="RECURSOS/CD_new.csv",
    power_on_drag="RECURSOS/CD_new.csv",
    center_of_mass_without_motor= 0.716,
    coordinate_system_orientation= "nose_to_tail"
    )

COHETE.add_motor(motor_teorico, position=LONGITUD)      # MOTOR

COHETE.add_nose(length=0.330, kind="ogive", position=0)

COHETE.add_trapezoidal_fins(
            n=4,
            root_chord=0.20,
            tip_chord=0.07,
            span=0.20,
            position=1.53
        )

main = COHETE.add_parachute(
    name="Main",
    cd_s=5,      # Coeficiente de Drag * Superficie
    trigger="apogee",
)

print(env.elevation)
##################### FUNCIÓN DEL Apogeo y las coordenadas de impacto ##############################
def Apogeo_Impacto(elevacion, direccion): # con el formato [(0 - 90º), (0 - 360º)
    
    flight = Flight(
    environment=env,
    rocket=COHETE,
    rail_length=6,
    inclination=elevacion,
    heading=direccion
    )

    distancia_impact = sqrt(flight.x_impact ** 2 + flight.y_impact ** 2)
    return float(flight.apogee), float(distancia_impact)

################### GRÁFICA #####################
fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

N_elevaciones = 5
N_direcciones = 6
elevaciones = np.linspace(70, 90, N_elevaciones)
direcciones = np.linspace(0, 360, N_direcciones)
X, Y = np.meshgrid(elevaciones, direcciones)

apogeos = np.zeros((N_direcciones, N_elevaciones))
distancias = np.zeros((N_direcciones, N_elevaciones))


for e_c, elevacion in enumerate(elevaciones):
    for d_c, direccion in enumerate(direcciones):
        apogee, distance = Apogeo_Impacto(elevacion, direccion)
        apogeos[int(d_c), int(e_c)] = apogee - env.elevation
        distancias[int(d_c), int(e_c)] = distance
        print(f'Elevacion = {round(elevacion)}, Direccion = {round(direccion)}, Apogeo = {round(apogee - env.elevation)}, Distancia al impacto = {round(distance)}')
Z = apogeos

norm = plt.Normalize(distancias.min(), distancias.max())
colors = cm.viridis(norm(distancias))  # Cambia 'viridis' por cualquier cmap


surf = ax.plot_surface(X, Y, Z, facecolors= colors, linewidth=0, antialiased=False, shade=False)

m = cm.ScalarMappable(cmap=cm.viridis, norm=norm)
m.set_array([])
fig.colorbar(m, ax=ax, label='Distancia al impacto (m)')

ax.set_xlabel('Elevacion (º)')
ax.set_ylabel('Dirección (º)')
ax.set_zlabel('Apogeo (m)')


plt.show()