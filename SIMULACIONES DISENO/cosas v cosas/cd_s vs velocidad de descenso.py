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
cd_s = np.linspace(0.1, 3, num=20)  
radius_parachute = np.linspace(0.2, 1.5, num=20)

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
total_simulaciones = len(cd_s)
print(f"Iniciando {total_simulaciones} simulaciones para analizar la masa del cohete...")

for i, cd_s_actual in enumerate(cd_s, start=1):
    for j, radius_parachute_actual in enumerate(radius_parachute, start=1):
        print(f"\rProgreso: [{i}/{total_simulaciones}] | Coeficiente de arrastre: {cd_s_actual:.1f}", end="", flush=True)

        ASPID = Rocket(
            radius=RADIO_ASPID,
            mass=17.5,
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

        
        ASPID.add_parachute(
            "drogue",
            cd_s=cd_s_actual,  
            trigger="apogee",
            radius=radius_parachute_actual,
            lag=1,
        )

        ASPID.add_parachute(
            "main",
            cd_s=6.171,
            trigger=300,
            radius=1.78,
            lag=1,
        )
        

        # Simular Vuelo
        test_flight = Flight(
            environment=env,
            rocket=ASPID,
            rail_length=12,
            inclination=84.0,
            
        )
        
        # Guardar exclusivamente el resultado del apogeo
        resultados_apogeo.append(test_flight.vz(test_flight.apogee_time + 10))

print("\nSimulaciones completadas. Generando gráfica...")

# ==========================================
# 5. VISUALIZACIÓN DE RESULTADOS
# ==========================================

# Transformar los resultados a una matriz [radius x cd_s]
resultados_apogeo = np.array(resultados_apogeo)
resultados_apogeo = resultados_apogeo.reshape((len(radius_parachute), len(cd_s)))

# Gráfica 1: Velocidad de descenso vs cd_s para cada radio de drogue
plt.figure(figsize=(10, 6))
for idx, radio in enumerate(radius_parachute):
    plt.plot(cd_s, resultados_apogeo[idx], marker='o', linestyle='-', linewidth=2, label=f'Radio {radio:.2f} m')

plt.title('Velocidad de descenso vs cd_s para diferentes radios de drogue', fontsize=14)
plt.xlabel('cd_s de la drogue', fontsize=12)
plt.ylabel('Velocidad de Descenso [m/s]', fontsize=12)
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.legend(title='Radio drogue')
plt.tight_layout()
plt.show()

# Gráfica 3: Mapa de calor de velocidad de descenso para combinaciones de cd_s y radio
plt.figure(figsize=(10, 6))
plt.imshow(resultados_apogeo, aspect='auto', origin='lower',
           extent=[cd_s[0], cd_s[-1], radius_parachute[0], radius_parachute[-1]],
           cmap='viridis')
plt.colorbar(label='Velocidad de Descenso [m/s]')
plt.title('Mapa de calor: Velocidad de descenso vs cd_s y radio de drogue', fontsize=14)
plt.xlabel('cd_s de la drogue', fontsize=12)
plt.ylabel('Radio de la drogue [m]', fontsize=12)
plt.tight_layout()
plt.show()

