"""
Aquest codi actualitza els valors dels Fons d'Inversió de la web de Caixa d'Enginyers
i identifica quins han pujat o baixat més durant els últims dies
"""

import requests
from bs4 import BeautifulSoup
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Llegir Excel valors anteriors
data = pd.read_excel('FI_CE.xlsx')

# Canviar tipus data de string a date
nouData = []
for t in data.index:
    try:
        nouData.append(dt.datetime.strptime(data['Fecha'][t], '%d/%m/%Y').date())
    except:
        nouData.append(data['Fecha'][t].date())

data = data.drop(columns=['Fecha'])
data['Fecha'] = nouData
data2 = data.set_index('Fecha')

# Llistat de fons d¡inversió i paràmetres per trobar valors a la web
fondos_inversion = data2.columns
fondos_inversion2 = {}

for FI in fondos_inversion:
    if str(FI) == 'fondtesoro-cortoplazo':
        fondos_inversion2[FI] = 1
    else:
        fondos_inversion2[FI] = 4

report = data2

for FI in fondos_inversion:
    # Defineix i crida url
    url = 'https://www.caixaenginyers.com/web/fondosinversion/' + FI
    response = requests.get(url)
    html = response.content

    # passo la url pel BeautifulSoup
    soup = BeautifulSoup(html, "lxml")  # soup = BeautifulSoup(html2,"html.parser")

    # obtenir titol del fons
    title = soup.title.string

    # obtenir data i valor del fons
    eee = soup.find_all('tr')[fondos_inversion2[FI]]
    e2 = eee.find_all('td')[2]
    data = e2.span.string
    data = dt.datetime.strptime(data, '(%d/%m/%Y)').date()
    valor = str(e2)[str(e2).find('\n') + 1:str(e2).find('<br')].strip()
    valor = float(valor.replace(',', '.'))

    # afegir nous valors a report
    try:
        report.loc[data][FI] = valor
    except:
        report.loc[data] = 0
        report.loc[data][FI] = valor
    print(title, data, valor)

# guardar nova taula actualtzada a Excel
report = report.sort_index(axis=0)
report.to_excel('FI_CoVid.xlsx')

# Calcular valors dels FIs en p.u. per poder comparar-los millor. Referencia (1) el primer dia disponible
report_pu = report
for FI in fondos_inversion:
    report_pu[FI] = report[FI] / report[FI][0]

# Fer gràfic de valors en p.u.
colormap = plt.cm.nipy_spectral
colors = [colormap(i) for i in np.linspace(0, 1, 13)]

for FI in fondos_inversion:
    plt.plot(report.index, report_pu[FI], label=FI, color=colors[fondos_inversion.get_loc(FI)], linewidth=0.5)
plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
           ncol=5, mode="expand", borderaxespad=0., fontsize='xx-small')
plt.ylim(bottom=0.65)
plt.show()


# Fer llista alarmes per variacions superios a 'variacio' els ultims 'dies'
def alarmes(dies, variacio):
    pugen = []
    baixen = []
    for fi in fondos_inversion:
        if report[fi][-1] != 0:
            if (report[fi][-1] / report[fi][-dies]) > 1 + variacio: pugen.append(
                fi + ' ' + str(report[fi][-1] / report[fi][-dies]))
            if (report[fi][-1] / report[fi][-dies]) < 1 - variacio: baixen.append(
                fi + ' ' + str(report[fi][-1] / report[fi][-dies]))
        else:
            if (report[fi][-2] / report[fi][-dies - 1]) > 1 + variacio: pugen.append(
                fi + ' ' + str(report[fi][-2] / report[fi][-dies - 1]))
            if (report[fi][-2] / report[fi][-dies - 1]) < 1 - variacio: baixen.append(
                fi + ' ' + str(report[fi][-2] / report[fi][-dies - 1]))
    return pugen, baixen


# Mostrar quins FI han pujat o baixat mes d'un 2%
pugen, baixen = alarmes(7, 0.02)
print('Pugen7', pugen)
print('Baixen7', baixen)
pugen, baixen = alarmes(14, 0.02)
print('Pugen14', pugen)
print('Baixen14', baixen)
