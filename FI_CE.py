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
    except:  # la data no esta en el format correcte
        nouData.append(data['Fecha'][t].date())

data = data.drop(columns=['Fecha'])
data['Fecha'] = nouData
data2 = data.set_index('Fecha')

# https://www.caixaenginyers.com/es/web/fondosinversion/impact?p_p_id=com_cajaingenieros_portal_investmentfund_detail_web_portlet_InvestmentFundPortlet_INSTANCE_j9VZ5fI49u5Q&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=getExcelExport&p_p_cacheability=cacheLevelPage&_com_cajaingenieros_portal_investmentfund_detail_web_portlet_InvestmentFundPortlet_INSTANCE_j9VZ5fI49u5Q_fundId=79611&_com_cajaingenieros_portal_investmentfund_detail_web_portlet_InvestmentFundPortlet_INSTANCE_j9VZ5fI49u5Q_period=1y&_com_cajaingenieros_portal_investmentfund_detail_web_portlet_InvestmentFundPortlet_INSTANCE_j9VZ5fI49u5Q_action=exportToExcel&_com_cajaingenieros_portal_investmentfund_detail_web_portlet_InvestmentFundPortlet_INSTANCE_j9VZ5fI49u5Q_articleResourcePrimKey=147748714


# Llistat de fons d'inversió i paràmetres per trobar valors a la web
fondos_inversion = data2.columns
fondos_inversion2 = {}

for FI in fondos_inversion:
    if str(FI) == 'fondtesoro-cortoplazo':
        fondos_inversion2[FI] = 4 #1
    else:
        fondos_inversion2[FI] = 4

report = data2

for FI in fondos_inversion:
    # Defineix i crida url
    url = 'https://www.caixaenginyers.com/web/fondosinversion/' + FI
    response = requests.get(url, verify=False)
    html = response.content

    # passo la url pel BeautifulSoup
    soup = BeautifulSoup(html, "lxml")  # soup = BeautifulSoup(html2,"html.parser")

    # obtenir titol del fons
    title = soup.title.string

    # obtenir data i valor del fons
    try:
        eee = soup.find_all('tr')[fondos_inversion2[FI]]
        e2 = eee.find_all('td')[2]
        data = e2.span.string
        data = dt.datetime.strptime(data, '(%d/%m/%Y)').date()
        valor = str(e2)[str(e2).find('\n') + 1:str(e2).find('<br')].strip()
        valor = float(valor.replace(',', '.'))
    except:  # no s'ha pogut obtenir el valor de la web
        try:
        # if FI == 'premier' or : #temporalment la web en CAT no funciona pel FI PREMIER
            url = 'https://www.caixaenginyers.com/es/web/fondosinversion/' + FI
            response = requests.get(url)
            html = response.content
            # passo la url pel BeautifulSoup
            soup = BeautifulSoup(html, "lxml")  # soup = BeautifulSoup(html2,"html.parser")
            # obtenir titol del fons
            title = soup.title.string
            try:
                eee = soup.find_all('tr')[fondos_inversion2[FI]]
                e2 = eee.find_all('td')[2]
                data = e2.span.string
                data = dt.datetime.strptime(data, '(%d/%m/%Y)').date()
                valor = str(e2)[str(e2).find('\n') + 1:str(e2).find('<br')].strip()
                valor = float(valor.replace(',', '.'))
            except:
                print(FI, "tampoc no s'ha pogut obtenir")
                valor = 0
        except:#else:
            print(FI, "no s'ha pogut obtenir")
            valor = 0
        # print(FI, "no s'ha pogut obtenir")
        # valor = 0

    # afegir nous valors a report
    try:
        report.loc[data][FI] = valor
    except:  # no hi ha nou valor a afegir
        report.loc[data] = 0
        report.loc[data][FI] = valor
    print(title, data, valor)

# guardar nova taula actualtzada a Excel
report = report.sort_index(axis=0)
report.to_excel('FI_CE.xlsx')

report = report.replace(0,None)
report = report.interpolate()

# Calcular valors dels FIs en p.u. per poder comparar-los millor. Referencia (1) el primer dia disponible
report_pu = report
for FI in fondos_inversion:
    report_pu[FI] = report[FI] / report[FI][0]

# Fer gràfic de valors en p.u.
colormap = plt.cm.nipy_spectral
colors = [colormap(i) for i in np.linspace(0, 1, 13)]
line_style = [x%2 for x in range(len(colors))]
for i in range(len(line_style)):
    if (line_style[i] == 0):
        line_style[i] = '-'
    else:
        line_style[i] = '--'

for FI in fondos_inversion:
    plt.plot(report.index, report_pu[FI], label=FI, color=colors[fondos_inversion.get_loc(FI)], linewidth=0.5,
             ls=line_style[fondos_inversion.get_loc(FI)])
plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
           ncol=5, mode="expand", borderaxespad=0., fontsize='xx-small')
plt.ylim(bottom=0.65)
# plt.xlabel('date', fontsize=12)
# plt.ylabel('p.u.', fontsize=12)
plt.tick_params(direction='out', length=2, width=1, labelsize=6, grid_alpha=0.5)
plt.savefig('figura.png', dpi=200)
plt.savefig('figura2.png', dpi=100)
plt.show()
plt.close('all')


# Fer llista alarmes per variacions superios a 'variacio' en pu els ultims 'dies'
def alarmes(dies, variacio):
    pugen = []
    baixen = []
    for fi in fondos_inversion:
        if report[fi][-1] != 0:
            if (report[fi][-1] / report[fi][-dies]) > 1 + variacio: pugen.append(
                fi + ' ' + str(round(report[fi][-1] / report[fi][-dies], 5)))
            if (report[fi][-1] / report[fi][-dies]) < 1 - variacio: baixen.append(
                fi + ' ' + str(round(report[fi][-1] / report[fi][-dies], 5)))
        else:
            if (report[fi][-2] / report[fi][-dies - 1]) > 1 + variacio: pugen.append(
                fi + ' ' + str(round(report[fi][-2] / report[fi][-dies - 1], 5)))
            if (report[fi][-2] / report[fi][-dies - 1]) < 1 - variacio: baixen.append(
                fi + ' ' + str(round(report[fi][-2] / report[fi][-dies - 1], 5)))
    return pugen, baixen


# Mostrar quins FI han pujat o baixat mes d'un 2%
pugen, baixen = alarmes(5, 0.02)
print('Pugen5', pugen)
print('Baixen5', baixen)
pugen, baixen = alarmes(10, 0.02)
print('Pugen10', pugen)
print('Baixen10', baixen)
pugen, baixen = alarmes(20, 0.02)
print('Pugen20', pugen)
print('Baixen20', baixen)
pugen, baixen = alarmes(40, 0.02)
print('Pugen40', pugen)
print('Baixen40', baixen)
pugen, baixen = alarmes(60, 0.02)
print('Pugen60', pugen)
print('Baixen60', baixen)