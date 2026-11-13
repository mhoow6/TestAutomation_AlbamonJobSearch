from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC061(TCBase):
    """근무시간 선택 방식을 목록에서 직접 선택으로 전환하는지 검증한다."""

    def setUp(self):
        super().init()

    def test_select_custom_work_time_option(self):
        """목록에서 선택을 해제하고 근무시간 직접 선택을 선택한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-2']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            "근무기간 탭",
        )
        self.sleep()

        list_option = (
            By.XPATH,
            "//label[.//span[normalize-space()='목록에서 선택']]"
            "//input[@type='radio' and @name='workTimeType']",
        )
        direct_option = (
            By.XPATH,
            "//label[.//span[normalize-space()='직접선택']]"
            "//input[@type='radio' and @name='workTimeTypeDirect']",
        )
        direct_option_click = (
            By.XPATH,
            "//label[.//span[normalize-space()='직접선택']]"
            "[.//input[@type='radio' and @name='workTimeTypeDirect']]",
        )

        # 사전 조건: 근무시간 목록에서 선택이 선택되어 있어야 한다.
        self.wait_for_selected(list_option, "근무시간 목록에서 선택")

        self.click_element(direct_option_click, "근무시간 '직접선택' 선택")
        self.wait_for_selected(direct_option, "근무시간 직접선택")
        self.wait_for_not_selected(list_option, "해제된 근무시간 목록에서 선택")
        self.assert_for_not_selected(
            list_option,
            "'직접선택' 선택 후 '목록에서 선택'이 선택되어 있습니다.",
            highlight_locator=direct_option_click,
        )
        self.sleep()

    def tearDown(self):
        super().dispose()
