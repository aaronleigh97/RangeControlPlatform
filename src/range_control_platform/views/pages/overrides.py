from dash import html, dcc
import dash_bootstrap_components as dbc

def layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3("Overrides"),
                html.P(
                    "This page will allow controlled override requests with justification and audit trail."
                ),

                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Override reason"),
                                dcc.Textarea(
                                    id="override-reason",
                                    placeholder="Explain why an override is required (business justification)...",
                                    style={"width": "100%", "height": "100px"},
                                ),
                            ],
                            width=8,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Severity"),
                                dcc.Dropdown(
                                    id="override-severity",
                                    options=[
                                        {"label": "Low", "value": "low"},
                                        {"label": "Medium", "value": "medium"},
                                        {"label": "High", "value": "high"},
                                    ],
                                    placeholder="Select severity",
                                ),
                            ],
                            width=4,
                        ),
                    ],
                    className="g-2",
                ),

                dbc.Button("Submit Override Request", id="submit-override-btn", color="warning", className="mt-3"),
                html.Div(id="override-status", className="mt-3"),

                html.Hr(),
                html.H5("Override History (placeholder)"),
                html.Div(id="override-history"),
            ]
        )
    )