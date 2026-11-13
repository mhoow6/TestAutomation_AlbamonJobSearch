from TestCase.TC063 import TC063


class TC065(TC063):
    """근무시간 협의 제외를 해제했을 때 시간협의 공고를 포함하는지 검증한다."""

    INCLUDE_NEGOTIABLE_TIME = True
    NEGOTIATION_EXCLUDED_BEFORE = True
    NEGOTIATION_EXCLUDED_AFTER = False

    @classmethod
    def _is_allowed_work_time(cls, work_time):
        return work_time == "시간협의" or super()._is_allowed_work_time(work_time)

    def test_select_direct_work_time_range(self):
        """00:00~06:00 공고와 시간협의 공고가 함께 조회되는지 확인한다."""
        self._run_direct_work_time_range()
