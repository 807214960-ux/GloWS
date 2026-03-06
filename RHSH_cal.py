import numpy as np
import pandas as pd

T0 = 273.16
es0 = 611.0
Lv = 2.5e6
Rv = 461.0
epsilon = 0.622

def calc_esat(T):
    return es0 * np.exp(Lv / Rv * (1 / T0 - 1 / T))

def main():
    T_dir = ""  # Path to temperature variable
    Td_dir = ""  # Path to dew point temperature variable
    Pres_dir = ""  # Path to pressure variable
    Out_dir = ""  # Output file path

    T = pd.read_csv(T_dir)
    Td = pd.read_csv(Td_dir)
    Pres = pd.read_csv(Pres_dir)

    T_val = T['Temperature']
    Td_val = Td['Dewpoint_temperature']
    Pres_val = Pres['Pressure']

    # Calculate saturation vapor pressure
    esat_T = calc_esat(T_val)
    esat_Td = calc_esat(Td_val)

    # Relative Humidity (%)
    RH = np.clip(esat_Td / esat_T * 100, 0, 100)

    # Specific Humidity (kg/kg)
    SH = (epsilon * esat_Td) / (Pres_val - (1 - epsilon) * esat_Td)

    # Output results
    result = pd.DataFrame({
        "RH": RH.flatten(),
        "SH": SH.flatten()
    })

    result.to_csv(Out_dir, index=False)
    print("RH and SH calculation completed.")

if __name__ == "__main__":
    main()