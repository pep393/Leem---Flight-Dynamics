import matplotlib.pyplot as plt
import pandas as pd

archivos = [
    {'path': 'mach_cd_prot_cono_cola.csv', 'label': 'Power Off', 'color': 'tab:orange', 'style': '-'},
    {'path': 'mach_cd_prot_cono_cola_power_on.csv', 'label': 'Power On', 'color': 'tab:green', 'style': '-'},
]

plt.figure(figsize=(9, 5.5))

for item in archivos:
    # header=None indica que no hay encabezado; la primera fila son datos directos
    df = pd.read_csv(item['path'], header=None, names=['mach', 'cd'])
    
    plt.plot(
        df['mach'], 
        df['cd'], 
        label=item['label'], 
        color=item['color'], 
        linestyle=item['style'], 
        linewidth=2
    )

plt.xlabel('Mach')
plt.ylabel('Cd')
plt.title('Comparison Cd vs Mach')
plt.grid(True, linestyle=':', alpha=0.7)
plt.legend()
plt.tight_layout()

plt.show()