from starlette.middleware.base import BaseHTTPMiddleware

from app.core.tracing.tracer import Tracer


class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        trace_id = Tracer.start_trace()

        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id

        return response
