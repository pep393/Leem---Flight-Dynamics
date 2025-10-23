# Codigo provisional en proceso para sacar una prueba de las gráficas extrañas



from rocketpy import Environment, SolidMotor, Rocket, Flight
import numpy as np
import matplotlib.pyplot as plt

LONGITUD= 1.74

impulsos_totales = np.linspace(15000, 22000, num=3) # De 15-22 kNs
masas = np.linspace(12, 25, num=6)                  # De 12 a 25 kg

env = Environment()         # Entorno según la ISA
apogeos_auxiliar = []
apogeos = []


            # Por ahora cambiar estos datos por los del rail
for impulso in impulsos_totales:
    for masa in masas:

        env = Environment(

        )
    

        MOTOR = SolidMotor(
            thrust_source=1000,
            burn_time=3,
            dry_mass=5.00,                              # CHECK
            dry_inertia=(3.081, 3.081, 0.02569),
            nozzle_radius=30 / 1000,                        
            grain_number=1,                             # CHECK
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
            mass=5.144,
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


        test_flight = Flight(
            environment=env,
            rocket=COHETE,
            rail_length=6,
            inclination=84.0,
            heading=0
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

