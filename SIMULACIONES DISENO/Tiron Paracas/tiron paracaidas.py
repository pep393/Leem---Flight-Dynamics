# Código ideal, configuración ASPID

from rocketpy import Environment, Rocket, Flight, SolidMotor, utilities, Function
import numpy as np
import rocketpy.utilities as _rpu
from rocketpy.mathutils import Function
import matplotlib.pyplot as plt

chamber_height = 0.988
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.54

env = Environment()

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
    mass=17.5,      # Sobredimensionado
    inertia=(3.613, 3.613, 0.041),
    power_off_drag=r"RECURSOS\datos_convertidos.csv",
    power_on_drag=r"RECURSOS\CD_ON_ASPID.csv",
    center_of_mass_without_motor=1.1575,
    coordinate_system_orientation="nose_to_tail"
)

ASPID.add_motor(aspid_engine, position=LONGITUD_ASPID - chamber_height)
ASPID.add_nose(length=0.42, kind="ogive", position=0)
ASPID.add_trapezoidal_fins(
    n=4,
    root_chord=0.144,
    tip_chord=0.072,
    span=0.103,
    position=LONGITUD_ASPID - 0.144 - 0.05
)

ASPID.add_parachute(
    "drogue",
    cd_s=0.516,  
    trigger="apogee",
    radius=0.52,
    lag=1,
)

test_flight = Flight(
    environment=env,
    rocket=ASPID,
    rail_length=6,
    inclination=84.0,    
)

# ==========================================
# ANÁLISIS DE ACELERACIÓN
# ==========================================

# Obtener el tiempo de apertura del paracaídas drogue
drogue_trigger_time = test_flight.parachute_events[0][0]  # Tiempo de apertura del drogue
apogee_time = test_flight.apogee_time

print(f"\n{'='*60}")
print(f"INFORMACIÓN DE VUELO - ASPID")
print(f"{'='*60}")
print(f"Tiempo de apogeo: {apogee_time:.3f} s")
print(f"Tiempo de apertura drogue: {drogue_trigger_time:.3f} s")
print(f"Altitud de apogeo: {test_flight.apogee:.2f} m")

# Calcular aceleración en el momento de apertura del drogue
aceleracion_drogue = test_flight.az(drogue_trigger_time)
print(f"\n{'='*60}")
print(f"ACELERACIÓN EN APERTURA DEL DROGUE")
print(f"{'='*60}")
print(f"Aceleración vertical (az): {aceleracion_drogue:.6f} m/s²")
print(f"Aceleración en g's: {aceleracion_drogue/9.81:.6f} g")

# Crear gráfica de aceleración con alta precisión
tiempo_inicio = test_flight.apogee_time - 5  # 5 segundos antes del apogeo
tiempo_fin = test_flight.apogee_time + 10
precision = 10000  # Número de puntos

tiempos = np.linspace(tiempo_inicio, tiempo_fin, precision)
aceleraciones = [test_flight.az(t) for t in tiempos]

# Crear figura con mejor resolución
plt.figure(figsize=(12, 7))
plt.plot(tiempos, aceleraciones, 'b-', linewidth=1.5, label='Aceleración vertical')

# Marcar el punto de apertura del drogue
plt.axvline(x=drogue_trigger_time, color='r', linestyle='--', linewidth=2, 
            label=f'Apertura drogue (t={drogue_trigger_time:.2f}s)')
plt.plot(drogue_trigger_time, aceleracion_drogue, 'ro', markersize=10, 
         label=f'az={aceleracion_drogue:.2f} m/s²')

# Marcar apogeo
plt.axvline(x=apogee_time, color='g', linestyle='--', linewidth=1.5, 
            label=f'Apogeo (t={apogee_time:.2f}s)')

plt.xlabel('Tiempo (s)', fontsize=12)
plt.ylabel('Aceleración vertical (m/s²)', fontsize=12)
plt.title('Aceleración Vertical del Cohete ASPID durante el Vuelo', fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.legend(loc='best', fontsize=10)
plt.tight_layout()

plt.show()

# Análisis adicional - valores extremos
print(f"\n{'='*60}")
print(f"ANÁLISIS DE ACELERACIONES EXTREMAS")
print(f"{'='*60}")

# Aceleración máxima
aceleracion_max = max(aceleraciones)
idx_max = aceleraciones.index(aceleracion_max)
tiempo_max = tiempos[idx_max]
print(f"Aceleración máxima: {aceleracion_max:.2f} m/s² ({aceleracion_max/9.81:.2f} g) en t={tiempo_max:.2f} s")

# Aceleración mínima (desaceleración máxima)
aceleracion_min = min(aceleraciones)
idx_min = aceleraciones.index(aceleracion_min)
tiempo_min = tiempos[idx_min]
print(f"Aceleración mínima: {aceleracion_min:.2f} m/s² ({aceleracion_min/9.81:.2f} g) en t={tiempo_min:.2f} s")

print(f"\n{'='*60}\n")