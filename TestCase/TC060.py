import re

from Module.TCBase import TCBase
from TestCase.TC054 import TC054


class TC060(TCBase):
    """오전 파트와 오후~저녁 파트를 함께 선택했을 때 조건을 검증한다."""

    TIME_PARTS = (
        ("오전 파트", "AM"),
        ("오후~저녁 파트", "PM_TO_EVENING"),
    )
    ALLOWED_TIME_RANGES = ((6 * 60, 12 * 60),)
    EVENING_TIME = 18 * 60

    # TC054의 목록 조회 흐름만 재사용하고, TC054의 테스트 메서드는 상속하지 않는다.
    _run_work_time_test = TC054._run_work_time_test

    def setUp(self):
        super().init()

    @classmethod
    def _is_allowed_work_time(cls, work_time):
        """06:00~12:00과 겹치거나 18:00을 포함하는지 판정한다."""
        if TC054._is_allowed_work_time.__func__(cls, work_time):
            return True

        normalized = "".join(work_time.split())
        time_matches = re.findall(
            r"(?P<start>\d{1,2}:\d{2})~(?P<end>\d{1,2}:\d{2})",
            normalized,
        )
        for start_time, end_time in time_matches:
            start_hour, start_minute = map(int, start_time.split(":"))
            end_hour, end_minute = map(int, end_time.split(":"))
            start = start_hour * 60 + start_minute
            end = end_hour * 60 + end_minute
            if end <= start:
                end += 24 * 60

            if start <= cls.EVENING_TIME <= end:
                return True

        return False

    def test_apply_morning_and_morning_to_afternoon_work_time(self):
        """오전 또는 오후~저녁 시간대에 해당하는 공고만 조회되는지 확인한다."""
        self._run_work_time_test()

    def tearDown(self):
        super().dispose()
