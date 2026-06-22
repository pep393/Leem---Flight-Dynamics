from rocketpy import Environment, SolidMotor, Rocket, Flight, AirBrakes
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import numpy as np
from datetime import datetime

chamber_height = 0.923
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.8

TARGET_APOGEE = 3000  # Apogeo objetivo en metros (ajusta según tu competencia)

env = Environment()

airbrakes_deployment_history = []
apogee_prediction_history = []

aspid_engine = SolidMotor(
    thrust_source=r"RECURSOS\ASPIDTHRUST.csv",
    dry_mass=7.268,
    dry_inertia=(1.206, 1.205, 0.023),
    nozzle_radius=0.065,
    grain_number=4,
    grain_density=1730,
    grain_outer_radius=49 / 1000,
    grain_initial_inner_radius=32.5 / 2000,
    grain_initial_height=170 / 1000,
    grain_separation=15 / 1000,
    grains_center_of_mass_position=0.433,
    center_of_dry_mass_position=0.481,
    nozzle_position=chamber_height,
    throat_radius=12.5 / 1000,
    coordinate_system_orientation="combustion_chamber_to_nozzle",
)

ASPID = Rocket(
    radius=RADIO_ASPID,
    mass=15.32,   # Estaba en 15.32  
    inertia=(3.613, 3.613, 0.041),
    power_off_drag=r"RECURSOS\datos_convertidos.csv",
    power_on_drag=r"RECURSOS\CD_ON_ASPID.csv",
    center_of_mass_without_motor=1.7,
    coordinate_system_orientation="nose_to_tail"
)

ASPID.add_motor(aspid_engine, position=LONGITUD_ASPID - chamber_height)
ASPID.add_nose(length=0.40, kind="ogive", position=0)
ASPID.add_trapezoidal_fins(
    n=4,
    root_chord=0.244,
    tip_chord=0.072,
    span=0.203,
    position=LONGITUD_ASPID - 0.244 - 0.05
)

ASPID.add_parachute(
    "drogue",
    cd_s=0.3472,  
    trigger="apogee",
    radius=0.42,
    lag=1,
)

ASPID.add_parachute(
    "main",
    cd_s=6.171,
    trigger=300,
    radius=1.78,
    lag=1,
)


def predict_apogee_simple(altitude, vz, deployment_level, env, rocket):
    """
    Predicción simplificada del apogeo usando integración numérica.
    """
    h = altitude
    v = vz
    dt = 0.01  # paso de tiempo pequeño
    mass = rocket.total_mass(0)  # aproximación de masa constante post-burnout
    
    # Área de referencia
    area = np.pi * rocket.radius ** 2
    
    # Coeficiente de arrastre interpolado según deployment_level
    # Asumimos que el drag aumenta linealmente con la extensión
    cd_base = 0.5  # Cd sin aerofrenos (ajustar según tus datos)
    cd_max = 1.5   # Cd con aerofrenos completamente desplegados (ajustar)
    cd = cd_base + (cd_max - cd_base) * deployment_level
    
    max_iterations = 10000
    iteration = 0
    
    while v > 0 and iteration < max_iterations:
        # Densidad del aire a la altitud actual
        rho = env.density(h)
        
        # Fuerza de arrastre
        drag_force = 0.5 * rho * v**2 * area * cd
        
        # Aceleración (gravedad + arrastre)
        g = 9.81
        acceleration = -g - (drag_force / mass)
        
        # Integración (Euler)
        v += acceleration * dt
        h += v * dt
        
        iteration += 1
    
    return h


def mpc_cost_function(u, *args):
    """
    Función de costo para el MPC.
    u: vector de control (deployment_levels) en el horizonte de predicción
    """
    altitude, vz, target_apogee, env, rocket, horizon = args
    
    # Simulamos la trayectoria con los controles propuestos
    h = altitude
    v = vz
    dt = 0.1
    
    for deployment in u:
        # Limitar deployment entre 0 y 1
        deployment = np.clip(deployment, 0, 1)
        
        # Simular un paso con este deployment
        for _ in range(int(0.5 / dt)):  # Cada control dura 0.5 segundos
            if v <= 0:
                break
            
            mass = rocket.total_mass(0)
            area = np.pi * rocket.radius ** 2
            rho = env.density(h)
            
            cd_base = 0.5
            cd_max = 1.5
            cd = cd_base + (cd_max - cd_base) * deployment
            
            drag_force = 0.5 * rho * v**2 * area * cd
            g = 9.81
            acceleration = -g - (drag_force / mass)
            
            v += acceleration * dt
            h += v * dt
            
            if v <= 0:
                break
    
    # Continuar hasta apogeo sin control
    while v > 0:
        mass = rocket.total_mass(0)
        area = np.pi * rocket.radius ** 2
        rho = env.density(h)
        cd = 0.5
        
        drag_force = 0.5 * rho * v**2 * area * cd
        g = 9.81
        acceleration = -g - (drag_force / mass)
        
        v += acceleration * dt
        h += v * dt
    
    apogee = h
    
    # Costo: diferencia cuadrática con el apogeo objetivo
    # + penalización por cambios bruscos en el control
    cost = (apogee - target_apogee)**2
    
    # Penalización por cambios bruscos (suavidad del control)
    if len(u) > 1:
        control_smoothness_penalty = 100 * np.sum(np.diff(u)**2)
        cost += control_smoothness_penalty
    
    return cost


def controller_function(time, sampling_rate, state, state_history, observed_variables, aerofreno):
    """
    Controlador MPC para los aerofrenos.
    """
    global airbrakes_deployment_history, apogee_prediction_history
    
    # No desplegar durante el burnout del motor
    if time < aspid_engine.burn_out_time:
        aerofreno.deployment_level = 0
        airbrakes_deployment_history.append((time, aerofreno.deployment_level))
        return aerofreno.deployment_level

    
    
    # # Extraer estado actual
    altitude_ASL = state[2]
    vx, vy, vz = state[3], state[4], state[5]
    
    # # Calcular velocidad relativa al viento
    wind_x = env.wind_velocity_x(altitude_ASL)
    wind_y = env.wind_velocity_y(altitude_ASL)
    free_stream_speed = ((wind_x - vx)**2 + (wind_y - vy)**2 + vz**2)**0.5
    mach_number = free_stream_speed / env.speed_of_sound(altitude_ASL)
    
    # if mach_number > 0.60:
    #     aerofreno.deployment_level = 0
    #     airbrakes_deployment_history.append((time, aerofreno.deployment_level))
    #     return aerofreno.deployment_level
    
    # No desplegar cuando la velocidad vertical es negativa (ya descendiendo)
    if vz < 0:
        aerofreno.deployment_level = 0
        airbrakes_deployment_history.append((time, aerofreno.deployment_level))
        return aerofreno.deployment_level
    
    if altitude_ASL < 1500:
        aerofreno.deployment_level = 0
        airbrakes_deployment_history.append((time, aerofreno.deployment_level))
        return aerofreno.deployment_level
    
    ##################### MPC CONTROLLER #####################
    
    # Horizonte de predicción (número de pasos de control)
    horizon = 5
    
    # Optimización: encontrar la secuencia óptima de deployment_levels
    # Initial guess: mantener cerrado
    u0 = np.zeros(horizon)
    
    # Límites: deployment entre 0 y 1
    bounds = [(0, 1) for _ in range(horizon)]
    
    # Argumentos para la función de costo
    args = (altitude_ASL, vz, TARGET_APOGEE, env, ASPID, horizon)
    
    # Optimización
    result = minimize(
        mpc_cost_function,
        u0,
        args=args,
        method='SLSQP',
        bounds=bounds,
        options={'maxiter': 50, 'ftol': 1e-4}
    )
    
    # Aplicar solo el primer control de la secuencia óptima (principio del MPC)
    optimal_deployment = np.clip(result.x[0], 0, 1)
    aerofreno.deployment_level = optimal_deployment
    
    # Guardar historial
    airbrakes_deployment_history.append((time, aerofreno.deployment_level))
    
    # Predicción del apogeo con el control actual (para análisis)
    predicted_apogee = predict_apogee_simple(altitude_ASL, vz, optimal_deployment, env, ASPID)
    apogee_prediction_history.append((time, predicted_apogee))
    return aerofreno.deployment_level
    
    #########################################################


aerofreno = ASPID.add_air_brakes(
    drag_coefficient_curve="airbrakes.csv",
    override_rocket_drag = True,
    controller_function=controller_function,
    sampling_rate=100,  # 100 Hz
      
)

# Simulación del vuelo
test_flight = Flight(
    environment=env,
    rocket=ASPID,
    rail_length=12,
    inclination=84.0,
    
)

print(test_flight.apogee)
test_flight.z()


# from rocketpy.simulation import FlightDataExporter

# exporter = FlightDataExporter(test_flight)
# exporter.export_data(
#     "altitudevtime.csv",
#     "altitude"
# )
