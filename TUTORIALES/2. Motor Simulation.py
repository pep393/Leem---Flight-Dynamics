from rocketpy import SolidMotor, GenericMotor
####################### SOLID MOTOR #######################3

MOTOR = SolidMotor(
    thrust_source="RECURSOS\FR_Vulkan.eng",
    reshape_thrust_curve=[4, 6000],      # Time  / Total Impulse
    dry_mass=5.00,                   
    dry_inertia=(1.206, 1.205, 0.023),
    
    nozzle_radius=30 / 1000,                    
    grain_number=2,
    grain_density=1841,                         
    grain_outer_radius=91 / 2000,               
    grain_initial_inner_radius=36 / 2000,     
    grain_initial_height=200 / 1000,           
    grain_separation=15 / 1000,                 
    grains_center_of_mass_position= 451.75 / 1000,
    center_of_dry_mass_position= 502 / 1000,   

    coordinate_system_orientation="nozzle_to_combustion_chamber",
)

MOTOR.all_info()


################# GENERIC MOTOR ##################
"""
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


motor_teorico.all_info()
"""