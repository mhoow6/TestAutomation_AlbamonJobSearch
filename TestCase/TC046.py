from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC046(TCBase):
    """근무요일 목록의 최대 선택 개수를 검증한다."""

    ALERT_MESSAGE = "최대 3개까지 선택할 수 있습니다."

    def setUp(self):
        super().init()

    def test_cannot_select_more_than_three_work_day_conditions(self):
        """근무요일 3개 선택 후 4번째 조건을 선택하면 최대 개수 알림을 표시한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-2']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            "근무기간 탭",
        )
        self.sleep()

        weekday_list_radio = (
            By.XPATH,
            "//input[@type='radio' and @name='dutyWeeks']",
        )
        self.wait_for_selected(weekday_list_radio, "근무요일 목록에서 선택")
        self.sleep()

        def weekday_locator(name):
            return (
                By.XPATH,
                f"//label[.//span[normalize-space()={name!r}]]"
                "//input[@type='checkbox' and @name='dutyWeeks']",
            )

        def weekday_click_locator(name):
            return (
                By.XPATH,
                f"//label[.//span[normalize-space()={name!r}]]"
                "//input[@type='checkbox' and @name='dutyWeeks']"
                "/ancestor::label[1]",
            )

        selected_weekdays = ("월~금", "월~토", "주말(토,일)")
        for weekday_name in selected_weekdays:
            self.click_element(
                weekday_click_locator(weekday_name),
                f"'{weekday_name}' 조건",
            )
            self.wait_for_selected(
                weekday_locator(weekday_name),
                f"'{weekday_name}' 조건",
            )
            self.sleep()

        weekday_panel = "//div[@role='tabpanel' and @id='panel-2']"
        weekday_counter = (
            By.XPATH,
            f"{weekday_panel}//div[contains(@class, 'filter-work-day__title-box__counter')]",
        )
        self.assert_element_text(weekday_counter, "(3/3)", "근무요일 조건 개수")

        fourth_weekday = "월~일"
        fourth_weekday_input = weekday_locator(fourth_weekday)
        self.highlight_element(
            weekday_click_locator(fourth_weekday),
            f"4번째 '{fourth_weekday}' 조건 선택",
        )
        self.click_element(
            weekday_click_locator(fourth_weekday),
            f"4번째 '{fourth_weekday}' 조건",
        )
        self.sleep()

        alert = self.wait.until(self.get_alert)
        self.assertEqual(alert.text, self.ALERT_MESSAGE, "알림 문구가 다릅니다.")
        alert.dismiss()
        self.wait_for_not_selected(
            fourth_weekday_input,
            f"초과 선택된 '{fourth_weekday}' 조건",
        )
        self.sleep(2)

    def tearDown(self):
        super().dispose()
