from rocketpy import Environment, GenericMotor, Rocket, Flight, Function
from math import pi
import numpy as np
import matplotlib.pyplot as plt


LONGITUD = 2.462

env = Environment()

MOTOR = GenericMotor(
    thrust_source="RECURSOS/Predicted_thrust.csv",
    reshape_thrust_curve=[3.4, 7000],
    burn_time=3.4,
    chamber_radius = 0.065,
    chamber_height = 0.7,   
    chamber_position=0.51,
    dry_mass=7.02,
    propellant_initial_mass=7.98,
    dry_inertia=(0.5, 0.5, 0.005),
    nozzle_radius=0.065 / 2,
)



COHETE = Rocket(
    radius=0.065,
    mass=11.7,
    inertia=(3.613, 3.613, 0.041),
    power_off_drag=r"RECURSOS/CD_OFF_ASPID.csv",
    power_on_drag=r"RECURSOS/CD_ON_ASPID.csv",
    center_of_mass_without_motor= 1.1575,
    coordinate_system_orientation= "nose_to_tail"
    )

COHETE.add_motor(MOTOR, position=LONGITUD)      # MOTOR

COHETE.add_nose(length=0.6, kind="ogive", position=0)

COHETE.add_trapezoidal_fins(
            n=4,
            root_chord=0.20,
            tip_chord=0.07,
            span=0.20,
            position=LONGITUD - 0.2
        )

def controller_function(time, sampling_rate, state, state_history, observed_variables, aerofreno):
    """
    Controlador MPC para los aerofrenos.
    TODO es exactamente igual al código original, excepto que usa la simulación con Numba.
    """
    global airbrakes_deployment_history, apogee_prediction_history
    
    # No desplegar durante el burnout del motor
    if time < MOTOR.burn_out_time:
        aerofreno.deployment_level = 0
        return aerofreno.deployment_level
    
    # Extraer estado actual
    altitude_ASL = state[2]
    vx, vy, vz = state[3], state[4], state[5]
    
    # Calcular velocidad relativa al viento
    wind_x = env.wind_velocity_x(altitude_ASL)
    wind_y = env.wind_velocity_y(altitude_ASL)
    free_stream_speed = ((wind_x - vx)**2 + (wind_y - vy)**2 + vz**2)**0.5
    mach_number = free_stream_speed / env.speed_of_sound(altitude_ASL)
    
    # No desplegar a altas velocidades (limitación estructural)
    if mach_number >= 0.8:
        aerofreno.deployment_level = 0
        return aerofreno.deployment_level
    
    aerofreno.deployment_level = 1
    ######################################################################


aerofreno = COHETE.add_air_brakes(
    drag_coefficient_curve="airbrakes.csv",
    controller_function=controller_function,
    sampling_rate=100  # 100 Hz
)

flight = Flight(
    environment=env,
    rocket=COHETE,
    rail_length=6,
    inclination=86.0,
    heading=0
)


print(flight.apogee)