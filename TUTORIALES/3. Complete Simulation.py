from rocketpy import Environment, GenericMotor, Rocket, Flight

LONGITUD = 1.74

env = Environment()     # ISA

motor_teorico = GenericMotor(
        thrust_source = "RECURSOS\FR_Vulkan.eng",
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
    power_off_drag=r"RECURSOS/CD_new.csv",
    power_on_drag=r"RECURSOS/CD_new.csv",
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

COHETE.draw()




flight = Flight(
    environment=env,
    rocket=COHETE,
    rail_length=9,
    inclination=84.0
)


flight.all_info()
