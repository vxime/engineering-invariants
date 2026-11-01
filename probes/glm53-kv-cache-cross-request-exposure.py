"""Minimal state-machine model of the SGLang PD-disaggregation abort gap.

Models Req.set_finish_with_abort() / finished() / update_finish_state() as
described in the article (SGLang @ 8f3d694, python/sglang/srt/managers/
schedule_batch.py L2053-2072, L1479-1481, L1842-1848). NOT the real SGLang
runtime — a ~30-line model of the state-transition ordering that let an
aborted request pass prefill admission before PR #38935.
"""
FINISH_ABORT = ("abort", 400, "AbortError")


class Req:
    def __init__(self):
        self.origin_input_ids = list(range(681281))  # long prompt
        self.to_finish = None
        self.finished_reason = None

    def set_finish_with_abort(self):
        self.origin_input_ids = [0]  # 1-token placeholder to skip prefill
        self.to_finish = FINISH_ABORT

    def finished(self):
        return self.finished_reason is not None

    def update_finish_state(self):
        if self.to_finish:
            self.finished_reason = self.to_finish
            self.to_finish = None


def prefill_admission(req):
    # Admission gate as it stood before PR #38935: checks finished() only.
    return not req.finished()


req = Req()
req.set_finish_with_abort()

# The abort IS recorded — but finished() still reads the old field.
assert req.to_finish is not None, "abort reason must be recorded"
admitted = prefill_admission(req)
print(f"after set_finish_with_abort: finished()={req.finished()}, admitted={admitted}")
assert admitted is True, "pre-#38935 admission lets the aborted request through"

# Only after the state migration does the gate see it.
req.update_finish_state()
assert req.finished() is True
assert prefill_admission(req) is False
print("PASS: abort in to_finish does not stop admission until update_finish_state() runs")
