from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from TestCase.TC069 import TC069


class TC070(TC069):
    """고용형태 복수 선택 조건이 함께 적용되는지 검증한다."""

    EMPLOYMENT_TYPES = ("알바", "정규직")

    def _has_selected_employment_type(self, employment_type):
        """상세 고용형태 중 선택한 고용형태가 하나라도 포함되는지 확인한다."""
        detail_types = {
            detail.strip()
            for detail in employment_type.split(",")
            if detail.strip()
        }
        return bool(detail_types.intersection(self.EMPLOYMENT_TYPES))

    def _get_detail_employment_type(self, detail_link, title, job_items):
        """공고 상세를 새 탭에서 확인하고 목록 탭으로 돌아온다."""
        original_handle = self.browser.current_window_handle
        original_handles = set(self.browser.window_handles)
        detail_handle = None

        try:
            self._log_action(f"공고 상세 새 탭 여는 중: {title}")
            detail_url = detail_link.get_attribute("href")
            if not detail_url:
                self.fail(f"공고 상세 URL을 찾을 수 없습니다: {title}")

            self.browser.execute_script("window.open(arguments[0], '_blank');", detail_url)
            self.wait.until(
                lambda driver: len(set(driver.window_handles) - original_handles) == 1
            )
            detail_handle = next(
                handle
                for handle in self.browser.window_handles
                if handle not in original_handles
            )
            self.browser.switch_to.window(detail_handle)
            self.sleep(2)

            alert = self.get_alert(self.browser)
            if alert:
                alert_message = alert.text
                alert.accept()
                self.fail(
                    f"마감 공고로 상세 고용형태를 확인할 수 없습니다: "
                    f"{alert_message} (공고: {title})"
                )

            employment_locator = (
                By.XPATH,
                "//dt[normalize-space()='고용형태']/following-sibling::dd[1]",
            )
            employment_element = self.wait_for_element(
                employment_locator,
                f"'{title}' 상세 고용형태",
            )
            employment_type = " ".join(employment_element.text.split())
            self._log_action(f"상세 고용형태 확인: {employment_type}")
            return employment_type
        finally:
            if detail_handle and detail_handle in self.browser.window_handles:
                self.browser.close()
            if original_handle in self.browser.window_handles:
                self.browser.switch_to.window(original_handle)
                self.wait_for_elements(job_items, "공고 목록 유지")

    def _select_employment_types(self):
        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-3']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-3']"),
            "상세조건 탭",
        )
        self.sleep()

        for employment_type in self.EMPLOYMENT_TYPES:
            state_locator = (
                By.XPATH,
                f"//label[.//span[normalize-space()={employment_type!r}]]"
                "//input[@type='checkbox']",
            )
            click_locator = (
                By.XPATH,
                f"//label[.//span[normalize-space()={employment_type!r}]]",
            )
            self.select_if_not_selected(
                state_locator,
                click_locator,
                f"고용형태 '{employment_type}'",
            )
            self.sleep()

        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-3']//em"),
            str(len(self.EMPLOYMENT_TYPES)),
            "상세조건 탭 선택 개수",
        )
        for employment_type in self.EMPLOYMENT_TYPES:
            self.assert_element_text(
                (
                    By.XPATH,
                    "//div[contains(@class, 'selector-chips__list')]"
                    "//button[contains(@class, 'selector-chips__chip')"
                    f" and normalize-space()={employment_type!r}]",
                ),
                employment_type,
                f"조건 리스트의 고용형태 {employment_type}",
            )

    def test_apply_employment_type_alba(self):
        """선택한 복수 고용형태 공고만 조회되는지 확인한다."""
        self.load()
        self._select_employment_types()

        self.click_element((By.ID, "select-size"), "공고 목록 노출 개수 선택")
        self.click_element((By.XPATH, "//button[normalize-space()='50개씩']"), "공고 50개씩 보기")
        self.wait.until(
            lambda driver: driver.find_element(By.ID, "select-size").text.strip() == "50개씩"
        )
        self.sleep()
        job_items = (By.XPATH, "//ul[contains(@class, 'SimpleRecruitList')]//li")
        page = 1
        checked_jobs = 0

        while checked_jobs < self.MAX_JOBS:
            self.wait_for_elements(job_items, f"{page}페이지 공고 목록")
            items = self.browser.find_elements(*job_items)
            self.assertTrue(items, f"{page}페이지에 공고가 없습니다.")
            invalid_jobs = []

            remaining_jobs = self.MAX_JOBS - checked_jobs
            for index in range(1, min(len(items), remaining_jobs) + 1):
                current_items = self.browser.find_elements(*job_items)
                item = current_items[index - 1]
                title = item.find_element(By.CSS_SELECTOR, "a.list-item-recruit__link").text
                detail_link = item.find_element(By.CSS_SELECTOR, "a.list-item-recruit__link")
                employment_type = self._get_detail_employment_type(
                    detail_link, title, job_items
                )
                valid = self._has_selected_employment_type(employment_type)
                self._log_action(
                    f"{page}페이지 {index}번 공고 | 고용형태: {employment_type} | "
                    f"검증: {'통과' if valid else '실패'}"
                )
                if not valid:
                    invalid_jobs.append(f"{title} [{employment_type}]")
                checked_jobs += 1

            self.assertFalse(
                invalid_jobs,
                "선택한 고용형태가 아닌 공고가 있습니다: "
                f"{invalid_jobs}",
            )

            if checked_jobs >= self.MAX_JOBS:
                break

            next_page_locator = (
                By.XPATH,
                f"//*[@role='navigation']//button[contains(@aria-label, 'goto {page + 1} in')]",
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

