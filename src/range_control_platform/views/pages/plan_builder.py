from dash import dcc, html
import dash_bootstrap_components as dbc


def layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3("Plan Builder"),
                html.P("Build a new plan, or load a previously saved local snapshot."),

                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Saved Plans (local CSV)"),
                                dcc.Dropdown(
                                    id="saved-plan-dd",
                                    placeholder="Select a saved plan to load",
                                    persistence=True,
                                    persistence_type="session",
                                ),
                            ],
                            width=9,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Load Selected Plan",
                                id="plan-load-btn",
                                color="secondary",
                                className="w-100",
                                disabled=True,
                            ),
                            width=3,
                            className="d-flex align-items-end",
                        ),
                    ],
                    className="g-2",
                ),

                html.Hr(),

                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Facia"),
                                dcc.Dropdown(
                                    id="facia-dd",
                                    placeholder="Select a Facia",
                                    persistence=True,
                                    persistence_type="session",
                                ),
                            ],
                            width=4,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Branch"),
                                dcc.Dropdown(
                                    id="branch-dd",
                                    placeholder="Select a Branch",
                                    disabled=True,
                                    persistence=True,
                                    persistence_type="session",
                                ),
                            ],
                            width=4,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Department"),
                                dcc.Dropdown(
                                    id="dept-dd",
                                    placeholder="Select a Department",
                                    disabled=True,
                                    persistence=True,
                                    persistence_type="session",
                                ),
                            ],
                            width=4,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Planned Stand Count"),
                                dcc.Input(
                                    id="stand-count",
                                    type="number",
                                    min=0,
                                    step=1,
                                    value=0,
                                    disabled=True,
                                    persistence=True,
                                    persistence_type="session",
                                    style={"width": "100%"},
                                ),
                            ],
                            width=4,
                        ),
                    ],
                    className="g-2",
                ),

                html.Hr(),

                dbc.Button(
                    "Create / Update Plan",
                    id="plan-save-btn",
                    color="primary",
                    disabled=True,
                ),
                html.Div(id="plan-status", className="mt-3"),
            ]
        )
    )
