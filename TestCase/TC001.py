from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC001(TCBase):

    def setUp(self):
        super().init()

    def test_reset_search_conditions(self):
        """조건 선택 후 초기화하면 선택 조건과 조건 수가 제거되는지 확인한다."""
        super().load()

        # 사전조건: 업직종 탭이 선택되지 않았으면 선택한다.
        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-1']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-1']"),
            "업직종 탭",
        )
        self.sleep()

        # 사전조건: 업직종 대분류 중 '교육·강사'를 선택한다.
        self.click_element(
            (By.XPATH, "//li[@role='button' and @id='category-A000']"),
            "'교육·강사' 대분류",
        )
        self.sleep()

        # 사전조건: 업직종 조건 중 '교육·강사 전체'를 선택한다.
        education_locator = (
            By.XPATH,
            "//li[@role='button' and @id='part-A000']",
        )
        education_selected_class = (
            "FilterListColumn_filter-list__column-button--selected__2niWt"
        )
        self.click_element(education_locator, "'교육·강사 전체' 조건")
        self.wait_for_selected(
            education_locator,
            "'교육·강사 전체' 조건",
            education_selected_class,
        )
        self.sleep()

        # 사전조건: 근무기간 탭이 선택되지 않았다면 먼저 선택한다.
        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-2']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            "근무기간 탭",
        )
        self.sleep()

        # 사전조건: 근무기간 조건 중 '하루(1일)'을 선택한다.
        duration_input_locator = (
            By.XPATH,
            "//input[@type='checkbox' and @name='dutyTerms' and @value='ONE_DAY']",
        )
        duration_click_locator = (
            By.XPATH,
            "//input[@type='checkbox' and @name='dutyTerms' and @value='ONE_DAY']"
            "/ancestor::*[1]",
        )
        self.click_element(duration_click_locator, "'하루(1일)' 조건")
        self.wait_for_selected(duration_input_locator, "'하루(1일)' 조건")
        self.sleep()

        # 테스트 절차: 조건이 선택되면 활성화되는 '초기화' 버튼을 클릭한다.
        self.click_element(
            (By.XPATH, "//button[normalize-space()='초기화']"),
            "'초기화' 버튼",
        )

        # 기대 결과: 선택 조건이 없으므로 초기화 버튼이 비활성화된다.
        self.assert_element_disabled(
            (By.XPATH, "//button[.//span[normalize-space()='초기화']]"),
            "초기화 버튼이 비활성화되어야 합니다.",
        )
        self.sleep()

        # 기대 결과: 선택 조건 칩이 모두 사라진다.
        self.assert_no_elements(
            (By.CSS_SELECTOR, "div.selector-chips__list button"),
            "초기화 후에도 선택 조건 목록에 항목이 남아 있습니다.",
            highlight_locator=(
                By.CSS_SELECTOR,
                "div[class*='SelectorChips_selector-chips']",
            ),
            name="선택 조건 목록 영역",
        )
        self.sleep()

        # 기대 결과: 업직종 탭의 조건 개수 표시가 사라진다.
        self.assert_no_elements(
            (
                By.XPATH,
                "//label[@role='tab' and @for='tab-1']//em",
            ),
            "초기화 후에도 업직종 탭에 숫자 표시가 남아 있습니다.",
            highlight_locator=(
                By.CSS_SELECTOR,
                "label[role='tab'][for='tab-1']",
            ),
            name="업직종 탭(숫자 표시 확인 영역)",
        )
        self.sleep()

        # 기대 결과: 근무기간 탭의 조건 개수 표시가 사라진다.
        self.assert_no_elements(
            (
                By.XPATH,
                "//label[@role='tab' and @for='tab-2']//em",
            ),
            "초기화 후에도 근무기간 탭에 숫자 표시가 남아 있습니다.",
            highlight_locator=(By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            name="근무기간 탭(숫자 표시 확인 영역)",
        )
        self.sleep()

        # 기대 결과를 확인하기 위한 사전 조건
        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-2']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            "근무기간 탭",
        )

        # 기대 결과: 기존에 선택한 '하루(1일)' 조건이 해제된다.
        self.assert_for_not_selected(
            duration_input_locator,
            "초기화 후에도 '하루(1일)' 조건이 선택되어 있습니다.",
            highlight_locator=duration_click_locator,
        )
        self.sleep()

        # 기대 결과: 근무기간 조건 개수가 0으로 표시된다.
        self.assert_element_text(
            (
                By.XPATH,
                "//div[@role='tabpanel' and @id='panel-2']"
                "//div[contains(@class, 'filter-toggle__title-box__counter')]",
            ),
            "(0/6)",
            "근무기간 조건 개수",
        )
        self.sleep()

    def tearDown(self):
        super().dispose()
