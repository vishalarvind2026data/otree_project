"""
Custom in-website routes for oTree:
- /api/run_bots: API to run bots and compile econometrics
- /run_bots: User-friendly bot simulation interface
- /report: Scientific econometric report with all 5 figures & tables
"""

from starlette.routing import Route
from starlette.endpoints import HTTPEndpoint
from starlette.responses import JSONResponse
import otree.views.cbv as cbv
import report_helper


import asyncio


async def api_run_bots(request):
    """API endpoint to trigger simulation and update analytics."""
    if request.method == 'POST':
        try:
            data = await request.json()
        except Exception:
            data = {}
    else:
        data = dict(request.query_params)

    n = int(data.get('num_bots', 30))
    cfg = str(data.get('session_config', 'modal_shift'))
    preset = str(data.get('preset', 'default'))

    res = await asyncio.to_thread(
        report_helper.execute_bot_simulation_and_pipeline, n, cfg, preset
    )
    return JSONResponse(res)


class RunBotsView(cbv.AdminView):
    url_pattern = '/run_bots'

    def get_template_name(self):
        return 'run_bots.html'


class GlobalReportView(cbv.AdminView):
    url_pattern = '/report'

    def get_template_name(self):
        return 'report.html'

    def vars_for_template(self):
        source = 'bots'
        if hasattr(self, 'request') and self.request:
            source = self.request.query_params.get('source', 'bots')
        return dict(
            report_data=report_helper.get_report_data(source),
            current_source=source
        )


def register(app):
    routes_to_add = [
        Route('/api/run_bots', endpoint=api_run_bots, methods=['GET', 'POST'], name='api_run_bots'),
        Route('/run_bots', endpoint=RunBotsView, name='RunBotsView'),
        Route('/report', endpoint=GlobalReportView, name='GlobalReportView'),
    ]
    for r in routes_to_add:
        if not any(hasattr(existing, 'path') and existing.path == r.path for existing in app.routes):
            app.routes.insert(0, r)
