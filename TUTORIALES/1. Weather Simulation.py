from rocketpy import Environment
from datetime import datetime

#######################ISA######################
"""
env = Environment()
"""



####################FORECAST#######################
"""
env_gfs = Environment(
    date=(2025, 9, 30, 16),          # Año, Mes, Día, Hora
    latitude=40.44552575443143,
    longitude= -3.7302877778310006,
    )

env_gfs.set_elevation("Open-Elevation")
env_gfs.set_atmospheric_model(type="forecast", file="GFS")   # Se pueden cambiar a otros...
env_gfs.all_info()
"""


#################ENSEMBLE####################

env_ensemble = Environment()
env_ensemble.set_date((2025, 9, 30, 16))
env_ensemble.set_location(latitude=40.44552575443143, longitude=-3.7302877778310006)
env_ensemble.set_elevation(elevation="Open-Elevation")
env_ensemble.set_atmospheric_model(type="Ensemble", file="GEFS")
env_ensemble.all_info()



"""
print(datetime.now())
"""

