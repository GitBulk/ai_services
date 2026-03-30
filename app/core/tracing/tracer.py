from app.core.time.service import DateTimeService
from app.core.tracing.context import span_id_ctx, trace_id_ctx
from app.core.tracing.span import Span, generate_id


# Usage:
# span = Tracer.start_span("retriever")
# results = retriever.search(query)
# Tracer.end_span(span)
class Tracer:
    @staticmethod
    def start_trace():
        trace_id = generate_id()
        trace_id_ctx.set(trace_id)
        return trace_id

    @staticmethod
    def start_span(name: str) -> Span:
        trace_id = trace_id_ctx.get()
        parent_id = span_id_ctx.get()

        span_id = generate_id()
        span_id_ctx.set(span_id)

        now = DateTimeService.now()

        return Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_id=parent_id,
            name=name,
            start_time=now.epoch_ms,
        )

    @staticmethod
    def end_span(span: Span):
        now = DateTimeService.now()
        span.finish(now.epoch_ms)

        # log ra (hoặc gửi sang ELK sau này)
        print(
            {
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "parent_id": span.parent_id,
                "name": span.name,
                "duration_ms": span.end_time - span.start_time,
            }
        )
