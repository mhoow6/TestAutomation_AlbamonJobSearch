import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from Module.TCBase import TCBase


class TC033(TCBase):
    """유효하지 않은 키워드 검색 시 안내 문구를 확인한다."""

    def setUp(self):
        super().init()

    def test_invalid_keyword_search_message(self):
        """-1 입력 후 검색 결과 없음 안내 문구가 표시되는지 검증한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-1']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-1']"),
            "업직종 탭",
        )

        keyword_input = (
            By.CSS_SELECTOR,
            "input[name='filter-search'][placeholder*='키워드 검색']",
        )
        self.wait_for_element(keyword_input, "업직종 키워드 검색창")
        self.browser.find_element(*keyword_input).send_keys("-1")

        no_result_message = (
            By.XPATH,
            "//*[@id='panel-1']/div/div[1]/div[1]/div[1]/div[2]/div",
        )
        self.highlight_element(
            no_result_message,
            "유효하지 않은 키워드 검색 안내 문구",
        )
        message_element = self.wait.until(
            EC.visibility_of_element_located(no_result_message)
        )
        actual_message = re.sub(r"\s+", " ", message_element.text).strip()
        expected_message = "검색 결과가 없습니다. 전체목록에서 골라보세요"
        self.assertEqual(
            actual_message,
            expected_message,
            "유효하지 않은 키워드 검색 안내 문구가 정확하지 않습니다. "
            f"실제 문구: {message_element.text!r}",
        )
        self.sleep()

    def tearDown(self):
        super().dispose()
