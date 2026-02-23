from dash import html, dcc
import dash_bootstrap_components as dbc

def layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H3("Admin"),
                html.P(
                    "This page will manage reference configuration: allocations (space), budgets, "
                    "grade entitlements, stand limits, etc. For now, it just shows seed data."
                ),

                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Label("View reference data section"),
                                dcc.Dropdown(
                                    id="admin-section-dd",
                                    options=[
                                        {"label": "Facias", "value": "facias"},
                                        {"label": "Grades", "value": "grades"},
                                        {"label": "Departments", "value": "departments"},
                                        {"label": "Categories", "value": "categories"},
                                        {"label": "Stand Limits", "value": "stand_limits"},
                                        {"label": "Branches", "value": "branches"},
                                    ],
                                    value="facias",
                                    clearable=False,
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            dbc.Button("Refresh", id="admin-refresh-btn", color="secondary"),
                            width=2,
                        ),
                    ],
                    className="g-2 align-items-end",
                ),

                html.Hr(),
                html.Div(id="admin-output"),
            ]
        )
    )
