import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline, PchipInterpolator, interp1d

# Datos originales
mach_data = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
cd_data = np.array(
    [0.494, 0.453, 0.432, 0.418, 0.407, 0.398, 0.391, 0.385, 0.395, 0.479]
)

# Definición de interpoladores
f_linear = interp1d(mach_data, cd_data, kind="linear")
f_cubic = CubicSpline(mach_data, cd_data)
f_pchip = PchipInterpolator(mach_data, cd_data)

# Malla de Mach con paso fino de 0.01
mach_interp = np.round(np.arange(0.10, 1.01, 0.01), 2)

# Creación del DataFrame con las tres interpolaciones
df = pd.DataFrame(
    {
        "Mach": mach_interp,
        "CD_Linear": np.round(f_linear(mach_interp), 5)
    }
)

# Exportación a CSV
df.to_csv("interpolacion_mach_cd.csv", index=False)