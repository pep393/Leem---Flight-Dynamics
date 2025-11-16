from rocketpy import Environment, SolidMotor, Rocket, Flight, StochasticRocket, StochasticSolidMotor, MonteCarlo, StochasticEnvironment, StochasticFlight, StochasticNoseCone, StochasticTrapezoidalFins, Function
import numpy as np
import matplotlib.pyplot as plt


LONGITUD = 1.74                 #Longitud [m]
RADIO = 0.065                   # Radio [m]
chamber_height = 0.70



######## ENVIRONMENT ##########
env = Environment()
stochastic_environment = StochasticEnvironment(
    environment=env
)
##############################




####################### MOTOR #####################################
MOTOR = SolidMotor(
    thrust_source=r"RECURSOS\FR_Vulkan.eng",
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
    nozzle_position=0,  
    throat_radius=18 / 2000,                   
    coordinate_system_orientation="nozzle_to_combustion_chamber",
)

stochastic_motor = StochasticSolidMotor(
    solid_motor=MOTOR,
    total_impulse=50)          
####################################################################




#################################  COHETE #######################
ROCKET = Rocket(
    radius=RADIO,
    mass=5.144,     # Masa sin motor [kg]  
    inertia=(0.5, 0.5, 0.005),
    power_off_drag=r"RECURSOS/CD_new.csv",        
    power_on_drag=r"RECURSOS/CD_new.csv",
    center_of_mass_without_motor= 0.716,
    coordinate_system_orientation= "nose_to_tail")
ROCKET.add_motor(MOTOR, position=LONGITUD)

nose_cone = ROCKET.add_nose(                # Añadir Nosecone 
    length=0.33, kind="ogive", position=0
)

fin_set = ROCKET.add_trapezoidal_fins(  # Añadir aletas
    n=4,
    root_chord=0.20,
    tip_chord=0.07,
    span=0.20,
    position=1.53
)


stochastic_rocket = StochasticRocket(       # Añadir cohete estocástico
    rocket=ROCKET
)
stochastic_nosecone = StochasticNoseCone(   # Añadir nariz cónica estocástica
    nosecone = nose_cone
)
stochastic_fins = StochasticTrapezoidalFins(    # Añadir aletas estocásticas
    trapezoidal_fins=fin_set
)
stochastic_rocket.add_motor(stochastic_motor)   
stochastic_rocket.add_nose(stochastic_nosecone)     # Añadir elementos estocásticos
stochastic_rocket.add_trapezoidal_fins(stochastic_fins)
###############################################################################




###################### FLIGHT #####################3
flight = Flight(
    environment=env,
    rocket=ROCKET,
    rail_length=9,
    inclination=84.0
)
stochastic_flight = StochasticFlight(
    flight=flight
)
###################################################




########## MONTE CARLO #########
test_dispersion = MonteCarlo(       # Establecemos la clase Monte Carlo
    filename= "pruebaMonteCarlo",
    environment =stochastic_environment,
    rocket = stochastic_rocket,
    flight=stochastic_flight
    # export_list=["apogee"]
)
test_dispersion.simulate(   # Se simula con 10 variaciones
    number_of_simulations = 1000,
    append=True
)


test_dispersion.plots.all()
