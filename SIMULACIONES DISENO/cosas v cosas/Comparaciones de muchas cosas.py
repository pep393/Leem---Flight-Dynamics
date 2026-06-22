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

CARPETA_BASE = "Resultados_Simulacion_ASPID"

# ==========================================
# ESPACIO DE VARIABLES (LINSPACE)
# ==========================================
impulsos_totales = np.linspace(2000, 10000, num=10) # Ns
tiempos_quema = np.linspace(2,6, num=4)           # s
masas_motor_secas = np.linspace(2, 10, num=8)     # kg (Masa seca del motor)

env = Environment() 

metricas = ['apogeo', 'max_g', 'v_rail', 'max_q', 'max_mach']
resultados = {m: {t: {imp: [] for imp in impulsos_totales} for t in tiempos_quema} for m in metricas}

# ==========================================
# BUCLE DE SIMULACIÓN CON PROGRESO
# ==========================================
total_simulaciones = len(tiempos_quema) * len(impulsos_totales) * len(masas_motor_secas)
sim_actual = 0

print(f"Iniciando {total_simulaciones} simulaciones (Perfil Rectangular)...")

for t_quema in tiempos_quema:
    for impulso in impulsos_totales:
        
        # Cálculo del empuje constante (Rectángulo)
        fuerza_empuje = impulso / t_quema
        
        for masa_motor in masas_motor_secas:
            
            sim_actual += 1
            print(f"\rProgreso: [{sim_actual}/{total_simulaciones}] | T.Quema: {t_quema:.1f}s | F: {fuerza_empuje:.1f}N | Masa: {masa_motor:.1f}kg", end="", flush=True)
            
            # 1. Configurar Motor (Empuje y Tiempo por separado)
            aspid_engine = SolidMotor(
                thrust_source=fuerza_empuje, # Valor constante
                burn_time=t_quema,           # Duración de la fuerza
                dry_mass=masa_motor,
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

            # 2. Configurar Cohete
            ASPID = Rocket(
                radius=RADIO_ASPID,
                mass=11.7,
                inertia=(3.613, 3.613, 0.041),
                power_off_drag=r"RECURSOS\CD_OFF_ASPID.csv",
                power_on_drag=r"RECURSOS\CD_ON_ASPID.csv",
                center_of_mass_without_motor=1.1575,
                coordinate_system_orientation="nose_to_tail"
            )

            ASPID.add_motor(aspid_engine, position=LONGITUD_ASPID - chamber_height)
            ASPID.add_nose(length=0.42, kind="ogive", position=0)
            ASPID.add_trapezoidal_fins(
                n=4, root_chord=0.144, tip_chord=0.072,
                span=0.103, position=LONGITUD_ASPID - 0.144 - 0.05
            )

            # 3. Simular Vuelo
            test_flight = Flight(
                environment=env,
                rocket=ASPID,
                rail_length=12,
                inclination=84.0,
                terminate_on_apogee=True 
            )
            
            # 4. Guardar resultados
            resultados['apogeo'][t_quema][impulso].append(test_flight.apogee)
            resultados['max_g'][t_quema][impulso].append(test_flight.max_acceleration / 9.81)
            resultados['v_rail'][t_quema][impulso].append(test_flight.out_of_rail_velocity)
            resultados['max_q'][t_quema][impulso].append(test_flight.max_dynamic_pressure)
            resultados['max_mach'][t_quema][impulso].append(test_flight.max_mach_number)

print("\n¡Simulaciones terminadas! Guardando archivos...")

# ==========================================
# FUNCIÓN DE GUARDADO (IMÁGENES INDIVIDUALES)
# ==========================================
def save_metric_plot(metric_key, title, ylabel):
    ruta_subcarpeta = os.path.join(CARPETA_BASE, metric_key)
    os.makedirs(ruta_subcarpeta, exist_ok=True)
    
    for t_quema in tiempos_quema:
        fig, ax = plt.subplots(figsize=(8, 6))
        
        for impulso in impulsos_totales:
            y_data = resultados[metric_key][t_quema][impulso]
            ax.plot(masas_motor_secas, y_data, marker='o', markersize=4, label=f'I Total: {impulso:.0f} Ns')
        
        ax.set_title(f"{title}\n(Perfil Rectangular - Tiempo de Quema: {t_quema:.1f} s)", fontweight='bold')
        ax.set_xlabel('Masa Seca Motor [kg]')
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()

        nombre_archivo = f"{metric_key}_tquema_{t_quema:.1f}s.png"
        ruta_completa = os.path.join(ruta_subcarpeta, nombre_archivo)
        
        plt.savefig(ruta_completa, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
    print(f"Hecho: {metric_key}")

# ==========================================
# EJECUTAR EXPORTACIÓN
# ==========================================
save_metric_plot('apogeo', 'Apogeo vs Masa Seca', 'Apogeo [m]')
save_metric_plot('max_g', 'Aceleración Máxima vs Masa Seca', 'Max G [g]')
save_metric_plot('v_rail', 'Velocidad de Salida del Rail vs Masa Seca', 'Velocidad [m/s]')
save_metric_plot('max_q', 'Presión Dinámica Máxima (Max Q) vs Masa Seca', 'Max Q [Pa]')
save_metric_plot('max_mach', 'Número de Mach Máximo vs Masa Seca', 'Mach')

print(f"\nProceso finalizado. Revisa la carpeta: {CARPETA_BASE}")