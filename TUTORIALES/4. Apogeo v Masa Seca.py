from rocketpy import Environment, GenericMotor, Rocket, Flight
import numpy as np
import matplotlib.pyplot as plt


chamber_height = 0.7          # Altura de la camara (sin tobera, sacada de otra simulación)
RADIO_ASPID = 110 / 2000      
LONGITUD_ASPID = 2830 / 1000  # Dimensiones cohete
SEPAR_TOBERA = 0.04765        

impulsos_totales = np.linspace(15000, 22000, num=2) # De 15-22 kNs
masas = np.linspace(12, 25, num=2)                  # De 12 a 25 kg

env = Environment()         # Entorno según la ISA
apogeos_auxiliar = []
apogeos = []


for impulso in impulsos_totales:
    for masa in masas:

        motor_teorico = GenericMotor(
        thrust_source = r"RECURSOS/motorA_WCS.eng",
        reshape_thrust_curve=[6, impulso],    # Escala el thrust para que de un impulso total quemando durante x tiempo
        burn_time=None,             # El rocketpy me obliga a definir esto pero lo pongo en None porque ya tenemos 

        chamber_height=chamber_height,
        chamber_radius=RADIO_ASPID,
        
        chamber_position=0.35,    # Posicion de coordenadas del motor sin tobera

        nozzle_radius=30 / 1000,                # Anchura de tobera ASPID

        propellant_initial_mass=4,       # Masa total del combustible. En este caso es 0.1 para tener una masa seca real porque no se puede quitar(7.95, sacado de otra simulacion de ASPID)
        dry_mass=masa,                      # Masa del motor en seco

        dry_inertia=(1.206, 1.205, 0.023) ,     # Las inercias están mal pero para este analisis no importan
        coordinate_system_orientation="combustion_chamber_to_nozzle"
        )

        ASPID = Rocket(
            radius=RADIO_ASPID,
            mass=12,                         # Masa sin motor
            inertia=(0.5, 0.5, 0.005),          # Inercias siguen mal que mieo
            power_off_drag=r"RECURSOS/CD_new.csv",        
            power_on_drag=r"RECURSOS/CD_new.csv",
            center_of_mass_without_motor= 0.565,     # Esto xd, creo que está bien pero habría que contrastar
            coordinate_system_orientation= "nose_to_tail")
        ASPID.add_motor(motor_teorico, position=LONGITUD_ASPID - SEPAR_TOBERA - (chamber_height / 2))


        nose_cone = ASPID.add_nose(
            length=0.5, kind="ogive", position=-0.5
        )

        fin_set = ASPID.add_trapezoidal_fins(   # Aletas ASPID
            n=4,
            root_chord=0.2,
            tip_chord=0.1,
            span=0.16,
            position=1.547+0.5,
            sweep_angle= 0
        )

        test_flight = Flight(
            environment=env,
            rocket=ASPID,
            rail_length=12,
            inclination=84.0
        )
        
        apogeos_auxiliar.append(test_flight.apogee)
        
    apogeos.append(apogeos_auxiliar.copy())
    apogeos_auxiliar.clear()                    # Movidas con listas para almacenar datos y tal...


### PLOT APOGEO ###
for i in range(len(impulsos_totales)):
    plt.plot(masas, apogeos[i - 1], label=f"{impulsos_totales[i - 1]} kNs")
plt.xlabel('Masa Seca [kg]')
plt.ylabel('Apogeo [m]')
plt.title('Apogeo vs Masa Seca',fontweight='bold')
plt.legend()
plt.grid(True, linestyle='--', linewidth=0.5)
plt.minorticks_on()
plt.grid(which='minor', linestyle=':', linewidth=0.5)
plt.show()

