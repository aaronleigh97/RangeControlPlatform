from dash import html
import dash_bootstrap_components as dbc

def layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3("Validation"),
                html.P("Validate the saved plan against store-grade department space allowances."),

                html.H5("Current Plan"),
                html.Div(id="current-plan-summary"),

                html.Hr(),
                dbc.Button("Run Validation", id="run-validation-btn", color="primary"),
                dbc.Alert(
                    id="validation-alert",
                    children="No validation run yet.",
                    color="secondary",
                    className="mt-3",
                ),
                html.Div(id="validation-details"),
            ]
        )
    )
