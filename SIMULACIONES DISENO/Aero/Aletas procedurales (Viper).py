from rocketpy import Environment, Rocket, Flight, SolidMotor, utilities
import numpy as np
import rocketpy.utilities as _rpu
from rocketpy.mathutils import Function

# ============================================================
# MONKEY-PATCH — solo se aplica una vez, fuera del loop
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

chamber_height = 0.35
RADIO_ASPID = 0.065
LONGITUD_ASPID = 1.75

env = Environment()

root_chords = np.linspace(0.1, 0.5, num=10)
tip_chords  = np.linspace(0.05, 0.1, num=10)
spans       = np.linspace(0.1, 0.15, num=10)

i = 0
for span in spans:
    for root_chord in root_chords:
        for tip_chord in tip_chords:

            aspid_engine = SolidMotor(
                thrust_source=r"RECURSOS\FR_Vulkan.eng",
                dry_mass=4.77,  
                dry_inertia=(1.206, 1.205, 0.023),
                nozzle_radius=0.065,
                grain_number=1,
                grain_density=1841,
                grain_outer_radius=49 / 1000,
                grain_initial_inner_radius=32.5 / 2000,
                grain_initial_height=170 / 1000,
                grain_separation=15 / 1000,


                grains_center_of_mass_position=0.155,
                center_of_dry_mass_position=0.216,

                nozzle_position=chamber_height,
                throat_radius=12.5 / 1000,
                coordinate_system_orientation="combustion_chamber_to_nozzle",
            )

            ASPID = Rocket(
                radius=RADIO_ASPID,
                mass=2.43,
                inertia=(2.513, 2.513, 0.023),
                power_off_drag=r"RECURSOS\CD_OFF_ASPID.csv",
                power_on_drag=r"RECURSOS\CD_ON_ASPID.csv",
                center_of_mass_without_motor=,
                coordinate_system_orientation="nose_to_tail"
            )
            ASPID.add_motor(aspid_engine, position=LONGITUD_ASPID - chamber_height)
            ASPID.add_nose(length=0.34, kind="ogive", position=0)
            ASPID.add_trapezoidal_fins(
                n=4,
                root_chord=0.2,   
                tip_chord=0.07,
                span=0.2,
                position=LONGITUD_ASPID - 0.2 - 0.05
            )

            test_flight = Flight(
                environment=env,
                rocket=ASPID,
                rail_length=6,
                inclination=84.0
            )

            # Estabilidad
            min_stab = round(test_flight.min_stability_margin, 3)
            max_stab = round(test_flight.max_stability_margin, 3)

            # Flutter — tupla de 2: (flutter_mach_func, safety_factor_func)
            flutter_mach_func, safety_factor_func = utilities.fin_flutter_analysis(
            fin_thickness=0.01,
            shear_modulus=1.7e9,
            flight=test_flight,
            see_prints=False,
            see_graphs=False
            )

            sf_arr = safety_factor_func.source   # shape (N, 2)
            mask   = sf_arr[:, 1] > 0            # filtra SF=0 (extrapolación fuera de rango)
            min_sf = round(float(np.min(sf_arr[mask, 1])), 3) if mask.any() else float('nan')
            print(f"{i:4d} | Stab MIN {min_stab:6.3f} MAX {max_stab:6.3f} "
                  f"| Flutter SF min: {min_sf:6.3f} "
                  f"| Root: {round(root_chord,3)}, Tip: {round(tip_chord,3)}, Span: {round(span,3)}")
            i += 1

            ASPID.draw()
            test_flight.stability_margin()