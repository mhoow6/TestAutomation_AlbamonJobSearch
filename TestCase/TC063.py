from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase
from TestCase.TC054 import TC054


class TC063(TCBase):
    """근무시간 직접선택에서 00:00~06:00 조건을 검증한다."""

    ALLOWED_TIME_RANGES = ((0, 6 * 60),)
    START_TIME = "00:00"
    END_TIME = "06:00"
    INCLUDE_NEGOTIABLE_TIME = False
    NEGOTIATION_EXCLUDED_BEFORE = None
    NEGOTIATION_EXCLUDED_AFTER = None
    NEGOTIATION_TRANSITION_WAIT = 0

    def setUp(self):
        super().init()

    @classmethod
    def _is_allowed_work_time(cls, work_time):
        return TC054._is_allowed_work_time.__func__(cls, work_time)

    def _select_time(self, button_id, value, name):
        self.click_element((By.ID, button_id), f"{name} 선택창")
        self.click_element(
            (By.XPATH, f"//*[@role='listbox']//button[@data-value='{value}']"),
            f"{name} {value}",
        )
        select_locator = (By.CSS_SELECTOR, f"select[name='{button_id.removeprefix('select-')}']")
        self.wait.until(
            lambda driver: driver.find_element(*select_locator).get_attribute("value")
            == value
        )

    def _run_direct_work_time_range(self):
        """설정된 직접선택 근무시간 범위와 공고 목록을 검증한다."""
        self.load()
        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-2']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            "근무기간 탭",
        )
        self.sleep()
        direct_option = (
            By.XPATH,
            "//label[.//span[normalize-space()='직접선택']]//input[@name='workTimeTypeDirect']",
        )
        self.click_element(
            (By.XPATH, "//label[.//span[normalize-space()='직접선택']][.//input[@name='workTimeTypeDirect']]"),
            "근무시간 '직접선택' 조건",
        )
        self.wait_for_selected(direct_option, "근무시간 직접선택")
        self._select_time("select-minTime", self.START_TIME, "시작시간")
        self.sleep()
        self._select_time("select-maxTime", self.END_TIME, "종료시간")
        self.sleep()

        if self.NEGOTIATION_EXCLUDED_BEFORE is not None:
            exclude_negotiation = (
                By.XPATH,
                "(//label[.//span[normalize-space()='협의 제외']]"
                "//input[@type='checkbox' and @name='dfa' and not(@disabled)])[last()]",
            )
            exclude_negotiation_click = (
                By.XPATH,
                "(//label[.//span[normalize-space()='협의 제외']]"
                "//input[@type='checkbox' and @name='dfa' and not(@disabled)]"
                "/ancestor::label[1])[last()]",
            )
            # 페이지 기본값이 환경에 따라 달라질 수 있으므로 사전 조건을 먼저 맞춘다.
            if self.NEGOTIATION_EXCLUDED_BEFORE:
                self.select_if_not_selected(
                    exclude_negotiation,
                    exclude_negotiation_click,
                    "근무시간 '협의 제외' 사전 조건",
                )
            elif self.is_element_selected(exclude_negotiation):
                self.click_element(
                    exclude_negotiation_click,
                    "근무시간 '협의 제외' 사전 조건 해제",
                )
                self.wait_for_not_selected(
                    exclude_negotiation,
                    "근무시간 '협의 제외' 사전 조건",
                )

            if self.NEGOTIATION_TRANSITION_WAIT:
                self.sleep(self.NEGOTIATION_TRANSITION_WAIT)

            if self.NEGOTIATION_EXCLUDED_AFTER != self.NEGOTIATION_EXCLUDED_BEFORE:
                action = "선택" if self.NEGOTIATION_EXCLUDED_AFTER else "해제"
                self.click_element(
                    exclude_negotiation_click,
                    f"근무시간 '협의 제외' {action}",
                )

            if self.NEGOTIATION_EXCLUDED_AFTER:
                self.wait_for_selected(exclude_negotiation, "선택된 근무시간 협의 제외")
            else:
                self.wait_for_not_selected(exclude_negotiation, "해제된 근무시간 협의 제외")

        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-2']//em"),
            "1",
            "근무시간 직접선택 후 근무기간 탭 선택 개수",
        )
        self.assert_element_text(
            (
                By.XPATH,
                "//div[contains(@class, 'selector-chips__list')]//button["
                "contains(@class, 'selector-chips__chip') and "
                f"normalize-space()='{self.START_TIME}~{self.END_TIME}']",
            ),
            f"{self.START_TIME}~{self.END_TIME}",
            "조건 리스트의 직접선택 근무시간",
        )

        self.click_element((By.ID, "select-size"), "공고 목록 노출 개수 선택")
        self.click_element((By.XPATH, "//button[normalize-space()='50개씩']"), "공고 50개씩 보기")
        self.wait.until(lambda driver: driver.find_element(By.ID, "select-size").text.strip() == "50개씩")
        self.sleep()

        job_items = (By.XPATH, "//ul[contains(@class, 'SimpleRecruitList')]//li")
        time_details = ".//div[contains(@class, 'list-item-recruit__contents--time')]//p"
        self.wait_for_recruit_list_rendered(job_items, "50개 보기 적용 후 공고 목록")
        self.sleep()

        page = 1
        checked_jobs = 0
        invalid_jobs = []
        while checked_jobs < self.MAX_JOBS:
            self.wait_for_elements(job_items, f"{page}페이지 공고 목록")
            items = self.browser.find_elements(*job_items)
            self.assertTrue(items, f"{page}페이지에 공고가 없습니다.")

            remaining_jobs = self.MAX_JOBS - checked_jobs
            for index in range(1, min(len(items), remaining_jobs) + 1):
                current_items = self.browser.find_elements(*job_items)
                item = current_items[index - 1]
                work_time = " ".join(
                    " ".join(element.text.split())
                    for element in item.find_elements(By.XPATH, time_details)
                    if ":" in element.text or "시간협의" in element.text
                ).strip() or "확인 불가"
                is_allowed_work_time = self._is_allowed_work_time(work_time)
                self._log_action(
                    f"{page}페이지 {index}번 공고 | 목록 근무시간: {work_time} | "
                    f"검증: {'통과' if is_allowed_work_time else '실패'}"
                )
                if not is_allowed_work_time:
                    invalid_jobs.append(
                        f"{page}페이지 {index}번 공고 [{work_time}]"
                    )
                checked_jobs += 1

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
                item.find_element(By.CSS_SELECTOR, "a.list-item-recruit__link").text
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
            page += 1

        self.assertFalse(
            invalid_jobs,
            f"{self.START_TIME}~{self.END_TIME} 조건과 맞지 않는 공고가 있습니다: "
            f"{invalid_jobs}",
        )

    def test_select_direct_work_time_range(self):
        """직접선택에서 00:00~06:00을 선택하고 해당 공고만 조회되는지 확인한다."""
        self._run_direct_work_time_range()

    def tearDown(self):
        super().dispose()
