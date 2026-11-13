import re

from Module.TCBase import TCBase
from TestCase.TC054 import TC054


class TC058(TCBase):
    """근무시간에서 풀타임(8시간 이상) 조건을 선택했을 때 적용을 검증한다."""

    TIME_PARTS = (("풀타임(8시간 이상)", "FULL_TIME"),)
    MINIMUM_WORK_MINUTES = 8 * 60

    # TC054의 목록 조회 흐름만 재사용하고, TC054의 테스트 메서드는 상속하지 않는다.
    _run_work_time_test = TC054._run_work_time_test

    def setUp(self):
        super().init()

    @classmethod
    def _is_allowed_work_time(cls, work_time):
        """근무시간 중 하나라도 8시간 이상인지 판정한다."""
        normalized = "".join(work_time.split())
        time_matches = re.findall(
            r"(?P<start>\d{1,2}:\d{2})~(?P<end>\d{1,2}:\d{2})",
            normalized,
        )
        if not time_matches:
            return False

        for start_time, end_time in time_matches:
            start_hour, start_minute = map(int, start_time.split(":"))
            end_hour, end_minute = map(int, end_time.split(":"))
            start = start_hour * 60 + start_minute
            end = end_hour * 60 + end_minute
            if end <= start:
                end += 24 * 60

            if end - start >= cls.MINIMUM_WORK_MINUTES:
                return True

        return False

    def test_apply_full_time_work_time(self):
        """8시간 이상 근무하는 공고만 조회되는지 확인한다."""
        self._run_work_time_test()

    def tearDown(self):
        super().dispose()
