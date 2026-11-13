from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC019(TCBase):
    ALERT_MESSAGE = "최대 5개까지 선택할 수 있습니다."

    def setUp(self):
        super().init()

    def test_cannot_select_more_than_five_region_conditions(self):
        """지역 조건을 5개 선택한 뒤 추가 선택 시 최대 개수 알림을 표시한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-0']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-0']"),
            "지역 탭",
        )
        self.sleep()

        panel = "//div[@role='tabpanel' and @id='panel-0']"
        counter = (
            By.XPATH,
            f"{panel}//div[contains(@class, 'filter-header__counter')]",
        )

        # 사전 조건: 제주 → 서귀포시로 이동한 뒤 하위 지역 5개를 선택한다.
        self.click_element(
            self.region_button_locator(panel, "제주"),
            "'제주' 지역",
        )
        self.sleep()
        self.click_element(
            self.region_button_locator(panel, "서귀포시"),
            "'서귀포시' 지역",
        )
        self.sleep()

        condition_names = (
            "강정동",
            "남원읍",
            "대정읍",
            "대포동",
            "도순동",
            "동홍동"
        )

        for name in condition_names[:5]:
            self.click_element(
                self.region_button_locator(panel, name),
                f"'{name}' 지역 조건",
            )
            self.sleep()

        self.assert_element_text(counter, "5/5", "5개 선택 상태의 지역 조건 개수")

        # 테스트 절차: 6번째 지역 조건을 선택한다.
        sixth_name = condition_names[-1]
        self.highlight_element(
            self.region_button_locator(panel, sixth_name),
            "6번째 지역 조건 선택",
        )
        self.sleep()
        self.click_element(
            self.region_button_locator(panel, sixth_name),
            f"6번째 '{sixth_name}' 지역 조건",
        )

        # 기대 결과: 알림이 표시되고 6번째 조건은 추가되지 않는다.
        alert = self.wait.until(self.get_alert)
        self.assertEqual(alert.text, self.ALERT_MESSAGE, "알림 문구가 다릅니다.")
        
        self.sleep()
        alert.dismiss()

    def tearDown(self):
        super().dispose()
