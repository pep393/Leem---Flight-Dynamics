from rocketpy import Environment, SolidMotor, Rocket, Flight
import numpy as np
import matplotlib.pyplot as plt
import os

# ==========================================
# PARÁMETROS GEOMÉTRICOS Y GLOBALES
# ==========================================
chamber_height = 0.988
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.54     

CARPETA_BASE = "Resultados_Simulacion_ASPID_Apogeo"



# ==========================================
# 2. ESPACIO DE LA VARIABLE INDEPENDIENTE
# ==========================================
# Variamos la masa del cuerpo del cohete (sin motor) de 5 kg a 20 kg
masas_cohete = np.linspace(11, 20, num=5) 

# Lista simple para guardar los resultados del apogeo
resultados_apogeo = []
resultados_impact = []

# Inicializar entorno (se usa el entorno por defecto, puedes añadir clima si lo necesitas)
env = Environment() 

# ==========================================
# 3. DEFINICIÓN DEL MOTOR (Estático)
# ==========================================
# Como el motor ya no varía, lo definimos una sola vez fuera del bucle para optimizar
aspid_engine = SolidMotor(
    thrust_source=r"RECURSOS\ASPIDTHRUST.csv", 
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
    dry_mass=7.268
)

# ==========================================
# 4. BUCLE DE SIMULACIÓN
# ==========================================
total_simulaciones = len(masas_cohete)
print(f"Iniciando {total_simulaciones} simulaciones para analizar la masa del cohete...")

for i, masa_actual in enumerate(masas_cohete, start=1):
    
    print(f"\rProgreso: [{i}/{total_simulaciones}] | Masa Cohete: {masa_actual:.1f} kg", end="", flush=True)
    
    # Configurar el Cohete con la masa variable iterada
    # Nota: Mantenemos la inercia constante por simplicidad, aunque en un modelo 
    # de alta fidelidad, cambiar la masa cambiaría ligeramente el tensor de inercia.
    ASPID = Rocket(
        radius=RADIO_ASPID,
        mass=masa_actual, # <--- AQUÍ APLICAMOS LA VARIACIÓN
        inertia=(3.613, 3.613, 0.041), 
        power_off_drag=r"RECURSOS\datos_convertidos.csv",
        power_on_drag=r"RECURSOS\CD_ON_ASPID.csv",
        center_of_mass_without_motor=1.1575,
        coordinate_system_orientation="nose_to_tail"
    )

    # Ensamblar las partes del cohete
    ASPID.add_motor(aspid_engine, position=LONGITUD_ASPID - chamber_height)
    ASPID.add_nose(length=0.42, kind="ogive", position=0)
    ASPID.add_trapezoidal_fins(
        n=4, root_chord=0.144, tip_chord=0.072,
        span=0.103, position=LONGITUD_ASPID - 0.144 - 0.05
    )

    """
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
    """

    # Simular Vuelo
    test_flight = Flight(
        environment=env,
        rocket=ASPID,
        rail_length=12,
        inclination=84.0,
        
    )
    
    # Guardar exclusivamente el resultado del apogeo
    resultados_apogeo.append(test_flight.apogee)
    resultados_impact.append(test_flight.impact_velocity)

print("\nSimulaciones completadas. Generando gráfica...")

# ==========================================
# 5. VISUALIZACIÓN DE RESULTADOS
# ==========================================
# Configuración de la figura
plt.figure(figsize=(10, 6))
plt.plot(masas_cohete, resultados_apogeo, marker='o', linestyle='-', color='b', linewidth=2)

# Etiquetas y formato
plt.title('Evolución del Apogeo en función de la Masa del Cohete', fontsize=14)
plt.xlabel('Masa estructural (sin motor) [kg]', fontsize=12)
plt.ylabel('Apogeo [m]', fontsize=12)
plt.grid(True, which='both', linestyle='--', linewidth=0.5)

# Ajustar el layout para evitar que se corten los textos
plt.tight_layout()

# Mostrar la gráfica en pantalla
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(masas_cohete, resultados_impact, marker='o', linestyle='-', color='r', linewidth=2)
plt.title('Evolución de la Velocidad de Impacto en función de la Masa del Cohete', fontsize=14)
plt.xlabel('Masa estructural (sin motor) [kg]', fontsize=12)
plt.ylabel('Velocidad de Impacto [m/s]', fontsize=12)
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()