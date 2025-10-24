import matplotlib.pyplot as plt
import numpy as np

from matplotlib import cm
from matplotlib.ticker import LinearLocator

from rocketpy import Environment, GenericMotor, Rocket, Flight


############### DEFINICIÓN DEL COHETE y SIMULACIÓN ##################
LONGITUD = 1.74

env = Environment()     # ISA

motor_teorico = GenericMotor(
        thrust_source = "TUTORIALES ROCKETPY/RECURSOS/FR_Vulkan.eng",
        burn_time=None,                     # El rocketpy me obliga a definir esto pero lo pongo en None porque ya tenemos 

        chamber_height=0.7,
        chamber_radius=0.065,
        
        chamber_position=0.35,              # Posicion de coordenadas del centro del tanque de combustible

        nozzle_radius=30 / 1000,            # Anchura de tobera

        propellant_initial_mass=2.020,      # Masa propelente
        dry_mass=2.5,                       # Masa del motor en seco

        dry_inertia=(1.206, 1.205, 0.023),
        coordinate_system_orientation="combustion_chamber_to_nozzle"
)



COHETE = Rocket(
    radius=0.065,
    mass=5.144,
    inertia=(0.5, 0.5, 0.005),
    power_off_drag="TUTORIALES ROCKETPY/RECURSOS/CD_new.csv",
    power_on_drag="TUTORIALES ROCKETPY/RECURSOS/CD_new.csv",
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
    cd_s=10.0,      # Coeficiente de Drag * Superficie
    trigger=500,
)

drogue = COHETE.add_parachute(
    name="Drogue",
    cd_s=1.0,
    trigger="apogee",
)


##################### FUNCIÓN DEL Apogeo y las coordenadas de impacto ##############################
def Apogeo_Impacto(azimut, direccion): # con el formato [(0 - 90º), (0 - 360º)
    
    flight = Flight(
    environment=env,
    rocket=COHETE,
    rail_length=9,
    inclination=azimut,
    heading=direccion
    )

    distancia_impact = flight.x_impact ** 2 + flight.y_impact ** 2
    return [float(flight.apogee), float(distancia_impact)]
    

    # Para probar la gráfica, defino una función aleatoria que compile más rápido
    # return [30*(90**2 - azimut ** 2) + 200*direccion, 2000*direccion + 10000 - azimut] 


################### GRÁFICA #####################
fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

N = 30
X = np.linspace(70, 90, N)
Y = np.linspace(0, 360, N)
X, Y = np.meshgrid(X, Y)

apogeos = np.eye(N)
impactos = np.eye(N)
impacto_max = 0
apogeo_max = 0

for i in range(N):
    for j in range(N):
        [z, d] = Apogeo_Impacto(X[i, j], Y[i, j])
        apogeos[i, j] = z
        impactos[i, j] = d
        impacto_max = max(d, impacto_max)
        apogeo_max = max(z, apogeo_max)
        print(f'azimut = {X[i, j]}, direccion = {Y[i, j]}, Apogeo = {z}, Distancia al impacto = {d}')

colores = np.array([[(round(float(impactos[i, j]/impacto_max), 5), 1 - round(float(impactos[i, j]/impacto_max), 5), 1 - round(float(impactos[i, j]/impacto_max), 5)) for j in range(N)] for i in range(N)]) # Es un gradiente Azul - Rojo
Z = apogeos 

# Plot the surface.
surf = ax.plot_surface(X, Y, Z, facecolors=colores,
                       linewidth=0, antialiased=False, shade=False)

ax.set_xlabel('Azimut (º)')
ax.set_ylabel('Dirección (º)')
ax.set_zlabel('Apogeo (m)')

# Customize the z axis.
ax.set_zlim(0, apogeo_max)
ax.zaxis.set_major_locator(LinearLocator(10))
# A StrMethodFormatter is used automatically
ax.zaxis.set_major_formatter('{x:.02f}')

# Add a color bar which maps values to colores.


plt.show()