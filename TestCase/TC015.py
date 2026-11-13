from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC015(TCBase):
    SEARCH_TERM = "강남구"

    def setUp(self):
        super().init()

    def test_search_region_name(self):
        """지역명 검색 결과의 모든 조건명에 검색어가 포함되는지 확인한다."""
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
        counter = (
            By.XPATH,
            f"{panel}//div[contains(@class, 'filter-header__counter')]",
        )
        search_input = (
            By.XPATH,
            f"{panel}//input[@name='filter-search']",
        )
        search_result_items = (
            By.XPATH,
            f"{panel}//ul[.//input[@type='checkbox']]//li",
        )

        # 사전 조건: 지역 조건이 선택되지 않은 초기 상태인지 확인한다.
        self.assert_element_text(counter, "0/5", "지역 조건 선택 개수")

        # 테스트 절차: 지역명 검색창에 검색어를 입력한다.
        search_element = self.wait_for_element(search_input, "지역명 검색창")
        search_element.clear()
        search_element.send_keys(self.SEARCH_TERM)

        # 검색어 입력 후 결과 목록이 갱신될 때까지 기다린다.
        results = self.wait_for_elements(search_result_items, "지역명 검색 결과")
        result_names = [result.text.strip() for result in results]

        self.assertGreater(
            len(result_names),
            0,
            "지역명 검색 결과가 표시되지 않았습니다.",
        )
        invalid_results = [
            result_name
            for result_name in result_names
            if self.SEARCH_TERM not in result_name
        ]
        self.assertFalse(
            invalid_results,
            "검색어를 포함하지 않는 지역 조건이 검색 결과에 표시되었습니다: "
            f"{invalid_results}",
        )

    def tearDown(self):
        super().dispose()
