from dash import Dash, dcc, html
import dash_bootstrap_components as dbc

from range_control_platform.controllers.admin_controller import register_admin_callbacks
from range_control_platform.controllers.plan_controller import register_plan_callbacks
from range_control_platform.controllers.ref_data_controller import register_ref_data_callbacks
from range_control_platform.controllers.report_controller import register_report_callbacks
from range_control_platform.controllers.router import register_router
from range_control_platform.controllers.validation_controller import register_validation_callbacks
from range_control_platform.data.repositories import build_reference_data_repository
from range_control_platform.data.seed import seed_reference_data
from range_control_platform.views.layout import app_shell


def create_app():
    reference_data_repo = build_reference_data_repository()
    initial_load_error = None
    try:
        initial_ref_data = reference_data_repo.load_reference_data()
        initial_ref_data["_meta"] = {"source": "jd" if initial_ref_data else "local"}
    except Exception as exc:
        initial_load_error = str(exc)
        initial_ref_data = seed_reference_data()
        initial_ref_data["_meta"] = {
            "source": "seed-fallback",
            "load_error": initial_load_error,
        }
    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
    )
    app.layout = app_shell(
        html.Div(
            [
                dcc.Location(id="url"),
                dcc.Store(id="ref-data-error-store", data=initial_load_error),
                html.Div(id="page-content"),
            ]
        ),
        initial_ref_data=initial_ref_data,
    )
    register_router(app)
    register_ref_data_callbacks(app, reference_data_repo)
    register_admin_callbacks(app)
    register_plan_callbacks(app)
    register_validation_callbacks(app)
    register_report_callbacks(app)
    return app


if __name__ == "__main__":
    create_app().run_server(debug=True)
