from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC014(TCBase):
    URL = f"{TCBase.URL}&similarDongJoin=true"
    ALERT_MESSAGE = "묶음 해제 시 선택한 지역이 모두 초기화 됩니다. 해제하시겠습니까?"

    def setUp(self):
        super().init()

    def region_button_locator(self, panel, name):
        """지역명으로 시·도, 시·구·군 또는 동·읍·면 XPath를 생성한다."""
        return (
            By.XPATH,
            f"{panel}//li[@role='button' and normalize-space()={name!r}]",
        )

    def test_confirm_before_ungrouping_similar_dong(self):
        """지역 선택 후 유사동 묶기 해제 시 초기화 확인 알림을 표시한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-0']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-0']"),
            "지역 탭",
        )
        self.sleep()

        panel = (
            "//div[@role='tabpanel' and "
            ".//input[@name='group-similar']]"
        )
        similar_dong_checkbox = (
            By.XPATH,
            f"{panel}//input[@name='group-similar']",
        )
        similar_dong_label = (
            By.XPATH,
            f"{panel}//label[.//input[@name='group-similar']]",
        )

        # 사전 조건: 유사동 묶기 ON 상태에서 제주 → 서귀포시 → 강정동을 선택한다.
        self.wait_for_selected(
            similar_dong_checkbox,
            "사전 조건 유사동 묶기",
        )
        self.click_element(
            self.region_button_locator(panel, "제주"),
            "'제주' 시·도",
        )
        self.sleep()
        self.click_element(
            self.region_button_locator(panel, "서귀포시"),
            "'제주 서귀포시' 시·구·군",
        )
        self.sleep()
        self.click_element(
            self.region_button_locator(panel, "강정동"),
            "'제주 서귀포시 강정동' 동·읍·면",
        )
        self.sleep()

        self.assert_element_text(
            (
                By.XPATH,
                f"{panel}//div[contains(@class, 'filter-header__counter')]",
            ),
            "1/5",
            "선택 지역 조건 개수",
        )
        self.assert_element_text(
            (
                By.XPATH,
                "//div[contains(@class, 'selector-chips__list')]"
                "//button[contains(@class, 'selector-chips__chip')]",
            ),
            "강정동",
            "선택 지역 조건",
        )

        # 테스트 절차: 유사동 묶기 해제를 시도하고 native confirm 창을 확인한다.
        self.click_element(similar_dong_label, "유사동 묶기 해제")
        alert = self.wait.until(self.get_alert)
        self.assertEqual(alert.text, self.ALERT_MESSAGE, "알림 문구가 다릅니다.")
        self.sleep()

        # 테스트 후 조건이 초기화되지 않도록 취소하고 기존 선택 상태를 확인한다.
        alert.dismiss()
        self.wait_for_selected(
            similar_dong_checkbox,
            "알림 취소 후 유사동 묶기",
        )
        self.assert_element_text(
            (
                By.XPATH,
                f"{panel}//div[contains(@class, 'filter-header__counter')]",
            ),
            "1/5",
            "알림 취소 후 지역 조건 개수",
        )
        self.sleep()

    def tearDown(self):
        super().dispose()
