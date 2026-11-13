import re

from Module.TCBase import TCBase
from TestCase.TC054 import TC054


class TC056(TCBase):
    """구간대 조건을 하나씩 선택했을 때 조건이 적용되는지 검증한다."""

    TIME_PARTS = (("오전~오후 파트", "AM_TO_PM"),)
    NOON_TIME = 12 * 60
    SINGLE_TIME_PART_CASES = (
        ((("오전~오후 파트", "AM_TO_PM"),), 12 * 60),
        ((("오후~저녁 파트", "PM_TO_EVENING"),), 18 * 60),
        ((("저녁~새벽 파트", "EVENING_TO_DAWN"),), 0),
        ((("새벽~오전 파트", "DAWN_TO_AM"),), 6 * 60),
    )
    CURRENT_BOUNDARY_TIME = None

    # TC054의 목록 조회 흐름만 재사용하고, TC054의 테스트 메서드는 상속하지 않는다.
    _run_work_time_test = TC054._run_work_time_test

    def setUp(self):
        super().init()

    @classmethod
    def _is_allowed_work_time(cls, work_time):
        """근무시간이 오전에서 오후로 이어져 12:00을 포함하는지 판정한다."""
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

            boundary_time = getattr(cls, "CURRENT_BOUNDARY_TIME", None)
            if boundary_time is None:
                boundary_time = cls.NOON_TIME
            if any(start <= boundary <= end for boundary in (boundary_time, boundary_time + 24 * 60)):
                return True

        return False

    def test_apply_morning_to_afternoon_work_time(self):
        """각 구간대 조건을 하나씩 선택해 해당 공고만 조회되는지 확인한다."""
        original_time_parts = self.TIME_PARTS
        original_boundary_time = type(self).CURRENT_BOUNDARY_TIME
        try:
            for time_parts, boundary_time in self.SINGLE_TIME_PART_CASES:
                self.TIME_PARTS = time_parts
                type(self).CURRENT_BOUNDARY_TIME = boundary_time
                self._run_work_time_test()
        finally:
            self.TIME_PARTS = original_time_parts
            type(self).CURRENT_BOUNDARY_TIME = original_boundary_time

    def tearDown(self):
        super().dispose()
