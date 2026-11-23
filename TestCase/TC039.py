from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC039(TCBase):
    """근무기간 조건을 하나씩 선택했을 때 적용되는지 검증한다."""

    DURATION_CONDITIONS = (
        ("ONE_DAY", "하루(1일)"),
        ("LESS_THAN_ONE_WEEK", "1주일이하"),
        ("ONE_WEEK_TO_ONE_MONTH", "1주일~1개월"),
        ("ONE_MONTH_TO_THREE_MONTH", "1개월~3개월"),
        ("THREE_MONTH_TO_SIX_MONTH", "3개월~6개월"),
        ("SIX_MONTH_TO_ONE_YEAR", "6개월~1년"),
        ("MORE_THAN_ONE_YEAR", "1년이상"),
    )

    def setUp(self):
        super().init()

    def _verify_selected_duration_jobs(self, condition, job_items):
        """선택한 근무기간 조건의 공고를 최대 MAX_JOBS건까지 검증한다."""
        duration_detail_item = (
            ".//div[contains(@class, 'list-item-recruit-details__item')]"
            "[.//span[normalize-space()='기간/요일']]"
        )
        page = 1
        checked_jobs = 0

        while checked_jobs < self.MAX_JOBS:
            try:
                self.wait_for_elements(job_items, f"{condition} {page}페이지 공고 목록")
                items = self.browser.find_elements(*job_items)
                self.assertTrue(items, f"{condition} {page}페이지에 공고가 없습니다.")
                invalid_jobs = []
                remaining_jobs = self.MAX_JOBS - checked_jobs

                for index in range(1, min(len(items), remaining_jobs) + 1):
                    item = self.browser.find_elements(*job_items)[index - 1]
                    title = item.find_element(
                        By.CSS_SELECTOR,
                        "a.list-item-recruit__link",
                    ).text
                    duration_items = item.find_elements(
                        By.XPATH,
                        duration_detail_item,
                    )
                    duration_detail = " ".join(
                        " ".join(element.text.split())
                        for element in duration_items
                    ).strip()
                    is_allowed = bool(duration_detail) and condition in duration_detail
                    self._log_action(
                        f"{condition} {page}페이지 {index}번 공고 | "
                        f"기간/요일: {duration_detail or '확인 불가'} | "
                        f"검증: {'통과' if is_allowed else '실패'}"
                    )
                    if not is_allowed:
                        invalid_jobs.append(
                            f"{title} [기간/요일: {duration_detail or '확인 불가'}]"
                        )
                    checked_jobs += 1

                self.assertFalse(
                    invalid_jobs,
                    f"{condition} 조건이 아닌 공고가 있습니다: {invalid_jobs}",
                )
                self._log_action(
                    f"{condition} 공고 {checked_jobs}/{self.MAX_JOBS}개 확인"
                )
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
                    for item in self.browser.find_elements(*job_items)
                )
                self.browser.find_element(*next_page_locator).click()

                def is_page_changed(driver):
                    try:
                        current_titles = tuple(
                            item.find_element(
                                By.CSS_SELECTOR,
                                "a.list-item-recruit__link",
                            ).text
                            for item in driver.find_elements(*job_items)
                        )
                        return bool(current_titles) and current_titles != previous_titles
                    except StaleElementReferenceException:
                        return False

                self.wait.until(is_page_changed)
                self.wait_for_recruit_list_rendered(
                    job_items,
                    f"{condition} {page + 1}페이지 공고 목록",
                )
                page += 1
            except Exception as exc:
                self.fail(
                    f"{condition} {page}페이지 공고 검증 중 오류가 발생했습니다: {exc}"
                )

    def test_apply_one_day(self):
        """검증 데이터의 각 근무기간 조건 공고만 조회되는지 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-2']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            "근무기간 탭",
        )
        self.sleep()

        page_size_locator = (By.ID, "select-size")
        self.click_element(page_size_locator, "공고 목록 노출 개수 선택")
        self.click_element(
            (By.XPATH, "//button[normalize-space()='50개씩']"),
            "공고 50개씩 보기",
        )
        self.wait.until(
            lambda driver: driver.find_element(*page_size_locator).text.strip()
            == "50개씩"
        )
        self._log_action(
            "공고 목록 노출 설정 확인: "
            f"{self.browser.find_element(*page_size_locator).text.strip()}"
        )
        self.sleep()

        job_items = (
            By.XPATH,
            "//ul[contains(@class, 'SimpleRecruitList')]//li",
        )
        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "공고 리스트 그리드뷰 전환",
        )
        self.sleep()

        self.wait_for_recruit_list_rendered(job_items, "그리드뷰 전환 후 공고 목록")
        duration_panel = "//div[@role='tabpanel' and @id='panel-2']"
        duration_counter = (
            By.XPATH,
            f"{duration_panel}//div[contains(@class, 'filter-toggle__title-box__counter')]",
        )
        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )

        for value, condition in self.DURATION_CONDITIONS:
            duration_input = (
                By.XPATH,
                f"{duration_panel}//input[@type='checkbox' and @name='dutyTerms' "
                f"and @value={value!r}]",
            )
            duration_click_target = (
                By.XPATH,
                f"{duration_panel}//input[@type='checkbox' and @name='dutyTerms' "
                f"and @value={value!r}]/ancestor::*[1]",
            )
            self.click_element(duration_click_target, f"'{condition}' 조건")
            self.wait_for_selected(duration_input, f"'{condition}' 조건")
            self.sleep()

            self.assert_element_text(
                (By.XPATH, "//label[@role='tab' and @for='tab-2']//em"),
                "1",
                f"{condition} 선택 후 근무기간 탭 선택 개수",
            )
            self.assert_element_text(
                duration_counter,
                "(1/6)",
                f"{condition} 선택 후 근무기간 조건 개수",
            )
            self.assert_element_text(
                (By.XPATH, f"{chip_base}[normalize-space()={condition!r}]"),
                condition,
                f"조건 리스트의 {condition}",
            )
            self.wait_for_recruit_list_rendered(
                job_items,
                f"{condition} 조건 적용 후 공고 목록",
            )
            self._verify_selected_duration_jobs(condition, job_items)
            self.click_element(duration_click_target, f"'{condition}' 조건 해제")
            self.wait_for_not_selected(duration_input, f"해제된 '{condition}' 조건")
            self.wait_for_recruit_list_rendered(
                job_items,
                f"{condition} 조건 해제 후 공고 목록",
            )

        self.sleep()

    def tearDown(self):
        super().dispose()
