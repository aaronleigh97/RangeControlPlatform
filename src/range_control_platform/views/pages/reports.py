from dash import dcc, html
import dash_bootstrap_components as dbc


def layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3("Reports"),
                html.P("This page will generate exports and summaries (PDF/CSV later)."),

                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button("Generate Summary", id="report-summary-btn", color="primary", className="w-100"),
                            width=4,
                        ),
                        dbc.Col(
                            dbc.Button("Export CSV", id="report-csv-btn", color="secondary", className="w-100"),
                            width=4,
                        ),
                        dbc.Col(
                            dbc.Button("Export PDF", id="report-pdf-btn", color="secondary", className="w-100"),
                            width=4,
                        ),
                    ],
                    className="g-2",
                ),

                html.Hr(),
                dbc.Alert(
                    id="report-status",
                    children="No report generated yet.",
                    color="secondary",
                ),
                dcc.Download(id="report-download"),
                html.Div(id="report-output"),
            ]
        )
    )
