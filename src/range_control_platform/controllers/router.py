from dash import Input, Output, html

from range_control_platform.views.pages import (
    admin,
    home,
    overrides,
    plan_builder,
    reports,
    validation,
)

def register_router(app):
    @app.callback(
        Output("page-content", "children"),
        Input("url", "pathname"),
    )
    def route(pathname: str):
        match pathname:
            case "/":
                return home.layout()
            case "/plan":
                return plan_builder.layout()
            case "/validation":
                return validation.layout()
            case "/overrides":
                return overrides.layout()
            case "/reports":
                return reports.layout()
            case "/admin":
                return admin.layout()
            case _:
                return html.Div("404 - Page not found")