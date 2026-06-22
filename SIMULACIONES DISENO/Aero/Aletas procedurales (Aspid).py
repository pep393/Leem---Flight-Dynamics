# Código para sacar las aletas de manera procedural, configuración ASPID. 
# Esta versión de ASPID está adaptada para los cfds. Cuidado con las aletas, la altura y la posición de las aletas. 
from rocketpy import Environment, Rocket, Flight, SolidMotor, utilities
import numpy as np
import rocketpy.utilities as _rpu
from rocketpy.mathutils import Function
import matplotlib.pyplot as plt

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

chamber_height = 0.988
RADIO_ASPID = 0.065
LONGITUD_ASPID = 2.7


env = Environment()

"""
env.set_atmospheric_model(
    type="custom_atmosphere",
    pressure=None,
    temperature=300,
    wind_u=[
        (0, 5), # 5 m/s at 0 m
        (1000, 10) # 10 m/s at 1000 m
    ],
    wind_v=[
        (0, -2), # -2 m/s at 0 m
        (500, 3), # 3 m/s at 500 m
        (1600, 2), # 2 m/s at 1000 m
    ],
)
"""

root_chords = np.linspace(0.1, 0.5, num=10)
tip_chords  = np.linspace(0.05, 0.1, num=10)
spans       = np.linspace(0.1, 0.15, num=20)

i = 0


for span in spans:
    for root_chord in root_chords:
        for tip_chord in tip_chords:

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
                position=LONGITUD_ASPID - 0.144 - 0.15
            )
            ASPID.draw()

            test_flight = Flight(
                environment=env,
                rocket=ASPID,
                rail_length=6,
                inclination=84.0
            )

            # test_flight.mach_number()
            # Estabilidad
            min_stab = round(test_flight.min_stability_margin, 3)
            max_stab = round(test_flight.max_stability_margin, 3)

            # Flutter
            flutter_mach_func, safety_factor_func = utilities.fin_flutter_analysis(
                fin_thickness=0.01,
                shear_modulus=1.7e9,
                flight=test_flight,
                see_prints=False,
                see_graphs=False
            )

            sf_arr = safety_factor_func.source
            mask   = sf_arr[:, 1] > 0
            min_sf = round(float(np.min(sf_arr[mask, 1])), 3) if mask.any() else float('nan')


            line = (f"{i:4d} | Stab MIN {min_stab:6.3f} MAX {max_stab:6.3f} "
                    f"| Flutter SF min: {min_sf:6.3f} "
                    f"| Root: {round(root_chord,3)}, Tip: {round(tip_chord,3)}, Span: {round(span,3)}")

            print(line)

            with open("fins.txt", "a") as f:
                f.write(line + "\n")

            i += 1


            
            # ============================================================
            # GRÁFICO: CoM y CoP del cohete vs tiempo
            # ============================================================
            t_end    = test_flight.apogee_time
            t_vals   = np.linspace(0, t_end, 300)
            t_burnout = aspid_engine.burn_out_time

            # Centro de masas — función del cohete evaluada en cada t
            cm_vals = np.array([ASPID.center_of_mass(t) for t in t_vals])

            # Centro de presiones — cp_position(mach) se evalúa con el Mach en cada instante
            cp_vals = np.array([
                ASPID.cp_position(test_flight.mach_number(t))
                for t in t_vals
            ])

            fig, ax = plt.subplots(figsize=(10, 4))

            ax.plot(t_vals, cm_vals, color="#E84545", linewidth=2,
                    label="Centro de masas (CoM)")
            ax.plot(t_vals, cp_vals, color="#4A90D9", linewidth=2,
                    linestyle="-.", label="Centro de presiones (CoP)")

            # Relleno entre CoM y CoP — verde si estable (CoP > CoM en nose_to_tail), rojo si no
            ax.fill_between(
                t_vals, cm_vals, cp_vals,
                where=(cp_vals > cm_vals),   # CoP más hacia la cola → estable
                alpha=0.15, color="green", label="Margen estable"
            )
            ax.fill_between(
                t_vals, cm_vals, cp_vals,
                where=(cp_vals <= cm_vals),  # CoP delante del CoM → inestable
                alpha=0.15, color="red", label="Margen inestable"
            )

            # MECO
            if t_burnout <= t_end:
                ax.axvline(t_burnout, color="#FFD700", linewidth=1.5,
                           linestyle="--", label=f"MECO  t={t_burnout:.2f} s")

            ax.set_xlabel("Tiempo (s)", fontsize=11)
            ax.set_ylabel("Posición desde la nariz (m)", fontsize=11)
            ax.set_title(
                f"CoM y CoP — Root={round(root_chord,3)} m | "
                f"Tip={round(tip_chord,3)} m | Span={round(span,3)} m",
                fontsize=11
            )
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            plt.show()
            # ============================================================
