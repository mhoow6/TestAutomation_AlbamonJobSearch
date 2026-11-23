from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC032(TCBase):
    """키워드 검색 결과의 업직종 조건이 실제 필터로 적용되는지 확인한다."""

    def setUp(self):
        super().init()

    def test_apply_qa_keyword_condition(self):
        """QA·테스터·검증을 선택하고 조건 수, 칩, 공고 업직종을 검증한다."""
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
        self.browser.find_element(*keyword_input).send_keys("QA")

        qa_result = (
            By.XPATH,
            "//div[@role='tabpanel' and @id='panel-1']"
            "//ul[contains(@class, 'autocomplete-list')]"
            "//li[.//div[normalize-space(.)='QA·테스터·검증']]",
        )
        self.wait_for_element(qa_result, "QA·테스터·검증 검색 결과")

        qa_checkbox = (
            By.XPATH,
            "//div[@role='tabpanel' and @id='panel-1']"
            "//ul[contains(@class, 'autocomplete-list')]"
            "//li[.//div[normalize-space(.)='QA·테스터·검증']]"
            "//label",
        )
        self.click_element(qa_checkbox, "QA·테스터·검증 조건")

        # 기대 결과: 업직종 탭과 조건 개수가 1로 표시된다.
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-1']//em"),
            "1",
            "업직종 탭 선택 개수",
        )
        self.assert_element_text(
            (
                By.XPATH,
                "//div[@role='tabpanel' and @id='panel-1']"
                "//div[contains(@class, 'filter-header__counter')]",
            ),
            "1/10",
            "업직종 조건 개수",
        )

        # 기대 결과: 조건 리스트에 QA·테스터·검증이 추가된다.
        self.assert_element_text(
            (
                By.XPATH,
                "//div[contains(@class, 'selector-chips__list')]"
                "//button[contains(@class, 'selector-chips__chip')"
                " and normalize-space()='QA·테스터·검증']",
            ),
            "QA·테스터·검증",
            "조건 리스트의 QA·테스터·검증",
        )

        # 테스트 조건의 그리드/펼쳐 보기 상태로 전환한다.
        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "공고 리스트 그리드뷰 전환",
        )

        # 기대 결과: 모든 조회 페이지의 공고 업직종 상세에 QA 조건이 포함된다.
        job_items = (
            By.XPATH,
            "//ul[contains(@class, 'SimpleRecruitList')]//li",
        )
        job_category_details = (
            ".//div[contains(@class, 'list-item-recruit-details__item')]"
            "[.//span[normalize-space()='업직종']]"
            "//span[contains(@class, 'list-item-recruit-details__children')]"
        )
        page = 1
        checked_jobs = 0

        while checked_jobs < self.MAX_JOBS:
            try:
                self.wait_for_elements(job_items, f"{page}페이지 QA 조건 적용 공고 목록")
                items = self.browser.find_elements(*job_items)
                self.assertTrue(items, f"{page}페이지에 공고가 없습니다.")
                items = items[: self.MAX_JOBS - checked_jobs]
                self._log_action(f"{page}페이지 공고 업직종 확인 중...")

                invalid_jobs = []
                for item in items:
                    category_detail = item.find_element(
                        By.XPATH,
                        job_category_details,
                    ).text
                    if "QA·테스터·검증" not in category_detail:
                        invalid_jobs.append(
                            item.find_element(
                                By.CSS_SELECTOR,
                                "a.list-item-recruit__link",
                            ).text
                        )

                self.assertFalse(
                    invalid_jobs,
                    f"{page}페이지에 QA·테스터·검증이 없는 공고가 있습니다: "
                    f"{invalid_jobs}",
                )

                checked_jobs += len(items)
                if checked_jobs >= self.MAX_JOBS:
                    break

                next_page_locator = (
                    By.XPATH,
                    f"//*[@role='navigation']//button["
                    f"contains(@aria-label, 'goto {page + 1} in')]",
                )
                if not self.scroll_to_pagination(next_page_locator):
                    break

                previous_titles = tuple(
                    item.find_element(
                        By.CSS_SELECTOR,
                        "a.list-item-recruit__link",
                    ).text
                    for item in items
                )
                self.browser.find_element(*next_page_locator).click()

                def is_page_changed(driver):
                    try:
                        current_items = driver.find_elements(*job_items)
                        current_titles = tuple(
                            item.find_element(
                                By.CSS_SELECTOR,
                                "a.list-item-recruit__link",
                            ).text
                            for item in current_items
                        )
                        return bool(current_titles) and current_titles != previous_titles
                    except StaleElementReferenceException:
                        return False

                self.wait.until(is_page_changed)
                page += 1
            except Exception as exc:
                self.fail(
                    f"{page}페이지 QA 조건 적용 공고 검증 중 오류가 발생했습니다: "
                    f"{exc}"
                )

    def tearDown(self):
        super().dispose()
