from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC040(TCBase):
    """근무기간 복수 조건의 공고를 검증한다."""

    def setUp(self):
        super().init()

    def test_apply_multiple_duration(self):
        """하루(1일) 또는 1개월~3개월인 공고를 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-2']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            "근무기간 탭",
        )
        self.sleep()

        one_day_input = (
            By.XPATH,
            "//input[@type='checkbox' and @name='dutyTerms' and @value='ONE_DAY']",
        )
        self.click_element(
            (
                By.XPATH,
                "//input[@type='checkbox' and @name='dutyTerms' and @value='ONE_DAY']"
                "/ancestor::*[1]",
            ),
            "'하루(1일)' 조건",
        )
        self.wait_for_selected(one_day_input, "'하루(1일)' 조건")

        one_to_three_months = (
            By.XPATH,
            "//div[@role='tabpanel' and @id='panel-2']"
            "//*[normalize-space(.)='1개월~3개월']",
        )
        self.click_element(one_to_three_months, "'1개월~3개월' 조건")

        duration_counter = (
            By.XPATH,
            "//div[@role='tabpanel' and @id='panel-2']"
            "//div[contains(@class, 'filter-toggle__title-box__counter')]",
        )
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-2']//em"),
            "2",
            "근무기간 탭 선택 개수",
        )
        self.assert_element_text(duration_counter, "(2/6)", "근무기간 조건 개수")

        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )
        for duration_name in ("하루(1일)", "1개월~3개월"):
            self.assert_element_text(
                (By.XPATH, f"{chip_base}[normalize-space()={duration_name!r}]"),
                duration_name,
                f"조건 리스트의 {duration_name}",
            )

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
        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "공고 리스트 그리드뷰 전환",
        )

        job_items = (By.XPATH, "//ul[contains(@class, 'SimpleRecruitList')]//li")
        duration_details = (
            ".//div[contains(@class, 'list-item-recruit-details__item')]"
            "[.//span[normalize-space()='기간/요일']]"
            "//span[contains(@class, 'list-item-recruit-details__children')]"
        )
        valid_durations = ("하루(1일)", "1개월~3개월")
        page = 1
        checked_jobs = 0
        one_day_count = 0
        one_to_three_months_count = 0
        total_job_count = 0

        while checked_jobs < self.MAX_JOBS:
            try:
                self.wait_for_elements(job_items, f"{page}페이지 공고 목록")
                items = self.browser.find_elements(*job_items)
                self.assertTrue(items, f"{page}페이지에 공고가 없습니다.")
                items = items[: self.MAX_JOBS - checked_jobs]
                self._log_action(f"{page}페이지 복수 근무기간 공고 확인 중...")
                invalid_jobs = []
                for index, item in enumerate(items, start=1):
                    total_job_count += 1
                    title = item.find_element(
                        By.CSS_SELECTOR,
                        "a.list-item-recruit__link",
                    ).text
                    duration_elements = item.find_elements(By.XPATH, duration_details)
                    duration_detail = " ".join(
                        element.text for element in duration_elements
                    ) or item.text
                    if "하루(1일)" in duration_detail:
                        one_day_count += 1
                    if "1개월~3개월" in duration_detail:
                        one_to_three_months_count += 1
                    if not any(duration in duration_detail for duration in valid_durations):
                        invalid_jobs.append(title)

                self.assertFalse(
                    invalid_jobs,
                    f"{page}페이지에 선택한 근무기간이 아닌 공고가 있습니다: "
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
                    f"{page}페이지 복수 근무기간 공고 검증 중 오류가 발생했습니다: "
                    f"{exc}"
                )

        self._log_action(
            "전체 조회 결과 기간별 공고 수 - "
            f"하루(1일): {one_day_count}개, "
            f"1개월~3개월: {one_to_three_months_count}개, "
            f"전체 조회 공고: {total_job_count}개"
        )
        self.sleep()

    def tearDown(self):
        super().dispose()
