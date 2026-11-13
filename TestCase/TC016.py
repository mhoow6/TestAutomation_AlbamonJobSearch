import re

from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC016(TCBase):
    SEARCH_TERM = "-1"
    NO_RESULT_LINES = (
        "검색 결과가 없습니다.",
        "전체목록에서 골라보세요",
    )

    def setUp(self):
        super().init()

    def _assert_no_result_message(self, panel):
        """검색 결과 없음 안내 문구의 두 줄을 각각 검증한다."""
        for expected_line in self.NO_RESULT_LINES:
            locator = (
                By.XPATH,
                f"{panel}//*[normalize-space()={expected_line!r}]",
            )
            try:
                self.wait.until(
                    lambda driver: any(
                        element.is_displayed()
                        and re.sub(
                            r"\s+",
                            " ",
                            element.get_attribute("textContent") or "",
                        ).strip()
                        == expected_line
                        for element in driver.find_elements(*locator)
                    )
                )
            except Exception as exc:
                self.fail(
                    "'지역명 검색 결과 없음 안내 문구'의 일부 문장이 "
                    f"'{expected_line}'(으)로 표시되지 않았습니다: {exc}"
                )

    def test_invalid_region_name_search(self):
        """유효하지 않은 지역명 검색 시 안내 문구가 표시되는지 확인한다."""
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

        # 사전 조건: 지역 조건이 선택되지 않은 초기 상태인지 확인한다.
        self.assert_element_text(counter, "0/5", "지역 조건 선택 개수")

        # 테스트 절차: 지역명 검색창에 유효하지 않은 검색어를 입력한다.
        search_element = self.wait_for_element(search_input, "지역명 검색창")
        search_element.clear()
        search_element.send_keys(self.SEARCH_TERM)

        # 검색 결과가 없다는 안내 문구가 정확히 표시되는지 확인한다.
        self._assert_no_result_message(panel)

    def tearDown(self):
        super().dispose()
