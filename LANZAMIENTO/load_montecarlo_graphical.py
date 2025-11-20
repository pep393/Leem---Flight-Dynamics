import matplotlib.pyplot as plt
import numpy as np

filename = "pruebaMonteCarlo.outputs.txt"
dispersion_output_file = open(str(filename), "r+")

dato = "trajectory"

flights_data = []
for line in dispersion_output_file:
    flight_data = eval(line)
    flights_data.append(flight_data[dato])          
    
dispersion_output_file.close()

times = np.linspace(0, 300 ,num=1000)        # Importante que tiene que cuadrar los tres números con los la del Monte Carlo


for flight in flights_data:
    plt.plot(times, flight, linewidth=1)
plt.xlabel('Tiempo [s]')
plt.ylabel(f'{dato}')
plt.title(f'{dato} vs tiempo',fontweight='bold')
plt.grid(True, linestyle='--', linewidth=0.5)
plt.minorticks_on()
plt.grid(which='minor', linestyle=':', linewidth=0.5)
plt.show()