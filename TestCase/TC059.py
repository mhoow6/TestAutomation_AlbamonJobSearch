import re

from Module.TCBase import TCBase
from TestCase.TC054 import TC054
from TestCase.TC058 import TC058


class TC059(TCBase):
    """풀타임 조건과 새벽 파트를 함께 선택했을 때 조건을 검증한다."""

    TIME_PARTS = (
        ("풀타임(8시간 이상)", "FULL_TIME"),
        ("새벽 파트", "DAWN"),
    )
    MINIMUM_WORK_MINUTES = TC058.MINIMUM_WORK_MINUTES
    DAWN_RANGE = (0, 6 * 60)

    # TC054의 목록 조회 흐름만 재사용하고, TC054의 테스트 메서드는 상속하지 않는다.
    _run_work_time_test = TC054._run_work_time_test

    def setUp(self):
        super().init()

    @classmethod
    def _is_allowed_work_time(cls, work_time):
        """8시간 이상이거나 00:00~06:00과 겹치는 근무시간인지 판정한다."""
        if TC058._is_allowed_work_time.__func__(cls, work_time):
            return True

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

            dawn_start, dawn_end = cls.DAWN_RANGE
            for day_offset in (0, 24 * 60):
                selected_start = dawn_start + day_offset
                selected_end = dawn_end + day_offset
                if start < selected_end and end > selected_start:
                    return True

        return False

    def test_apply_full_time_and_dawn_work_time(self):
        """풀타임 또는 새벽 시간대에 해당하는 공고만 조회되는지 확인한다."""
        self._run_work_time_test()

    def tearDown(self):
        super().dispose()
