import matplotlib.pyplot as plt
import numpy as np
import re
filename = "pruebaMonteCarlo.outputs.txt"

flight_data = []
auxiliar = []

to_look_for_data = ["apogee"]        # Poner aquí todos los valores que queramos sacar

dispersion_output_file = open(str(filename), "r+")



for data in to_look_for_data:
    patron = rf'"{data}":\s*([\d.]+)'
    for line in dispersion_output_file:
        resultado = re.search(patron, line)
        auxiliar.append(float(resultado.group(1)))
    flight_data.append(auxiliar.copy())
    auxiliar.clear()
    dispersion_output_file.seek(0)

dispersion_output_file.close()


for c, graphic in enumerate(flight_data):
    print(f"{to_look_for_data[c]} - Mean Value: {np.mean(graphic)}")
    print(f"{to_look_for_data[c]} - Standard Deviation: {np.std(graphic)}")

    plt.figure()
    plt.hist(graphic, bins=int(len(graphic)**0.5))
    plt.title(f"{to_look_for_data[c]}")
    plt.xlabel(f"{to_look_for_data[c]}")
    plt.ylabel("Number of Occurences")
    plt.show()
