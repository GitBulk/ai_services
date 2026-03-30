from contextvars import ContextVar

trace_id_ctx = ContextVar("trace_id", default=None)
span_id_ctx = ContextVar("span_id", default=None)
