from dash import Input, Output
from range_control_platform.data.seed import seed_reference_data

def register_ref_data_callbacks(app):
    @app.callback(
        Output("ref-data-store", "data"),
        Input("admin-refresh-btn", "n_clicks"),
    )
    def load_reference_data(_n_clicks):
        # Always return latest seed snapshot for now.
        return seed_reference_data()
