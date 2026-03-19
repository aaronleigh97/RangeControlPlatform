from dash import Input, Output, State, dcc, html, no_update
import dash_bootstrap_components as dbc
from dash import ctx

from range_control_platform.services.plan_service import (
    export_plan_snapshots_to_csv,
    load_latest_validation_status_by_plan_key,
    load_plan_snapshots,
    summarize_plan_snapshots,
)


def _build_count_table(title: str, rows: list[tuple[str, int]]):
    if not rows:
        return dbc.Col(
            dbc.Card(dbc.CardBody([html.H6(title), html.P("No data")]))
        )

    header = html.Thead(html.Tr([html.Th(title), html.Th("Count")]))
    body = html.Tbody([
        html.Tr([html.Td(label), html.Td(count)])
        for label, count in rows
    ])
    table = dbc.Table([header, body], bordered=False, hover=True, striped=True, size="sm")
    return dbc.Col(dbc.Card(dbc.CardBody([html.H6(title), table])), width=6)


def _build_recent_table(rows: list[dict], branch_grade_lookup=None, validation_lookup=None):
    if not rows:
        return html.P("No snapshots found.")
    branch_grade_lookup = branch_grade_lookup or {}
    validation_lookup = validation_lookup or {}

    headers = [
        "saved_at",
        "branch_id",
        "branch_grade",
        "facia",
        "department",
        "stand_count",
        "validation_status",
    ]
    thead = html.Thead(html.Tr([html.Th(h) for h in headers]))
    tbody = html.Tbody(
        [
            html.Tr([
                html.Td(row.get("saved_at", "")),
                html.Td(row.get("branch_id", "")),
                html.Td(branch_grade_lookup.get(row.get("branch_id"), "Unknown")),
                html.Td(row.get("facia", "")),
                html.Td(row.get("department", "")),
                html.Td(row.get("stand_count", "")),
                html.Td(
                    (validation_lookup.get(row.get("plan_key")) or {}).get("validation_status", "")
                ),
            ])
            for row in rows
        ]
    )
    return dbc.Table([thead, tbody], bordered=False, hover=True, striped=True, size="sm", responsive=True)

def _build_summary_output(
    summary: dict,
    current_branch_id=None,
    current_branch_grade=None,
    branch_grade_lookup=None,
    validation_lookup=None,
):
    metrics_items = [
        html.Li(f"Snapshot rows: {summary['total_snapshots']}"),
        html.Li(f"Unique plans (branch/facia/department): {summary['unique_plans']}"),
        html.Li(f"Latest saved snapshot: {summary['latest_saved_at'] or 'N/A'}"),
        html.Li(
            f"Stand count stats (min/avg/max): "
            f"{summary['stand_min']} / {summary['stand_avg']} / {summary['stand_max']}"
        ),
    ]
    if current_branch_id:
        metrics_items.append(
            html.Li(
                f"Current plan branch grade ({current_branch_id}): "
                f"{current_branch_grade or 'Unknown'}"
            )
        )

    metrics = html.Ul(metrics_items)

    breakdowns = dbc.Row(
        [
            _build_count_table("By Facia", summary.get("facia_counts", [])),
            _build_count_table("By Department", summary.get("department_counts", [])),
        ],
        className="g-2",
    )

    recent_section = dbc.Card(
        dbc.CardBody(
            [
                html.H6("Recent Snapshots (latest 10)"),
                _build_recent_table(
                    summary.get("recent_rows", []),
                    branch_grade_lookup=branch_grade_lookup,
                    validation_lookup=validation_lookup,
                ),
            ]
        ),
        className="mt-3",
    )

    return html.Div(
        [
            dbc.Card(dbc.CardBody([html.H5("Plan Snapshot Summary"), metrics])),
            html.Div(className="mt-3"),
            breakdowns,
            recent_section,
        ]
    )


def register_report_callbacks(app):
    @app.callback(
        Output("report-status", "children"),
        Output("report-status", "color"),
        Output("report-output", "children"),
        Output("report-download", "data"),
        Input("report-summary-btn", "n_clicks"),
        Input("report-csv-btn", "n_clicks"),
        Input("report-pdf-btn", "n_clicks"),
        State("plan-store", "data"),
        State("ref-data-store", "data"),
        prevent_initial_call=True,
    )
    def handle_reports(_summary_clicks, _csv_clicks, _pdf_clicks, current_plan, ref_data):
        triggered = ctx.triggered_id

        if triggered == "report-summary-btn":
            rows = load_plan_snapshots()
            if not rows:
                return (
                    "No saved plan snapshots found yet. Save a plan first.",
                    "warning",
                    html.Div("Nothing to summarize yet."),
                    no_update,
                )

            summary = summarize_plan_snapshots(rows)

            current_branch_id = (current_plan or {}).get("branch_id")
            current_branch_grade = None
            branch_grade_lookup = {}
            validation_lookup = load_latest_validation_status_by_plan_key()
            if ref_data:
                branches = ref_data.get("branches", [])
                branch_grade_lookup = {
                    b.get("branch_id"): b.get("grade")
                    for b in branches
                    if b.get("branch_id")
                }
            if current_branch_id and ref_data:
                branches = ref_data.get("branches", [])
                branch = next(
                    (b for b in branches if b.get("branch_id") == current_branch_id),
                    None,
                )
                current_branch_grade = (branch or {}).get("grade")

            output = _build_summary_output(
                summary,
                current_branch_id=current_branch_id,
                current_branch_grade=current_branch_grade,
                branch_grade_lookup=branch_grade_lookup,
                validation_lookup=validation_lookup,
            )
            return (
                f"Summary generated from {summary['total_snapshots']} snapshot row(s).",
                "success",
                output,
                no_update,
            )

        if triggered == "report-csv-btn":
            rows = load_plan_snapshots()
            if not rows:
                return (
                    "No saved plan data exists yet. Save a plan first.",
                    "warning",
                    no_update,
                    no_update,
                )
            csv_path = export_plan_snapshots_to_csv(rows)

            return (
                f"CSV export ready: {csv_path.name}",
                "success",
                no_update,
                dcc.send_file(str(csv_path), filename="Built_Plans.csv"),
            )

        if triggered == "report-pdf-btn":
            return (
                "PDF export is not implemented yet. Use Generate Summary or Export CSV.",
                "secondary",
                no_update,
                no_update,
            )

        return no_update, no_update, no_update, no_update
