### CONFIGURACION DE LEEMUR COHETE DE PRUEBA 1KM    

from rocketpy import Environment, GenericMotor, Rocket, Flight
import numpy as np
import matplotlib.pyplot as plt


chamber_height = 0.35          # Altura de la camara (sin tobera, sacada de otra simulación)
RADIO_ASPID = 0.065      
LONGITUD_ASPID = 1.83  # Dimensiones cohete


env = Environment()         # Entorno según la ISA


root_chords = np.linspace(0.15, 0.25, num=5)
tip_chords = np.linspace(0.05, 0.15, num=5)
spans = np.linspace(0.15, 0.3, num=5)
for span in spans:
    for root_chord in root_chords:
        for tip_chord in tip_chords:


            motor_teorico = GenericMotor(
            thrust_source = "FR_Vulkan.eng",
            burn_time=None,             # El rocketpy me obliga a definir esto pero lo pongo en None porque ya tenemos 

            chamber_height=chamber_height,
            chamber_radius=RADIO_ASPID,

            chamber_position=-0.175,

            nozzle_radius=0.065,                # Anchura de tobera ASPID

            propellant_initial_mass=2.020,       # Masa total del combustible. En este caso es 0.1 para tener una masa seca real porque no se puede quitar(7.95, sacado de otra simulacion de ASPID)
            dry_mass=6.000,                      # Masa del motor en seco

            dry_inertia=(1.206, 1.205, 0.023) ,     # Las inercias están mal pero para este analisis no importan
            coordinate_system_orientation="combustion_chamber_to_nozzle"
            )

            ASPID = Rocket(
                radius=RADIO_ASPID,
                mass=3.941,                         # Masa sin motor
                inertia=(0.5, 0.5, 0.005),          # Inercias siguen mal que mieo
                power_off_drag="CD_new.csv",        
                power_on_drag="CD_new.csv",
                center_of_mass_without_motor= 0.982,     # 0.89 cuidado
                coordinate_system_orientation= "nose_to_tail")
            ASPID.add_motor(motor_teorico, position=LONGITUD_ASPID)


            nose_cone = ASPID.add_nose(
                length=0.35, kind="ogive", position=0
            )

            fin_set = ASPID.add_trapezoidal_fins(   # Aletas ASPID
                n=4,
                root_chord=root_chord,
                tip_chord=tip_chord,
                span=span,
                position=1.62
            )

            test_flight = Flight(
                environment=env,
                rocket=ASPID,
                rail_length=12,
                inclination=84.0
            )
            print(f"Estabilidad Mínima {round(test_flight.min_stability_margin, 3)}, Root: {round(root_chord, 3)}, Tip: {round(tip_chord,3)}, Span: {round(span,3)}")