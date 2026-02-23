from dash import Input, Output, html

def register_admin_callbacks(app):
    @app.callback(
        Output("admin-output", "children"),
        Input("ref-data-store", "data"),
        Input("admin-section-dd", "value"),
    )
    def show_reference_data(ref_data, section):
        if not ref_data:
            return html.Div("No reference data loaded yet.")

        data = ref_data.get(section)

        # Pretty rendering for dict/list/other
        if isinstance(data, dict):
            return html.Ul([html.Li(f"{k}: {v}") for k, v in data.items()])
        if isinstance(data, list):
            return html.Ul([html.Li(str(x)) for x in data])

        return html.Pre(str(data))
