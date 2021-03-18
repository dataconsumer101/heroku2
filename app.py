import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server


# get dataframe for outputs
# loop until all records are pulled
def get_query(flavor,tree,borough):

    if flavor == 'barchart':
        stew = ',steward'
    else:
        stew = ''

    where = "spc_common=\'" + tree + "\' and boroname=\'" + borough + "\'"

    query = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?' +\
        '$select=spc_common,health,boroname{0},count(tree_id)' +\
            '&$where={1}' +\
                '&$group=spc_common,health,boroname{0}').format(stew, where)

    i = 0
    o_query = ''
    while True:

        o_query = query + '&$offset={}'.format(i * 1000)
        o_query = o_query.replace(' ', '%20')

        df_part = pd.read_json(o_query)

        if i == 0:
            df = df_part
        else:
            df = pd.concat([df, df_part])

        if df_part.shape[0] < 1000:
            break

        i += 1    

    # calculate share % for each section
    if flavor == 'datatable':
        df_treesum = df.groupby(['spc_common', 'boroname']).sum().reset_index()
        df_treesum.columns = ['spc_common', 'boroname', 'total']

        df_health = df.merge(df_treesum, on=['spc_common','boroname'])
        df_health['Share'] = round((df_health.count_tree_id / df_health.total) * 100, 1)
        df_health['Share'] = df_health['Share'].astype('str') + ' %'

        df_health = df_health[['spc_common', 'boroname', 'health', 'count_tree_id', 'Share']]
        df_health.columns = ['spc_common', 'boroname', 'Health Condition', 'Count', 'Share']
        
        df = df_health[['Health Condition', 'Count', 'Share']]
        df_health = []
    else:
        df_stewsum = df.groupby(['spc_common', 'boroname', 'steward']).sum().reset_index()
        df_stewsum.columns = ['spc_common', 'boroname', 'steward', 'total']

        df_steward = df.merge(df_stewsum, on=['spc_common','boroname','steward'])
        df_steward['share'] = round(df_steward.count_tree_id / df_steward.total, 4)

        df = df_steward[['steward', 'health', 'share']]
        df_steward = []

    return df


# For Species Drop Down
# get distinct list of tree species
query = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?' +\
    '$select=spc_common' +\
        '&$group=spc_common')

species = pd.read_json(query)

# exclude null
species = species.dropna()


# For Borough Drop Down
query = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?' +\
    '$select=boroname' +\
        '&$group=boroname')

borough = pd.read_json(query)

# exclude null
borough = borough.dropna()


# initial data table place holder
df_ph = pd.DataFrame(data={'Health Condition': [''], 'Count': 0, 'Share': [0]})


app.layout = html.Div(children=[
    html.H3('Data608 Assignment 4 -- New York City Trees'),    
    html.H5('Tree Species (Common Name)'),
    dcc.Dropdown(
        id = 'dropdown',
        options = [{'label': i.title(), 'value': i} for i in species.spc_common],        
        value = 'sugar maple'
        # placeholder='Choose a tree species...'
    ),
    html.H5('NYC Borough'),
    dcc.Dropdown(
        id = 'location',
        options = [{'label': i.title(), 'value': i} for i in borough.boroname],        
        value = 'Manhattan'
        # placeholder='Choose a tree species...'
    ),
    html.Br(),    
    dash_table.DataTable(
        id = 'table',
        columns = [{'name': i, "id": i} for i in df_ph.columns]
    ),
    dcc.Graph(id = 'bar_graph')    
])


@app.callback(
    Output('table', 'data'),
    Output('bar_graph', 'figure'),    
    Input('dropdown', 'value'),
    Input('location', 'value'))
def update_figure(tree, loc):

    # data table
    df_dt = get_query('datatable', tree, loc)

    # bar graph
    df_bg = get_query('barchart', tree, loc)    

    fig = px.bar(df_bg, x = 'steward', y = 'share', color = 'health', title = 'Tree Health Percent Share by Steward Group')    
    
    fig.update_layout(
        xaxis_title = 'Steward Group',
        yaxis_title = 'Percent of Trees',
        legend_title = 'Health Condition'
    )

    return df_dt.to_dict('records'), fig



if __name__ == '__main__':
    app.run_server(debug=True)


