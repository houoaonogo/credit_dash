#!/usr/bin/env python
# coding: utf-8

import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import pandas as pd

# 讀取數據（請確保 UCI_Credit_Card.csv 和 app.py 放在同一個專案目錄下）
df = pd.read_csv("UCI_Credit_Card.csv")
all_cols = df.columns.tolist()

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # 讓 Render 的 gunicorn 可以偵測並啟動

app.layout = html.Div([
    html.H1("信用卡資料全方位探索系統", style={'textAlign': 'center'}),
    dcc.Tabs(id="tabs", value='tab-1', children=[
        dcc.Tab(label='數據總覽', value='tab-1'),
        dcc.Tab(label='趨勢與相關性', value='tab-2'),
        dcc.Tab(label='類別違約分析', value='tab-3'),
    ]),
    html.Div(id='tabs-content'),
    html.Div([
        html.Button("下載數據檔案", id="btn-download", style={'margin-top': '20px'}),
        dcc.Download(id="download-dataframe-csv")
    ], style={'textAlign': 'right', 'padding': '20px'})
])

# Callback 1: 頁面內容切換
@app.callback(Output('tabs-content', 'children'), Input('tabs', 'value'))
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            dcc.Dropdown(id='hist-col', options=all_cols, value='LIMIT_BAL'),
            dcc.Graph(id='dist-plot'),
            dash_table.DataTable(id='stats-table', page_size=5)
        ])
    elif tab == 'tab-2':
        return html.Div([
            dcc.Dropdown(id='x-col', options=all_cols, value='AGE'),
            dcc.Dropdown(id='y-col', options=all_cols, value='LIMIT_BAL'),
            dcc.Graph(id='rel-plot'),
            dcc.Graph(id='corr-heatmap'),
            dcc.Graph(id='pay-trend-plot')
        ])
    elif tab == 'tab-3':
        return html.Div([
            dcc.Dropdown(id='cat-col', options=all_cols, value='EDUCATION'),
            dcc.Graph(id='bar-default-rate'),
            dcc.Graph(id='box-limit-cat')
        ])

# Callback 2: Tab 1 繪圖
@app.callback(
    [Output('dist-plot', 'figure'), Output('stats-table', 'data')],
    [Input('hist-col', 'value')]
)
def update_tab1(hist_col):
    fig = px.histogram(df, x=hist_col, marginal="box", title=f'{hist_col} 分佈')
    stats = df[[hist_col]].describe().reset_index().to_dict('records')
    return fig, stats

# Callback 3: Tab 2 繪圖
@app.callback(
    [Output('rel-plot', 'figure'), Output('corr-heatmap', 'figure'), Output('pay-trend-plot', 'figure')],
    [Input('x-col', 'value'), Input('y-col', 'value')]
)
def update_tab2(x_col, y_col):
    fig_rel = px.scatter(df, x=x_col, y=y_col, opacity=0.3, trendline="ols")
    fig_corr = px.imshow(df.corr(), title="相關性熱力圖")
    fig_pay = px.violin(df.melt(value_vars=['PAY_0','PAY_2','PAY_3','PAY_4','PAY_5','PAY_6']), 
                        x='variable', y='value', box=True, title="還款狀態趨勢")
    return fig_rel, fig_corr, fig_pay

# Callback 4: Tab 3 繪圖
@app.callback(
    [Output('bar-default-rate', 'figure'), Output('box-limit-cat', 'figure')],
    [Input('cat-col', 'value')]
)
def update_tab3(cat_col):
    def_rate = df.groupby(cat_col)['default.payment.next.month'].mean().reset_index()
    fig_bar = px.bar(def_rate, x=cat_col, y='default.payment.next.month', title=f"各類別違約率 ({cat_col})")
    fig_box = px.box(df, x=cat_col, y='LIMIT_BAL', color='default.payment.next.month', title="額度分佈與違約對比")
    return fig_bar, fig_box

# 下載邏輯
@app.callback(Output("download-dataframe-csv", "data"), Input("btn-download", "n_clicks"), prevent_initial_call=True)
def download_data(n_clicks):
    return dcc.send_data_frame(df.to_csv, "UCI_Credit_Card_Export.csv")

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
