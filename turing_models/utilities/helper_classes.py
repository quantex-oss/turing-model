from pydantic import BaseModel

from fundamental import ctx, PricingContext


class Base(BaseModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def api_data(self, **kw):
        ...

    def evaluation(self, *args, **kw):
        context = kw.pop('context', '')
        try:
            if context:
                ctx.context = context
        except Exception:
            pass
        scenario = PricingContext()
        request_id = kw.pop('request_id', '')
        if request_id:
            ctx.request_id = request_id

        pricing_context = kw.pop('pricing_context', '')
        self.api_data(**kw)
        if pricing_context:
            scenario.resolve(pricing_context)
            with scenario:
                return self._generate()
        else:
            return self._generate()

    def _generate(self):
        return getattr(self, "generate_data")()