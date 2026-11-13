from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC041(TCBase):
    """근무기간 조건을 6개 초과 선택할 때 알림을 확인한다."""

    ALERT_MESSAGE = "최대 6개까지 선택할 수 있습니다."
    DURATION_CONDITIONS = (
        "하루(1일)",
        "1주일이하",
        "1주일~1개월",
        "1개월~3개월",
        "3개월~6개월",
        "6개월~1년",
    )

    def setUp(self):
        super().init()

    def test_cannot_select_more_than_six_duration_conditions(self):
        """근무기간 6개 선택 후 1년이상을 선택하면 알림을 검증한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-2']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            "근무기간 탭",
        )
        self.sleep()

        panel = "//div[@role='tabpanel' and @id='panel-2']"
        for condition_name in self.DURATION_CONDITIONS:
            condition_locator = (
                By.XPATH,
                f"{panel}//*[normalize-space(.)={condition_name!r}]",
            )
            self.click_element(condition_locator, f"'{condition_name}' 조건")
            self.sleep()

        counter_locator = (
            By.XPATH,
            f"{panel}//div[contains(@class, 'filter-toggle__title-box__counter')]",
        )
        self.assert_element_text(counter_locator, "(6/6)", "6개 선택 상태의 근무기간 조건 개수")

        # 사전 조건: 공고 목록을 리스트 펼쳐 보기로 전환한다.
        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "공고 리스트 그리드뷰 전환",
        )

        # 테스트 절차: 7번째 근무기간 조건을 선택한다.
        extra_condition = (
            By.XPATH,
            f"{panel}//*[normalize-space(.)='1년이상']",
        )
        self.click_element(extra_condition, "7번째 '1년이상' 조건")
        self.sleep(2)

        alert = self.wait.until(self.get_alert)
        self.assertEqual(
            alert.text,
            self.ALERT_MESSAGE,
            "최대 근무기간 조건 초과 알림 문구가 다릅니다.",
        )
        alert.dismiss()

        # 초과 선택 후에도 기존 6개 조건만 유지되어야 한다.
        self.assert_element_text(counter_locator, "(6/6)", "알림 후 근무기간 조건 개수")

    def tearDown(self):
        super().dispose()
