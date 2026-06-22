import numpy as np
from scipy.optimize import minimize
from rocketpy import Environment, SolidMotor, Rocket, Flight

# --- CONFIGURACIÓN DE LA BÚSQUEDA ---
TARGET_V = 313.0  # m/s
TARGET_G = 28.0   # Gs
TARGET_A = TARGET_G * 9.80665  # m/s^2
TARGET_TIME = 2 # s 

# --- DEFINICIÓN DEL ENTORNO ---
env = Environment()

def evaluar_configuracion(params, verbose=False):
    """
    Función objetivo. Recibe [burn_time, total_impulse] y devuelve el error total.
    Si la simulación falla o es físicamente inviable, devuelve un castigo alto.
    """
    bt, ti = params[0], params[1]
    
    # Castigo severo si el optimizador intenta probar tiempos menores al target
    # o impulsos negativos/absurdos.
    if bt < TARGET_TIME or ti < 100 or bt > 20:
        return 1e6 

    try:
        # 1. MOTOR
        meteor_EUROC = SolidMotor(
            thrust=ti
            burn_time=bt,
            dry_mass=7.95,
            dry_inertia=(1.206, 1.205, 0.023),
            nozzle_radius=30 / 1000,
            grain_number=4,
            grain_density=1841,
            grain_outer_radius=49 / 1000,
            grain_initial_inner_radius=32.5 / 2000,
            grain_initial_height=170 / 1000,
            grain_separation=15 / 1000,
            grains_center_of_mass_position= 451.75 / 1000,
            center_of_dry_mass_position= 502 / 1000,
            nozzle_position=0,
            throat_radius=12.5 / 1000,
            coordinate_system_orientation="nozzle_to_combustion_chamber",
        )

        # 2. COHETE
        PosCM_sinMotor = 1.31
        SeparTobera = 0.04765
        longURSA = 2.54

        URSA = Rocket(
            radius=158 / 2000,
            mass=12.148,
            inertia=(5.469, 5.469, 0.059),
            power_off_drag=r"RECURSOS/CD_OFF_ASPID.csv",
            power_on_drag=r"RECURSOS/CD_ON_ASPID.csv",
            center_of_mass_without_motor= 1.31,
            coordinate_system_orientation= "tail_to_nose"
        )
        
        URSA.add_motor(meteor_EUROC, position=-PosCM_sinMotor - SeparTobera)
        URSA.add_nose(length=0.6, kind="ogive", position=longURSA - PosCM_sinMotor)
        URSA.add_trapezoidal_fins(
            n=4, root_chord=0.2, tip_chord=0.01, span=0.16,
            position=-PosCM_sinMotor + 0.2, sweep_angle=0
        )

        # 3. VUELO
        test_flight = Flight(
            environment=env,
            rocket=URSA,
            rail_length=12,
            inclination=84.0,
            heading=133,
            terminate_on_apogee=True 
        )

        if test_flight.t_final < TARGET_TIME:
            return 1e5 # Castigo si el cohete no llega volando a ese segundo

        # 4. EVALUACIÓN
        v = test_flight.speed(TARGET_TIME)
        ax = test_flight.ax(TARGET_TIME)
        ay = test_flight.ay(TARGET_TIME)
        az = test_flight.az(TARGET_TIME)
        a = np.sqrt(ax**2 + ay**2 + az**2)
        
        current_g = a / 9.80665

        error_v = (v - TARGET_V) / TARGET_V
        error_a = (a - TARGET_A) / TARGET_A
        total_error = np.sqrt(error_v**2 + error_a**2)

        if verbose:
            str_motor = f"{bt:.2f}s, {ti:.0f}Ns"
            str_vel = f"{v:.1f} (Dif: {v - TARGET_V:+.1f})"
            str_g = f"{current_g:.1f} (Dif: {current_g - TARGET_G:+.1f})"
            print(f"[{str_motor:<18}] | {str_vel:<25} | {str_g:<25} | {total_error:.4f}")

        return total_error

    except Exception as e:
        return 1e6 # Castigo alto si la simulación crashea


# ==========================================
# FASE 1: BÚSQUEDA GRUESA (GRID SEARCH)
# ==========================================
print(f"--- FASE 1: Búsqueda Gruesa (Grid Search) en t = {TARGET_TIME}s ---")
burn_times = np.linspace(TARGET_TIME, 6.0, 15) 
total_impulses = np.linspace(7000, 15000, 15) 

best_grid_error = float('inf')
best_grid_guess = None

for bt in burn_times:
    if bt < TARGET_TIME: continue
    for ti in total_impulses:
        # Silenciamos el verbose para no inundar la terminal con cientos de líneas
        err = evaluar_configuracion([bt, ti], verbose=True) 
        if err < best_grid_error:
            best_grid_error = err
            best_grid_guess = [bt, ti]

print(f"Mejor punto de partida encontrado: Tb = {best_grid_guess[0]:.2f}s, Itot = {best_grid_guess[1]:.0f}Ns (Error: {best_grid_error:.4f})")
print("\n--- FASE 2: Sintonía Fina (Nelder-Mead) ---")
print(f"{'MOTOR (Tb, Itot)':<20} | {'VELOCIDAD (m/s)':<25} | {'FUERZAS G':<25} | {'ERROR'}")
print("-" * 85)


# ==========================================
# FASE 2: OPTIMIZACIÓN LOCAL (NELDER-MEAD)
# ==========================================
# Definimos un wrapper para activar el verbose solo durante el descenso local
def objective_wrapper(x):
    return evaluar_configuracion(x, verbose=True)

# Ejecutamos el optimizador Nelder-Mead partiendo del mejor resultado del Grid
resultado_optimo = minimize(
    objective_wrapper, 
    best_grid_guess, 
    method='Nelder-Mead',
    options={'xatol': 1e-4, 'fatol': 1e-4, 'maxiter': 100} # Tolerancias para los decimales
)

# ==========================================
# RESULTADOS
# ==========================================
print("\n" + "=" * 85)
if resultado_optimo.success:
    opt_bt, opt_ti = resultado_optimo.x
    print(f"--- CONVERGENCIA ALCANZADA ---")
    print(f" -> Tiempo del suceso fijado: t = {TARGET_TIME} s")
    print(f" -> Tiempo de quema del motor exacto: {opt_bt:.4f} s")
    print(f" -> Impulso Total del motor exacto:  {opt_ti:.4f} Ns")
    print(f" -> Error mínimo residual: {resultado_optimo.fun:.6f}")
    print(f" -> Iteraciones necesarias: {resultado_optimo.nit}")
else:
    print("El optimizador terminó, pero reporta problemas de convergencia:")
    print(resultado_optimo.message)
    opt_bt, opt_ti = resultado_optimo.x
    print(f"Mejor estimación obtenida: Tb = {opt_bt:.4f}s, Itot = {opt_ti:.4f} Ns")