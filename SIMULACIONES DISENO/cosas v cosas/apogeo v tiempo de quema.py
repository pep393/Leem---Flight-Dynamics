from rocketpy import Environment, Rocket, Flight, SolidMotor, utilities
import numpy as np
import rocketpy.utilities as _rpu
from rocketpy.mathutils import Function
import matplotlib.pyplot as plt

# ============================================================
# MONKEY-PATCH
# ============================================================
def _flutter_safety_factor_fixed(flight, flutter_mach):
    flutter_source = flutter_mach.source
    safety_factor = []
    for i in range(len(flutter_source)):
        t  = flutter_source[i, 0]
        vf = flutter_source[i, 1]
        vm = flight.mach_number(t)
        if vm is None or vm == 0 or np.isnan(vm) or np.isinf(vm):
            continue
        sf = vf / vm
        if np.isnan(sf) or np.isinf(sf):
            continue
        safety_factor.append([t, sf])
    safety_factor = np.array(safety_factor)
    result = Function(
        source=safety_factor,
        inputs="Time (s)",
        outputs="Fin Flutter Safety Factor",
        interpolation="linear",
        extrapolation="zero",
    )
    result.set_title("Fin Flutter Safety Factor")
    return result

_rpu._flutter_safety_factor = _flutter_safety_factor_fixed
# ============================================================

chamber_height = 0.988
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.54

env = Environment()

times = np.linspace(2, 8, num=10)
impulsos = np.linspace(5000, 8000, num=10)

apogeos = []

for time in times:
    fila = []
    for impulso in impulsos:
        aspid_engine = SolidMotor(
            thrust_source=r"RECURSOS\Predicted_thrust.csv",
            reshape_thrust_curve=[time, impulso],
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
            root_chord=0.189,
            tip_chord=0.05,
            span=0.111,
            position=LONGITUD_ASPID - 0.189 - 0.05
        )

        test_flight = Flight(
            environment=env,
            rocket=ASPID,
            rail_length=6,
            inclination=84.0
        )

        fila.append(test_flight.apogee)
    apogeos.append(fila)

from rocketpy import Environment, Rocket, Flight, SolidMotor, utilities
import numpy as np
import rocketpy.utilities as _rpu
from rocketpy.mathutils import Function
import matplotlib.pyplot as plt

# ============================================================
# MONKEY-PATCH
# ============================================================
def _flutter_safety_factor_fixed(flight, flutter_mach):
    flutter_source = flutter_mach.source
    safety_factor = []
    for i in range(len(flutter_source)):
        t  = flutter_source[i, 0]
        vf = flutter_source[i, 1]
        vm = flight.mach_number(t)
        if vm is None or vm == 0 or np.isnan(vm) or np.isinf(vm):
            continue
        sf = vf / vm
        if np.isnan(sf) or np.isinf(sf):
            continue
        safety_factor.append([t, sf])
    safety_factor = np.array(safety_factor)
    result = Function(
        source=safety_factor,
        inputs="Time (s)",
        outputs="Fin Flutter Safety Factor",
        interpolation="linear",
        extrapolation="zero",
    )
    result.set_title("Fin Flutter Safety Factor")
    return result

_rpu._flutter_safety_factor = _flutter_safety_factor_fixed
# ============================================================

chamber_height = 0.988
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.54

env = Environment()

times = np.linspace(2, 8, num=10)
impulsos = np.linspace(5000, 8000, num=10)

apogeos = []

for time in times:
    fila = []
    for impulso in impulsos:
        aspid_engine = SolidMotor(
            thrust_source=r"RECURSOS\Predicted_thrust.csv",
            reshape_thrust_curve=[time, impulso],
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
            root_chord=0.189,
            tip_chord=0.05,
            span=0.111,
            position=LONGITUD_ASPID - 0.189 - 0.05
        )

        test_flight = Flight(
            environment=env,
            rocket=ASPID,
            rail_length=6,
            inclination=84.0
        )

        fila.append(test_flight.apogee)
    apogeos.append(fila)

# Graficar
for j, impulso in enumerate(impulsos):
    plt.plot(times, [apogeos[i][j] for i in range(len(times))], label=f"I = {impulso:.0f} Ns")

plt.xlabel("Tiempo de quema (s)")
plt.ylabel("Apogeo (m)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()