#!/usr/bin/env python
# coding: utf-8

# In[13]:


import requests

# -------------------------
# 1. Einstellungen
# -------------------------
API_KEY = "c13ff652e17330b9b9f54fd8aeea3d3e"

# 1. Ort eingeben
# -------------------------
STADT = input("Ort eingeben (z. B. Berlin): ")

#STADT = "Berlin"
URL = "https://api.openweathermap.org/data/2.5/weather"

# -------------------------
# 2. API-Aufruf
# -------------------------
params = {
    "q": STADT,
    "appid": API_KEY,
    "units": "metric",
    "lang": "de"
}

response = requests.get(URL, params=params)
daten = response.json()

# -------------------------
# 3. Daten auslesen
# -------------------------
temperatur = daten["main"]["temp"]                      # aktuelle Temperatur in °C
luftfeuchtigkeit = daten["main"]["humidity"]            # aktuelle Luftfeuchtigkeit in %
beschreibung = daten["weather"][0]["description"]       # Wettertext

# -------------------------
# 4. Ausgabe
# -------------------------
print(f"Wetter in {STADT}:")
print(f"🌡️ Temperatur: {temperatur} °C")
print(f"💧 Luftfeuchtigkeit: {luftfeuchtigkeit} %")
print(f"☁️ Wetter: {beschreibung}")



#------------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------- Erweiterung ------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------

print("-----------------------------------------------------------------------------------")

print("Hier ist Visualisierung von Temperatur- oder Niederschlagsverläufen (Monat-Jahr)")

from datetime import datetime
import calendar
import pandas as pd

import meteostat as ms
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt

# -------------------------
# 1. Inputs
# -------------------------
stadt = input("Stadt (z. B. Berlin): ")

jahre_text = input("Vorjahre zum Vergleich (z. B. 2022,2023): ")
jahre = [int(j.strip()) for j in jahre_text.split(",")]

monat_input = input("Monat (Zahl oder Name, leer = aktueller Monat): ").strip().lower()

# -------------------------
# 2. Monat parsen
# -------------------------
monat_mapping = {
    "januar": 1, "january": 1,
    "februar": 2, "february": 2,
    "märz": 3, "maerz": 3, "march": 3,
    "april": 4,
    "mai": 5, "may": 5,
    "juni": 6, "june": 6,
    "juli": 7, "july": 7,
    "august": 8,
    "september": 9,
    "oktober": 10, "october": 10,
    "november": 11,
    "dezember": 12, "december": 12
}

if not monat_input:
    monat = datetime.now().month
elif monat_input.isdigit():
    monat = int(monat_input)
else:
    monat = monat_mapping.get(monat_input)
    if monat is None:
        raise ValueError("Monat nicht erkannt")

monat_name = calendar.month_name[monat]
print(f"Gewählter Monat: {monat_name}")

# -------------------------
# 3. Geocode city
# -------------------------
geolocator = Nominatim(user_agent="meteostat_app")
location = geolocator.geocode(stadt)

if location is None:
    raise ValueError(f"Ort '{stadt}' nicht gefunden")

lat, lon = location.latitude, location.longitude
ort = ms.Point(lat, lon)

# -------------------------
# 4. Stations
# -------------------------
stationen_df = ms.stations.nearby(ort, limit=5)
if stationen_df.empty:
    raise ValueError("Keine Wetterstationen gefunden")

# -------------------------
# 5. Daten sammeln (ENDGÜLTIG ROBUST)
# -------------------------
daten = {}

for jahr in jahre:
    start = datetime(jahr, monat, 1)
    letzter_tag = calendar.monthrange(jahr, monat)[1]
    ende = datetime(jahr, monat, letzter_tag)

    df = None
    for station_id in stationen_df.index:
        df = ms.daily(station_id, start, ende).fetch()
        if df is not None and not df.empty:
            break

    temps, prcps = [], []

    if df is not None and not df.empty:
        for _, row in df.iterrows():
            # Temperatur
            tavg = row.get("tavg")
            tmin = row.get("tmin")
            tmax = row.get("tmax")

            if pd.notna(tavg):
                temps.append(tavg)
            elif pd.notna(tmin) and pd.notna(tmax):
                temps.append((tmin + tmax) / 2)
            else:
                temps.append(None)

            # Niederschlag → None = 0 mm
            prcp = row.get("prcp")
            prcps.append(prcp if pd.notna(prcp) else 0)
    else:
        temps = [None] * letzter_tag
        prcps = [0] * letzter_tag

    daten[jahr] = {"temp": temps, "prcp": prcps}

# -------------------------
# 6. Plot (2 y-Achsen)
# -------------------------
fig, ax_temp = plt.subplots(figsize=(13, 6))
ax_prcp = ax_temp.twinx()

tage = range(1, calendar.monthrange(jahre[0], monat)[1] + 1)
farben = plt.cm.tab10.colors

for i, (jahr, werte) in enumerate(daten.items()):
    farbe = farben[i % len(farben)]

    ax_temp.plot(
        tage, werte["temp"],
        marker="o",
        color=farbe,
        label=f"{jahr} Temperatur"
    )
 
    ax_prcp.bar(                               #wenn nichts erscheit, dann kein Regen in diesem Monat
        tage, werte["prcp"],
        alpha=0.3,
        color=farbe,
        label=f"{jahr} Niederschlag"
    )


ax_temp.set_xlabel("Tag im Monat")
ax_temp.set_ylabel("Temperatur (°C)")
ax_prcp.set_ylabel("Niederschlag (mm)")

ax_temp.set_title(f"Tägliche Temperatur & Niederschlag im {monat_name} in {stadt}")

lines1, labels1 = ax_temp.get_legend_handles_labels()
lines2, labels2 = ax_prcp.get_legend_handles_labels()
ax_temp.legend(lines1 + lines2, labels1 + labels2)

ax_temp.grid(True)
plt.tight_layout()
plt.show()





# In[ ]:




