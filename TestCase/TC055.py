from Module.TCBase import TCBase
from TestCase.TC054 import TC054


class TC055(TCBase):
    """근무시간에서 오전·저녁 파트를 복수 선택했을 때 조건을 검증한다."""

    TIME_PARTS = (("오전 파트", "AM"), ("저녁 파트", "EVENING"))
    ALLOWED_TIME_RANGES = (
        (6 * 60, 12 * 60),
        (18 * 60, 24 * 60),
    )

    # TC054의 공통 실행 흐름만 재사용하고, TC054의 테스트 메서드는 상속하지 않는다.
    _run_work_time_test = TC054._run_work_time_test

    def setUp(self):
        super().init()

    @classmethod
    def _is_allowed_work_time(cls, work_time):
        return TC054._is_allowed_work_time.__func__(cls, work_time)

    def test_apply_multiple_work_time(self):
        """오전·저녁 파트와 겹치는 공고만 조회되는지 확인한다."""
        self._run_work_time_test()

    def tearDown(self):
        super().dispose()
