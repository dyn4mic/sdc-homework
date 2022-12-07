# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
from datetime import timedelta,date,datetime
import requests
import api
#import urllib3
#requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'

app = Dash(__name__)

data = pd.read_csv(
    "https://covid19-dashboard.ages.at/data/CovidFaelle_Altersgruppe.csv", delimiter=";")

data_temp = data.copy()
data_temp['Time'] = pd.to_datetime(
    data_temp["Time"], format='%d.%m.%Y %H:%M:%S')
data_temp = data_temp.sort_values(['Bundesland', 'Altersgruppe', 'Time', ])
data_temp = data_temp.groupby(['Bundesland', 'Altersgruppe', 'Time']).sum(numeric_only=True)
data_temp = data_temp.reset_index()
data_temp['Anzahl_prev'] = data_temp.groupby(
    ['Bundesland', 'Altersgruppe'])['Anzahl'].shift(1)
data_temp['AnzahlTot_prev'] = data_temp.groupby(
    ['Bundesland', 'Altersgruppe'])['AnzahlTot'].shift(1)
data_temp['deltaAnzahl'] = data_temp['Anzahl']-data_temp['Anzahl_prev']
data_temp['deltaAnzahlTot'] = data_temp['AnzahlTot'] - \
    data_temp['AnzahlTot_prev']
data_temp2 = data_temp.set_index('Time').groupby(['Bundesland', 'Altersgruppe']).rolling(
    7, min_periods=1)['deltaAnzahl'].agg({"sevenday_inc": "sum"}).reset_index()
data_temp = pd.merge(data_temp, data_temp2, on=[
                     'Bundesland', 'Altersgruppe', 'Time'])
data_temp['sevenday_inc'] = 100000 * \
    data_temp['sevenday_inc']/data_temp['AnzEinwohner']


def getFilteredDataframe(bundesland: str = 'Österreich', start_date: 'datetime' = data_temp.Time.max()-timedelta(days=45), end_date: 'datetime' = data_temp.Time.max()):
    return data_temp[((data_temp['Time'] >= start_date) & (data_temp['Time'] <= end_date) & (data_temp['Bundesland'] == bundesland))].sort_values(by='Time')


@app.callback(
    Output('graph-heatmap-incident', 'figure'),
    Input('select-bundesland', 'value'),
    Input('time-date-picker-range', 'start_date'),
    Input('time-date-picker-range', 'end_date'))
def generateHeatmap(bundesland: str, start_date, end_date):
    data_temp3 = getFilteredDataframe(bundesland, start_date, end_date).pivot(
        index="Altersgruppe", columns="Time", values="sevenday_inc")
    data_temp3.index = pd.CategoricalIndex(data_temp3.index, categories=[
                                           ">84", "75-84", "65-74", "55-64", "45-54", "35-44", "25-34", "15-24", "5-14", "<5"])
    data_temp3.sort_index(level=0, inplace=True)
    fig = px.imshow(data_temp3, title="7-day incident by Age group - Heatmap")
    return fig


@app.callback(
    Output('graph-stacked-bar-deaths', 'figure'),
    Input('select-bundesland', 'value'),
    Input('time-date-picker-range', 'start_date'),
    Input('time-date-picker-range', 'end_date'))
def generateStackedBarChart(bundesland: str, start_date: 'datetime', end_date: 'datetime'):
    data_temp2 = getFilteredDataframe(bundesland, start_date, end_date)
    data_temp3 = data_temp2.drop(data_temp2.columns.difference(
        ["Time", "Altersgruppe", "deltaAnzahlTot"]), axis=1)
    data_temp3.Altersgruppe = pd.Categorical(data_temp3.Altersgruppe, categories=[
                                             ">84", "75-84", "65-74", "55-64", "45-54", "35-44", "25-34", "15-24", "5-14", "<5"], ordered=True)
    data_temp3.sort_values("Altersgruppe", inplace=True)
    fig = px.bar(data_temp3, x="Time", y="deltaAnzahlTot",
                 color="Altersgruppe", title="Daily Deaths by Age group")
    return fig


@app.callback(
    Output('graph-current-incident', 'figure'),
    Input('select-bundesland', 'value'))
def generateLastDayIncident(bundesland: str):
    data_temp2 = getFilteredDataframe(
        bundesland, data_temp["Time"].max(), data_temp["Time"].max())
    data_temp3 = data_temp2.drop(
        data_temp2.columns.difference(["Altersgruppe", "sevenday_inc"]), axis=1)
    data_temp3.Altersgruppe = pd.Categorical(data_temp3.Altersgruppe, categories=[
                                             ">84", "75-84", "65-74", "55-64", "45-54", "35-44", "25-34", "15-24", "5-14", "<5"], ordered=True)
    data_temp3.sort_values("Altersgruppe", inplace=True)
    fig = px.bar(data_temp3, x="sevenday_inc", y="Altersgruppe", color="Altersgruppe",
                 title="Last Day - 7-day incident by Age group")
    return fig

@app.callback(
    Output('textarea', 'value'),
    Input('input_number', 'value'))
def useApi(number: int):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
    }
    params = {
        'number': number,
    }
    response = requests.post('http://localhost:8000/domagicwithnumber', params=params, headers=headers)
    return response.text

@app.callback(
    Output('label-proposal', 'children'),
    Input('time-date-picker-range', 'end_date'),
    Input('radio-days', 'value'))
def calculateStartDate(end_date: 'datetime',number: int):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
    }
    params = {
        'endDate': end_date[:10],
        'shiftdays': number
    }
    response = requests.post('http://127.0.0.1:8000/shiftDate', params=params, headers=headers)
    return "(Proposed Start Date: {})".format(response.json()['startDate'])


app.layout = html.Div(children=[
    html.H1(children='COVID-19 - By the numbers'),
    html.Div(style={'width': '32%', 'display': 'inline-block'}),
    html.Div(children=[
        html.Label('Dropdown'),
        dcc.Dropdown(data_temp.Bundesland.unique().tolist(),
                     'Österreich', id='select-bundesland'),
        html.Br(),
        html.Label('Time'),html.Label("(Proposed Start Date: )",id="label-proposal"),
        html.Br(),
        dcc.DatePickerRange(
            id='time-date-picker-range',
            min_date_allowed=data_temp.Time.min(),
            max_date_allowed=data_temp.Time.max(),
            start_date=data_temp.Time.max()-timedelta(days=45),
            end_date=data_temp.Time.max()
        ),
        dcc.RadioItems([
        {'label': '45 Tage', 'value': 45},
        {'label': '90 Tage', 'value': 90},
        {'label': '120 Tage', 'value': 120}
    ],
    45,id='radio-days'
)
    ], style={'width': '32%', 'padding': 10, 'flex': 1, 'display': 'inline-block'}),
    html.Div(style={'width': '32%', 'display': 'inline-block'}),

    html.Div(children=[dcc.Graph(
        id='graph-heatmap-incident'
    )], style={'width': '49%', 'display': 'inline-block'}),
    html.Div(children=[dcc.Graph(
        id='graph-current-incident'
    )], style={'width': '49%', 'display': 'inline-block'}),
    html.Div(children=[dcc.Graph(
        id='graph-stacked-bar-deaths'
    )], style={'width': '49%', 'display': 'inline-block'}),
    html.Div(children=[dcc.Input(
            id="input_number",
            type="number",
            value='1',
            placeholder="input type number"
        ),dcc.Textarea(
        id='textarea',
        value='',
        style={'width': '100%', 'height': 300},
    )
        ], style={'width': '49%', 'display': 'inline-block'})

])



def start():    
    app.run_server(host='0.0.0.0')

if __name__ == '__main__':
    start()