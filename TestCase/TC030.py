from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC030(TCBase):
    """키워드 검색창 초기화 버튼의 동작을 확인한다."""

    def setUp(self):
        super().init()

    def test_keyword_search_clear_button(self):
        """QA 입력 후 X 버튼을 클릭하면 검색어가 비워지는지 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-1']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-1']"),
            "업직종 탭",
        )
        self.sleep()

        keyword_input = (
            By.CSS_SELECTOR,
            "input[name='filter-search'][placeholder*='키워드 검색']",
        )
        self.wait_for_element(keyword_input, "업직종 키워드 검색창")
        search_box = self.browser.find_element(*keyword_input)
        search_box.send_keys("QA")
        self.sleep()

        self.wait.until(
            lambda driver: driver.find_element(*keyword_input).get_attribute("value")
            == "QA"
        )

        clear_button = (
            By.CSS_SELECTOR,
            "button[class*='button-input-clear']",
        )
        self.wait_for_element(clear_button, "키워드 검색창 X 버튼")
        self.click_element(clear_button, "키워드 검색창 X 버튼")

        self.wait.until(
            lambda driver: driver.find_element(*keyword_input).get_attribute("value")
            == ""
        )

        # 기대 결과: 검색어가 비워지면 자동완성 검색 결과 목록이 사라진다.
        autocomplete_results = (
            By.CSS_SELECTOR,
            "#panel-1 ul.autocomplete-list",
        )
        try:
            self.wait.until(
                lambda driver: not any(
                    element.is_displayed()
                    for element in driver.find_elements(*autocomplete_results)
                )
            )
        except Exception as exc:
            self.fail(
                f"키워드 검색 결과 목록이 초기화 후에도 화면에 표시됩니다: {exc}"
            )

        # 기대 결과: 원래의 대분류/업직종 목록이 다시 표시된다.
        category_heading = (
            By.XPATH,
            "//div[@role='tabpanel' and @id='panel-1']"
            "//span[normalize-space()='대분류']",
        )
        job_type_heading = (
            By.XPATH,
            "//div[@role='tabpanel' and @id='panel-1']"
            "//span[normalize-space()='업직종']",
        )
        category_item = (
            By.XPATH,
            "//div[@role='tabpanel' and @id='panel-1']"
            "//*[self::li or self::button][normalize-space()='외식·음료']",
        )
        job_type_item = (
            By.XPATH,
            "//div[@role='tabpanel' and @id='panel-1']"
            "//*[self::li or self::button][normalize-space()='외식·음료 전체']",
        )

        self.wait_for_element(category_heading, "대분류 목록 제목")
        self.wait_for_element(job_type_heading, "업직종 목록 제목")
        self.wait_for_element(category_item, "대분류 목록의 외식·음료")
        self.wait_for_element(job_type_item, "업직종 목록의 외식·음료 전체")

    def tearDown(self):
        super().dispose()
