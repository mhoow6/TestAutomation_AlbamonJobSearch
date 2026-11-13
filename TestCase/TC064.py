from TestCase.TC063 import TC063


class TC064(TC063):
    """시작시간보다 종료시간이 빠른 직접선택 근무시간을 검증한다."""

    ALLOWED_TIME_RANGES = (
        (6 * 60, 24 * 60),
        (0, 5 * 60 + 30),
    )
    START_TIME = "06:00"
    END_TIME = "05:30"

    def test_select_direct_work_time_range(self):
        """직접선택에서 06:00~05:30을 선택하고 해당 공고만 조회되는지 확인한다."""
        self._run_direct_work_time_range()
