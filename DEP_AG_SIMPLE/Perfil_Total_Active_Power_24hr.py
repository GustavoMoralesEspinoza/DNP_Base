import py_dss_interface
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import pathlib
import matplotlib as mpl

script_path = os.path.dirname(os.path.abspath(__file__))

# Cambiar fuente a Times New Roman
mpl.rcParams['font.family'] = 'Times New Roman'

red = "1301"
rede = "RITQ" + red
dss_file = pathlib.Path(script_path).joinpath("../feeders", "ITQ", "RITQ" + red, "DU_1_Master_391_ITQ_" + rede + ".dss")
#dss_file = pathlib.Path(script_path).joinpath("../feeders", "18Bus", "ArquivoDss2_base.dss")
#dss_file = pathlib.Path(script_path).joinpath("../feeders", "54Bus", "54Bus.dss")
#dss_file = pathlib.Path(script_path).joinpath("../feeders", "ITQ_D", "RITQ" + red, "DU_1_Master_391_ITQ_" + rede + ".dss")
#dss_file = pathlib.Path(script_path).joinpath("../feeders", "3R_V2", "ieee34Mod3_Induscon_curvas.dss")
#dss_file = pathlib.Path(script_path).joinpath("../feeders", "18Bus", "ArquivoDss2_base.dss")
script_path = os.path.dirname(os.path.abspath(__file__))
dss_file = pathlib.Path(script_path).joinpath("../feeders", "PEA5020_54", "54_Bus_Base_noEM.dss")
dss_file = pathlib.Path(script_path).joinpath("../feeders", "PEA5020_54", "Chaveamento","54_Bus_Reconfig_SwtControl_Base.dss" )

dss = py_dss_interface.DSS()
dss.text(f"compile [{dss_file}]")

active_powers = []
for hour in range(24):
    dss.text("Set mode=daily")
    dss.text(f"Set number={hour + 1}")
    dss.text("Solve")
    total_power_a = abs(dss.circuit._total_power()[0])
    total_power_r = abs(dss.circuit._total_power()[1])
    active_powers.append(total_power_a)

max_active_power = max(active_powers)

df_active_powers = pd.DataFrame({
    'Hora': np.arange(1, 25),
    'Carga Activa Total (kW)': active_powers
})

# Crear gráfico
plt.figure(figsize=(8, 4))
plt.plot(np.arange(1, 25), active_powers, marker='o', linestyle='-', color='green', label="Active Power (kW)")
plt.axhline(max_active_power, color='gray', linestyle='--', linewidth=1.2, label=f'Pmax = {max_active_power:.1f} kW')

# Configurar ejes
plt.xlim(1, 24)
plt.xticks(np.arange(1, 25, 2), fontsize=17)  # Aumentar fuente de los valores del eje x
plt.yticks(fontsize=17)  # Aumentar fuente de los valores del eje y
plt.xlabel("Hour", fontsize=15, fontweight='bold')
plt.ylabel("Active Power (kW)", fontsize=15, fontweight='bold')

# Estilo general
plt.title("Total Load Profile", fontsize=15)
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(fontsize=15)
plt.tight_layout()

# Guardar y mostrar
plt.savefig("perfil_carga_activa_11a24.png", dpi=300)
plt.show()

df_active_powers['Carga Máxima (kW)'] = max_active_power
print(f"Carga Activa Máxima en el período de 24 horas: {max_active_power:.2f} kW")
print(df_active_powers)
df_active_powers.to_csv("carga_activa_24h.csv", index=False)

