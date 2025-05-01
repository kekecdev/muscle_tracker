import pandas as pd
from dash import Dash, html, dcc, Input, Output
import plotly.express as px

# Google Drive の公開 CSV URL（YOUR_FILE_ID を置き換えてください）
DRIVE_CSV_URL = "https://drive.google.com/uc?export=download&id=YOUR_FILE_ID"

def estimate_1rm(w, r):
    return w * (1 + r/30)

df = pd.read_csv(DRIVE_CSV_URL, parse_dates=['date'])
df['est_1rm'] = df.apply(lambda row: estimate_1rm(row['weight'], row['reps']), axis=1)

app = Dash(__name__)
app.layout = html.Div([
    html.H1("ベストセットトラッカー", style={'textAlign':'center'}),
    dcc.DatePickerRange(
        id='date-range',
        start_date=df.date.min(),
        end_date=df.date.max(),
        display_format='YYYY-MM-DD'
    ),
    dcc.Graph(id='graph-weight'),
    dcc.Graph(id='graph-est1rm'),
])

@app.callback(
    [Output('graph-weight','figure'),
     Output('graph-est1rm','figure')],
    [Input('date-range','start_date'),
     Input('date-range','end_date')]
)
def update(start_date, end_date):
    dff = df[(df.date>=start_date)&(df.date<=end_date)]
    fig1 = px.line(dff, x='date', y='weight', title='重量推移')\
             .update_xaxes(rangeslider_visible=True)
    fig2 = px.line(dff, x='date', y='est_1rm', title='推定1RM推移')\
             .update_xaxes(rangeslider_visible=True)
    return fig1, fig2

if __name__=='__main__':
    app.run_server(host='0.0.0.0', port=8080)
