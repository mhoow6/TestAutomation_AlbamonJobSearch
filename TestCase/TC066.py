from TestCase.TC063 import TC063


class TC066(TC063):
    """시간 협의 제외를 선택했을 때 시간 협의 공고가 제외되는지 검증한다."""

    NEGOTIATION_EXCLUDED_BEFORE = False
    NEGOTIATION_EXCLUDED_AFTER = True
    NEGOTIATION_TRANSITION_WAIT = 2

    def test_select_direct_work_time_range(self):
        """해제된 협의 제외를 선택하고 00:00~06:00 공고만 조회되는지 확인한다."""
        self._run_direct_work_time_range()
