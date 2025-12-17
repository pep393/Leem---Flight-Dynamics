from rocketpy import Environment, SolidMotor, Rocket, Flight, AirBrakes
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import numpy as np
from numba import njit

LONGITUD = 2.83
TARGET_APOGEE = 2800  # Apogeo objetivo en metros (ajusta según tu competencia)

env = Environment()

airbrakes_deployment_history = []
apogee_prediction_history = []

MOTOR = SolidMotor(
    thrust_source=r"RECURSOS/Predicted_thrust.csv",
    dry_mass=5.00,
    dry_inertia=(3.081, 3.081, 0.02569),
    nozzle_radius=30 / 1000,
    grain_number=4,
    grain_density=1841,
    grain_outer_radius=91 / 2000,
    grain_initial_inner_radius=36 / 2000,
    grain_initial_height=200 / 1000,
    grain_separation=15 / 1000,
    grains_center_of_mass_position=0.185,
    center_of_dry_mass_position=0.185,
    nozzle_position=0,
    throat_radius=18 / 2000,
    coordinate_system_orientation="nozzle_to_combustion_chamber",
)

COHETE = Rocket(
    radius=0.065,
    mass=13,
    inertia=(0.5, 0.5, 0.005),
    power_off_drag=r"RECURSOS/CD_OFF_ASPID.csv",
    power_on_drag=r"RECURSOS/CD_ON_ASPID.csv",
    center_of_mass_without_motor=0.716,
    coordinate_system_orientation="nose_to_tail"
)

COHETE.add_motor(MOTOR, position=LONGITUD)
COHETE.add_nose(length=0.330, kind="ogive", position=0)
COHETE.add_trapezoidal_fins(
    n=4,
    root_chord=0.20,
    tip_chord=0.07,
    span=0.20,
    position=1.53
)

# Pre-calcular tabla de densidades para usar con Numba
H_TABLE = np.linspace(0, 5000, 100)
RHO_TABLE = np.array([env.density(h) for h in H_TABLE])


@njit(cache=True)
def simulate_trajectory_numba(altitude, vz, u_controls, mass, radius, 
                               rho_table, h_table, target_apogee):
    """
    Simulación de trayectoria optimizada con Numba JIT compilation.
    Esta es la ÚNICA optimización aplicada - todo lo demás igual que el código original.
    
    Numba compila esta función a código máquina nativo, haciéndola ~50-100x más rápida.
    """
    h = altitude
    v = vz
    dt = 0.1
    area = np.pi * radius ** 2
    cd_base = 0.42
    cd_max = 0.55
    
    # Fase 1: Aplicar controles propuestos
    for deployment in u_controls:
        # Limitar deployment entre 0 y 1
        deployment = min(max(deployment, 0.0), 1.0)
        
        # Cada control dura 0.5 segundos
        for _ in range(5):  # 5 pasos de 0.1s = 0.5s
            if v <= 0:
                break
            
            # Interpolación de densidad (más rápido que llamar env.density)
            rho = np.interp(h, h_table, rho_table)
            
            # Modelo de arrastre
            cd = cd_base + (cd_max - cd_base) * deployment
            drag_force = 0.5 * rho * v * v * area * cd
            
            # Aceleración
            g = 9.81
            acceleration = -g - (drag_force / mass)
            
            # Integración de Euler
            v += acceleration * dt
            h += v * dt
            
            if v <= 0:
                break
    
    # Fase 2: Continuar hasta apogeo sin control
    while v > 0:
        rho = np.interp(h, h_table, rho_table)
        drag_force = 0.5 * rho * v * v * area * cd_base
        g = 9.81
        acceleration = -g - (drag_force / mass)
        
        v += acceleration * dt
        h += v * dt
    
    apogee = h
    
    # Calcular costo
    apogee_error = (apogee - target_apogee) ** 2
    
    # Penalización por suavidad
    smoothness = 0.0
    for i in range(len(u_controls) - 1):
        diff = u_controls[i + 1] - u_controls[i]
        smoothness += diff * diff
    
    cost = apogee_error + 100.0 * smoothness
    
    return cost


def mpc_cost_function(u, *args):
    """
    Función de costo para el MPC - Evalúa qué tan buena es una secuencia de controles.
    
    OBJETIVO: Esta función simula hacia el futuro usando una secuencia de controles propuesta
    y devuelve un "costo" (número) que indica qué tan mala es esa secuencia.
    El optimizador intentará MINIMIZAR este costo.
    
    La ÚNICA diferencia con el código original es que llama a la función Numba
    en vez de hacer la simulación en Python puro.
    """
    altitude, vz, target_apogee, env, rocket, horizon = args
    
    # Llamar a la función compilada con Numba
    mass = rocket.total_mass(0)
    radius = rocket.radius
    
    return simulate_trajectory_numba(
        altitude, vz, u, mass, radius,
        RHO_TABLE, H_TABLE, target_apogee
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
        airbrakes_deployment_history.append((time, aerofreno.deployment_level))
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
    if mach_number > 0.6:
        aerofreno.deployment_level = 0
        airbrakes_deployment_history.append((time, aerofreno.deployment_level))
        return aerofreno.deployment_level
    
    ##################### MPC CONTROLLER (CON NUMBA) #####################
    
    # Horizonte de predicción (número de pasos de control)
    horizon = 5
    
    # Optimización: encontrar la secuencia óptima de deployment_levels
    u0 = np.zeros(horizon)
    
    # Límites: deployment entre 0 y 1
    bounds = [(0, 1) for _ in range(horizon)]
    
    # Argumentos para la función de costo
    args = (altitude_ASL, vz, TARGET_APOGEE, env, COHETE, horizon)
    
    # Optimización (igual que antes, pero la función de costo es mucho más rápida)
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

    
    return aerofreno.deployment_level
    ######################################################################


aerofreno = COHETE.add_air_brakes(
    drag_coefficient_curve="airbrakes.csv",
    controller_function=controller_function,
    sampling_rate=100  # 100 Hz
)

print("\n" + "="*60)
print("INICIANDO SIMULACIÓN CON MPC + NUMBA")
print("="*60)
print("Única optimización: Numba JIT compilation")
print("Todo lo demás igual al código original")
print("="*60 + "\n")

# Simulación del vuelo
flight = Flight(
    environment=env,
    rocket=COHETE,
    rail_length=6,
    inclination=84.0,
    heading=0,
    terminate_on_apogee=True,
)

# Resultados
print(f"\n{'='*60}")
print(f"RESULTADOS DE LA SIMULACIÓN")
print(f"{'='*60}")
print(f"Apogeo objetivo: {TARGET_APOGEE} m")
print(f"Apogeo alcanzado: {flight.apogee:.2f} m")
print(f"Error: {abs(flight.apogee - TARGET_APOGEE):.2f} m")
print(f"Velocidad máxima: {flight.max_speed:.2f} m/s")
print(f"{'='*60}\n")

# Ploteo de resultados (igual que el original)
fig, axes = plt.subplots(3, 1, figsize=(12, 10))

# 1. Extensión de aerofrenos vs tiempo
if airbrakes_deployment_history:
    times, deployments = zip(*airbrakes_deployment_history)
    axes[0].plot(times, deployments, 'r-', linewidth=2, label='Extensión Aerofrenos')
    axes[0].axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
    axes[0].set_xlabel('Tiempo (s)')
    axes[0].set_ylabel('Nivel de Extensión (0-1)')
    axes[0].set_title('Control de Aerofrenos')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()
    axes[0].set_ylim([-0.05, 1.05])

# 2. Predicción de apogeo vs tiempo
if apogee_prediction_history:
    pred_times, pred_apogees = zip(*apogee_prediction_history)
    axes[1].plot(pred_times, pred_apogees, 'b-', linewidth=2, label='Apogeo Predicho')
    axes[1].axhline(y=TARGET_APOGEE, color='g', linestyle='--', linewidth=2, label='Objetivo')
    axes[1].axhline(y=flight.apogee, color='orange', linestyle='--', linewidth=2, label='Apogeo Real')
    axes[1].set_xlabel('Tiempo (s)')
    axes[1].set_ylabel('Altitud (m)')
    axes[1].set_title('Predicción de Apogeo durante el Vuelo')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

# 3. Altitud vs tiempo
axes[2].plot(flight.time, flight.z, 'k-', linewidth=2, label='Altitud Real')
axes[2].axhline(y=TARGET_APOGEE, color='g', linestyle='--', linewidth=2, label='Objetivo')
axes[2].set_xlabel('Tiempo (s)')
axes[2].set_ylabel('Altitud (m)')
axes[2].set_title('Trayectoria del Cohete')
axes[2].grid(True, alpha=0.3)
axes[2].legend()

plt.tight_layout()
plt.show()

# Gráficas adicionales de RocketPy
flight.z()
flight.vz()