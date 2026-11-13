import re

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from Module.TCBase import TCBase


class TC031(TCBase):
    """키워드 변경 시 업직종 검색 결과가 갱신되는지 확인한다."""

    def setUp(self):
        super().init()

    def test_keyword_search_result_refresh(self):
        """서빙 검색 결과를 QA 검색 결과로 변경하면 목록도 달라지는지 확인한다."""
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
        search_results = (
            By.XPATH,
            "//div[@role='tabpanel' and @id='panel-1']"
            "//ul[contains(@class, 'autocomplete-list')]"
            "//li",
        )

        self.wait_for_element(keyword_input, "업직종 키워드 검색창")
        search_box = self.browser.find_element(*keyword_input)

        search_box.send_keys("서빙")
        serving_results = self._read_search_results(search_results, "서빙")
        serving_result_names = set(serving_results)

        search_box.send_keys(Keys.CONTROL, "a")
        search_box.send_keys("QA")
        self.wait.until(
            lambda driver: self._search_results_changed(
                search_results,
                serving_result_names,
            )
        )
        qa_results = self._read_search_results(search_results, "QA")
        qa_result_names = set(qa_results)

        self.assertNotEqual(
            serving_result_names,
            qa_result_names,
            "검색어를 서빙에서 QA로 변경했지만 검색 결과가 갱신되지 않았습니다.",
        )

    def _read_search_results(self, locator, keyword):
        """검색 결과가 표시될 때까지 기다린 뒤 정규화된 결과명을 반환한다."""
        self.wait_for_elements(locator, f"{keyword} 키워드 검색 결과")
        return self._read_search_result_names(locator)

    def _read_search_result_names(self, locator):
        """현재 자동완성 목록의 텍스트를 정규화해 튜플로 반환한다."""
        return tuple(
            re.sub(r"\s+", " ", element.text).strip()
            for element in self.browser.find_elements(*locator)
            if element.text.strip()
        )

    def _search_results_changed(self, locator, previous_result_names):
        """현재 검색 결과 항목 집합이 이전 결과와 달라졌는지 확인한다."""
        current_result_names = set(self._read_search_result_names(locator))
        return bool(current_result_names) and current_result_names != previous_result_names

    def tearDown(self):
        super().dispose()
