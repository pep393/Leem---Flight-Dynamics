from rocketpy import SolidMotor, StochasticSolidMotor
import numpy as np

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
    total_impulse=80)          # Hay un impulso total de 2547 teóricos

valores_impulso_total = []
for i in range(5000):
    motor_estocastico = stochastic_motor.create_object()
    valores_impulso_total.append(round(motor_estocastico.total_impulse))

    print(f"Total Impulse: {round(motor_estocastico.total_impulse, 1)} | Mean Value: {round(np.mean(valores_impulso_total), 1)} | Standard Deviation: {round(np.std(valores_impulso_total), 1)} | Iteration: {i}")
