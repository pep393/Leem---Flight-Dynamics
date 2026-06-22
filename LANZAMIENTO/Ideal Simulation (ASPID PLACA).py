from rocketpy import Environment, Rocket, Flight, SolidMotor
import numpy as np
import serial
import time as time_lib

# --- CONFIGURACIÓN SERIAL ---
# Ajusta 'COM3' al puerto que use tu placa (en Linux/Mac suele ser '/dev/ttyUSB0' o similar)
PUERTO_SERIAL = 'COM5'
BAUD_RATE = 115200

try:
    placa = serial.Serial(PUERTO_SERIAL, BAUD_RATE, timeout=0.1)
    time_lib.sleep(2) # Pausa necesaria para que la placa se reinicie al abrir la conexión
    print("Conexión serial establecida.")
except serial.SerialException as e:
    print(f"ERROR: No se pudo abrir el puerto serial. Detalles: {e}")
    placa = None


# --- CONFIGURACIÓN ROCKETPY ---
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
    n=4,
    root_chord=0.144,
    tip_chord=0.072,
    span=0.103,
    position=LONGITUD_ASPID - 0.144 - 0.05
)
# --- LÓGICA DE CONTROL HIL CORREGIDA ---
# La firma debe ser exactamente: (time, sampling_rate, state, state_history, observed_variables, aerofreno)
def controller_function(time, sampling_rate, state, state_history, observed_variables, aerofreno):
    # Extraemos altitud y velocidad vertical (vz es state[5] en RocketPy)
    altitude = state[2]
    vz = state[5]
    
    if placa is not None and placa.is_open:
        try:
            # Enviamos ambos valores separados por coma
            mensaje = f"{altitude:.2f},{vz:.2f}\n"
            placa.write(mensaje.encode('utf-8'))
            placa.flush()
            
            respuesta = placa.readline().decode('utf-8').strip()
            if respuesta:
                extension = float(respuesta)
                aerofreno.deployment_level = max(0.0, min(1.0, extension))
        except Exception as e:
            pass
    print("Altitud:", altitude, "m, Aerofreno:", aerofreno.deployment_level)

# Al añadirlo, RocketPy validará que la función anterior tiene los argumentos correctos
aerofreno = ASPID.add_air_brakes(
    drag_coefficient_curve="airbrakes.csv", # Asegúrate de que este archivo existe en la ruta
    controller_function=controller_function,
    sampling_rate=100 
)

print("Iniciando vuelo...")
test_flight = Flight(
    environment=env,
    rocket=ASPID,
    rail_length=6,
    inclination=84.0
)

# Cerrar el puerto al terminar
if placa and placa.is_open:
    placa.close()
