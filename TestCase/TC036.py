from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC036(TCBase):
    """업직종 조건을 10개 초과 선택할 때 알림을 확인한다."""

    ALERT_MESSAGE = "최대 10개까지 선택할 수 있습니다."
    SELECTED_CLASS = (
        "FilterListColumn_filter-list__column-button--selected__2niWt"
    )
    CONDITIONS = (
        "입시·보습학원",
        "외국어·어학원",
        "독서·논술·스피치학원",
        "컴퓨터·정보통신",
        "요가·필라테스 강사",
        "피트니스 트레이너",
        "레져스포츠 강사",
        "예체능 강사",
        "유아·유치원",
        "등하원·승하차도우미",
    )

    def setUp(self):
        super().init()

    def test_cannot_select_more_than_ten_job_conditions(self):
        """10개 선택 후 11번째 업직종 조건을 선택하면 알림을 검증한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-1']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-1']"),
            "업직종 탭",
        )
        self.sleep()

        self.click_element(
            (By.XPATH, "//li[@role='button' and normalize-space(.)='교육·강사']"),
            "'교육·강사' 대분류",
        )
        self.sleep()

        for condition_name in self.CONDITIONS:
            condition_locator = (
                By.XPATH,
                f"//li[@role='button' and normalize-space(.)={condition_name!r}]",
            )
            self.click_element(condition_locator, f"'{condition_name}' 조건")
            self.wait_for_selected(
                condition_locator,
                f"'{condition_name}' 조건",
                self.SELECTED_CLASS,
            )
            self.sleep()

        counter_locator = (
            By.XPATH,
            "//div[@role='tabpanel' and @id='panel-1']"
            "//div[contains(@class, 'filter-header__counter')]",
        )
        self.assert_element_text(counter_locator, "10/10", "10개 선택 상태의 업직종 조건 개수")

        # 테스트 절차: 11번째 업직종 조건을 선택한다.
        extra_condition = (
            By.XPATH,
            "//li[@role='button' and normalize-space(.)='방문·학습지']",
        )
        self.highlight_element(extra_condition, "11번째 업직종 조건 방문·학습지")
        self.click_element(extra_condition, "11번째 '방문·학습지' 조건")

        # 기대 결과: 최대 선택 개수 초과 알림이 표시된다.
        alert = self.wait.until(self.get_alert)
        self.assertEqual(
            alert.text,
            self.ALERT_MESSAGE,
            "최대 업직종 조건 초과 알림 문구가 다릅니다.",
        )
        self.sleep()
        alert.dismiss()

        # 기대 결과: 11번째 조건은 추가되지 않고 10개 상태가 유지된다.
        self.assert_element_text(counter_locator, "10/10", "알림 후 업직종 조건 개수")

    def tearDown(self):
        super().dispose()
