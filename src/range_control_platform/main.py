from dash import Dash, dcc, html
import dash_bootstrap_components as dbc

from range_control_platform.controllers.admin_controller import register_admin_callbacks
from range_control_platform.controllers.plan_controller import register_plan_callbacks
from range_control_platform.controllers.ref_data_controller import register_ref_data_callbacks
from range_control_platform.controllers.report_controller import register_report_callbacks
from range_control_platform.controllers.router import register_router
from range_control_platform.controllers.validation_controller import register_validation_callbacks
from range_control_platform.views.layout import app_shell


def create_app():
    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
    )
    app.layout = app_shell(
        html.Div(
            [
                dcc.Location(id="url"),
                html.Div(id="page-content"),
            ]
        )
    )
    register_router(app)
    register_ref_data_callbacks(app)
    register_admin_callbacks(app)
    register_plan_callbacks(app)
    register_validation_callbacks(app)
    register_report_callbacks(app)
    return app
