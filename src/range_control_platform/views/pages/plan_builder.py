from dash import dcc, html
import dash_bootstrap_components as dbc


def layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3("Plan Builder"),
                html.P(
                    "Build a branch plan from the BigQuery-backed store, allocation, and stand-library data."
                ),
                html.Div(id="plan-status", className="mb-3"),

                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("Saved Plan Snapshots"),
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
                            width=2,
                            className="d-flex align-items-end",
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Delete Selected Plan",
                                id="plan-delete-btn",
                                color="danger",
                                className="w-100",
                                disabled=True,
                            ),
                            width=2,
                            className="d-flex align-items-end",
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Unload Current Plan",
                                id="plan-unload-btn",
                                color="warning",
                                outline=True,
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
                                dbc.Label("Plan Name"),
                                dcc.Input(
                                    id="plan-name-input",
                                    type="text",
                                    placeholder="Enter a plan alias",
                                    persistence=True,
                                    persistence_type="session",
                                    style={"width": "100%"},
                                ),
                            ],
                            width=12,
                        ),
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
                                dbc.Label("Stand From Library"),
                                dcc.Dropdown(
                                    id="stand-library-dd",
                                    placeholder="Select a stand",
                                    disabled=True,
                                    persistence=True,
                                    persistence_type="session",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                dbc.Label("Quantity To Add"),
                                dcc.Input(
                                    id="stand-qty",
                                    type="number",
                                    min=1,
                                    step=1,
                                    value=1,
                                    disabled=True,
                                    persistence=True,
                                    persistence_type="session",
                                    style={"width": "100%"},
                                ),
                            ],
                            width=2,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Add Stand",
                                id="add-stand-btn",
                                color="secondary",
                                className="w-100",
                                disabled=True,
                            ),
                            width=2,
                            className="d-flex align-items-end",
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Clear Stands",
                                id="clear-stands-btn",
                                color="light",
                                className="w-100",
                                disabled=True,
                            ),
                            width=2,
                            className="d-flex align-items-end",
                        ),
                    ],
                    className="g-2",
                ),

                html.Hr(),

                html.Div(id="plan-summary"),

                html.Hr(),

                html.H5("Selected Stands"),
                html.Div(id="selected-stands-table"),

                html.Hr(),

                dbc.Button(
                    "Save Plan Snapshot",
                    id="plan-save-btn",
                    color="primary",
                    disabled=True,
                ),
            ]
        )
    )
