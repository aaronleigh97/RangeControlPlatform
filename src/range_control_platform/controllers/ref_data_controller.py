from dash import Input, Output

from range_control_platform.data.seed import seed_reference_data

def register_ref_data_callbacks(app, reference_data_repo):
    @app.callback(
        Output("ref-data-store", "data"),
        Output("ref-data-error-store", "data"),
        Input("admin-refresh-btn", "n_clicks"),
    )
    def load_reference_data(_n_clicks):
        try:
            ref_data = reference_data_repo.load_reference_data()
            ref_data["_meta"] = {"source": "jd" if ref_data else "local"}
            return ref_data, None
        except Exception as exc:
            ref_data = seed_reference_data()
            ref_data["_meta"] = {
                "source": "seed-fallback",
                "load_error": str(exc),
            }
            return ref_data, str(exc)

    @app.callback(
        Output("ref-data-alert", "children"),
        Output("ref-data-alert", "is_open"),
        Input("ref-data-error-store", "data"),
    )
    def show_reference_data_error(load_error):
        if not load_error:
            return "", False
        return f"Reference data fallback active. JD BigQuery load failed: {load_error}", True
