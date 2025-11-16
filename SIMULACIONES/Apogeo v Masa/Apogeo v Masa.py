from rocketpy import Environment, GenericMotor, Rocket, Flight
import numpy as np
import matplotlib.pyplot as plt


chamber_height = 0.7          # Altura de la camara (sin tobera, sacada de otra simulación)
RADIO_ASPID = 0.065      
LONGITUD_ASPID = 2830 / 1000  # Dimensiones cohete
SEPAR_TOBERA = 0.04765        

impulsos_totales = np.linspace(8750, 11500, num=12) 
masas = np.linspace(5, 10, num=10)                  

env = Environment()         # Entorno según la ISA
apogeos_auxiliar = []
apogeos = []

max_g_auxiliar = []
max_g = []

max_mach_auxiliar = []
max_mach = []
                            

for impulso in impulsos_totales:
    for masa in masas:

        motor_teorico = GenericMotor(
        thrust_source ="RECURSOS/motorA_WCS.eng",
        reshape_thrust_curve=[4, impulso],    # Escala el thrust para que de un impulso total quemando durante x tiempo
        burn_time=None,             # El rocketpy me obliga a definir esto pero lo pongo en None porque ya tenemos 

        chamber_height=chamber_height,
        chamber_radius=RADIO_ASPID,
        
        chamber_position=0.35,    # Posicion de coordenadas del motor sin tobera

        nozzle_radius=30 / 1000,                # Anchura de tobera ASPID

        propellant_initial_mass=8.08,
        dry_mass=masa,                      # Masa del motor en seco

        dry_inertia=(1.206, 1.205, 0.023) ,     # Las inercias están mal pero para este analisis no importan
        coordinate_system_orientation="combustion_chamber_to_nozzle"
        )


        ASPID = Rocket(
            radius=RADIO_ASPID,
            mass=12.0,                         # Masa sin motor
            inertia=(0.5, 0.5, 0.005),          # Inercias siguen mal que mieo
            power_off_drag="RECURSOS/CD_new.csv",        
            power_on_drag="RECURSOS/CD_new.csv",
            center_of_mass_without_motor= 0.812, 
            coordinate_system_orientation= "nose_to_tail")
        ASPID.add_motor(motor_teorico, position=LONGITUD_ASPID)

        nose_cone = ASPID.add_nose(
            length=0.33, kind="ogive", position=0
        )

        fin_set = ASPID.add_trapezoidal_fins(   # Aletas ASPID
            n=4,
            root_chord=0.2,
            tip_chord=0.1,
            span=0.2,
            position=LONGITUD_ASPID - 0.2,
        )

        test_flight = Flight(
            environment=env,
            rocket=ASPID,
            rail_length=12,
            inclination=84.0
        )
        apogeos_auxiliar.append(test_flight.apogee)
        max_g_auxiliar.append(test_flight.max_acceleration/9.81)
        max_mach_auxiliar.append(test_flight.max_mach_number)
 
    apogeos.append(apogeos_auxiliar.copy())
    apogeos_auxiliar.clear()                  
    max_g.append(max_g_auxiliar.copy())
    max_g_auxiliar.clear()
    max_mach.append(max_mach_auxiliar.copy())
    max_mach_auxiliar.clear()



### PLOT APOGEO ###
for i in range(len(impulsos_totales)):
    plt.plot(masas, apogeos[i - 1], label=f"{impulsos_totales[i - 1]} Ns")
plt.xlabel('Masa Seca Motor[kg]')
plt.ylabel('Apogeo [m]')
plt.title('Apogeo vs Masa Seca del Motor',fontweight='bold')
plt.legend()
plt.grid(True, linestyle='--', linewidth=0.5)
plt.minorticks_on()
plt.grid(which='minor', linestyle=':', linewidth=0.5)
plt.show()

### PLOT MAX G ###
for i in range(len(impulsos_totales)):
    plt.plot(masas, max_g[i - 1], label=f"{impulsos_totales[i - 1]} Ns")
plt.xlabel('Masa Seca Motor[kg]')
plt.ylabel('Max G')
plt.title('Max G vs Masa Seca Motor',fontweight='bold')
plt.legend()
plt.grid(True, linestyle='--', linewidth=0.5)
plt.minorticks_on()
plt.grid(which='minor', linestyle=':', linewidth=0.5)
plt.show()

### PLOT MAX MACH ###
for i in range(len(impulsos_totales)):
    plt.plot(masas, max_mach[i - 1], label=f"{impulsos_totales[i - 1]} Ns")
plt.xlabel('Masa Seca Motor[kg]')
plt.ylabel('Max Mach')
plt.title('Max Mach vs Masa Seca Motor',fontweight='bold')
plt.legend()
plt.grid(True, linestyle='--', linewidth=0.5)
plt.minorticks_on()
plt.grid(which='minor', linestyle=':', linewidth=0.5)
plt.show()

