from dash import html
import dash_bootstrap_components as dbc

def layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3("Range Control Platform"),
                html.P("Use the navigation to build a plan, validate it, and manage overrides")
            ]
        )
    )