from dash import html, dcc
import dash_bootstrap_components as dbc
from range_control_platform.config import settings

NAV_ITEMS = [
    ("Home", "/"),
    ("Plan Builder", "/plan"),
    ("Validation", "/validation"),
    ("Overrides", "/overrides"),
    ("Reports", "/reports"),
    ("Admin", "/admin"),
]

def build_nav():
    return dbc.Nav([
        dbc.NavLink(label, href=path, active="exact")
        for (label, path) in NAV_ITEMS
    ],
    vertical=True,
    pills=True,
    className="pt-2"
    )

def app_shell(page_container, initial_ref_data=None):
    return dbc.Container(
        fluid=True,
        children=[
            #Top Bar
            dbc.Navbar(
                dbc.Container(
                    [
                        dbc.NavbarBrand(settings.APP_NAME),
                        dbc.Badge(f"ENV: {settings.ENV}", className="ms-auto")
                    ]
                ),
                color="dark",
                dark=True,
                className="mt-3",
            ),
            dbc.Alert(
                id="ref-data-alert",
                is_open=False,
                color="warning",
                className="mt-2 mb-2",
            ),
            # Global State Stores
            dcc.Store(id="ref-data-store", data=initial_ref_data),
            dcc.Store(id="plan-draft-store"),
            dcc.Store(id="plan-store"),
            dcc.Store(id="validation-store"),
            dcc.Store(id="audit-store"),

            dbc.Row(
                [
                    dbc.Col(build_nav(), width=2),
                    dbc.Col(page_container, width=10),
                ],
                className="g-3"
            )
        ]
    )
