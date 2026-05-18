import py_dss_interface
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import pathlib

from PyLeerCsv import *

class PyFluxoDSS:

    def __init__(self):
        self.Filename = None
        self.Cont_I = None
        self.Cont_Volt = None

    def Executar(self,FileName):
        Cont_Volt,Cont_I = self.LectorArquivoDSS(FileName)
        return Cont_Volt,Cont_I

    def LectorArquivoDSS(self,FileName):

        ### Cargando el Archivo ###

        script_path = os.path.dirname(os.path.abspath(__file__))
        dss_file = FileName

        ### Cargando Paquete OPenDSS ###

        dss = py_dss_interface.DSS()
        dss.text(f"compile [{dss_file}]")

        ### Registro de Tension y Corriente ###

        V_max = 1.05
        V_min = 0.95
        Cont_Volt = 0
        Cont_I = 0

        ###### Registro Limites de Voltage ######

        initial_voltages = []
        max_voltages = []
        min_voltages = []

        bus_names = dss.circuit.buses_names

        for bus in bus_names:
            dss.circuit.set_active_bus(bus)
            voltages_pu = dss.bus.vmag_angle_pu[::2]
            for v in voltages_pu:
                if v < 0.05:
                    voltages_pu.remove(v)
            voltage_pu = np.mean(voltages_pu)
            if v > 1.05:
                Cont_Volt += 1
            elif v < 0.95:
                Cont_Volt += 1
            min_voltages.append(np.min(voltages_pu))
            max_voltages.append(np.max(voltages_pu))

        #print(f"Rede con {Cont_V} barramentos fuera dos limites")

        ###### Registro Limites de Corriente ######

        initial_currents = []
        max_current = []
        min_current = []
        NormAmps = []

        line_name = dss.lines.names

        for line in line_name:
            #print("line",line)
            dss.lines.name = line
            Inoramp = dss.lines.norm_amps
            #Imag = dss.lines.phases
            dss.circuit.set_active_element(line)
            Imags = dss.cktelement.currents_mag_ang[:6:2]
            Imag = np.mean(Imags)
            if Imag > Inoramp:
                Cont_I += 1
            NormAmps.append(Inoramp)
            min_current.append(np.min(Imags))
            max_current.append(np.max(Imags))

        #print(f"Rede con {Cont_I} lineas fuera dos limites")
        #print("Cont_I",Cont_I)
        #print("Cont_Volt",Cont_Volt)
        self.Cont_I = Cont_I
        self.Cont_Volt = Cont_Volt

        return Cont_Volt,Cont_I
