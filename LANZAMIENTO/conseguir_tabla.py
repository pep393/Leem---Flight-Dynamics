import matplotlib.pyplot as plt
import numpy as np

filename = "pruebaMonteCarlo.outputs.txt"
dispersion_output_file = open(str(filename), "r+")

dato = "zoom_velocity"

numero_valores = 60

flights_data = []
for line in dispersion_output_file:
    flight_data = eval(line)
    flights_data.append(flight_data[dato])          
    
dispersion_output_file.close()


"""def interpolate_downsample(lst, new_length):
    x_old = np.linspace(0, 1, len(lst))
    x_new = np.linspace(0, 1, new_length)
    return np.interp(x_new, x_old, lst).tolist()
"""

puntos = []
for punto in range(numero_valores):
    puntos.append([])


for flight in flights_data:
    # flight = interpolate_downsample(flight, numero_valores)
    for c, point in enumerate(flight):
        puntos[c].append(point)

for c, i in enumerate(puntos):
    puntos[c] = np.mean(i)

for i in puntos:
    