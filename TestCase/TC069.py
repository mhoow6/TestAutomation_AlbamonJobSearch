from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC069(TCBase):
    """고용형태를 하나씩 선택해 해당 공고가 조회되는지 검증한다."""

    EMPLOYMENT_TYPES = (
        "알바",
        "정규직",
        "계약직",
        "파견직",
        "위촉직(프리랜서)",
        "청년인턴",
        "연수생/교육생",
    )
    EMPLOYMENT_DETAIL_ALIASES = {
        "청년인턴": ("청년인턴", "청년인턴직", "인턴"),
        "위촉직(프리랜서)": ("위촉직(프리랜서)", "위촉직/프리랜서"),
    }
    EMPLOYMENT_CHIP_LABELS = {
        "청년인턴": "청년인턴직",
    }
    def setUp(self):
        super().init()

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

            if "/user-account/cert/adult/non-login" in self.browser.current_url:
                self._log_action(
                    f"성인인증 필요 공고 검증 제외: {title} | "
                    f"URL: {self.browser.current_url}"
                )
                return None

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

    def _select_employment_type(self, employment_type):
        employment_input = (
            By.XPATH,
            "//label[.//span[normalize-space()="
            f"{employment_type!r}]]//input[@type='checkbox']",
        )
        employment_click = (
            By.XPATH,
            "//label[.//span[normalize-space()="
            f"{employment_type!r}]]",
        )
        self.select_if_not_selected(
            employment_input,
            employment_click,
            f"고용형태 '{employment_type}'",
        )
        self.sleep()

        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-3']//em"),
            "1",
            f"'{employment_type}' 상세조건 탭 선택 개수",
        )
        chip_label = self.EMPLOYMENT_CHIP_LABELS.get(
            employment_type,
            employment_type,
        )
        self.assert_element_text(
            (
                By.XPATH,
                "//div[contains(@class, 'selector-chips__list')]"
                "//button[contains(@class, 'selector-chips__chip')"
                f" and normalize-space()={chip_label!r}]",
            ),
            chip_label,
            f"조건 리스트의 고용형태 {chip_label}",
        )

    def _verify_jobs(self, employment_type):
        """선택한 고용형태의 공고를 최대 MAX_JOBS건까지 검증한다."""
        self.click_element((By.ID, "select-size"), "공고 목록 노출 개수 선택")
        self.click_element((By.XPATH, "//button[normalize-space()='50개씩']"), "공고 50개씩 보기")
        self.wait.until(
            lambda driver: driver.find_element(By.ID, "select-size").text.strip()
            == "50개씩"
        )
        self.sleep()

        job_items = (By.XPATH, "//ul[contains(@class, 'SimpleRecruitList')]//li")
        page = 1
        checked_jobs = 0

        while checked_jobs < self.MAX_JOBS:
            try:
                self.wait_for_elements(job_items, f"{page}페이지 공고 목록")
                items = self.browser.find_elements(*job_items)
                self.assertTrue(items, f"{page}페이지에 공고가 없습니다.")
                invalid_jobs = []

                for index in range(1, min(len(items), self.MAX_JOBS - checked_jobs) + 1):
                    current_items = self.browser.find_elements(*job_items)
                    item = current_items[index - 1]
                    title = item.find_element(By.CSS_SELECTOR, "a.list-item-recruit__link").text
                    detail_link = item.find_element(By.CSS_SELECTOR, "a.list-item-recruit__link")
                    employment_detail = self._get_detail_employment_type(
                        detail_link, title, job_items
                    )
                    if employment_detail is None:
                        checked_jobs += 1
                        continue

                    normalized_detail = "".join(employment_detail.split())
                    accepted_types = self.EMPLOYMENT_DETAIL_ALIASES.get(
                        employment_type,
                        (employment_type,),
                    )
                    is_selected = any(
                        "".join(detail_type.split()) in normalized_detail
                        for detail_type in accepted_types
                    )
                    self._log_action(
                        f"{page}페이지 {index}번 공고 | 고용형태: {employment_detail} | "
                        f"검증: {'통과' if is_selected else '실패'}"
                    )
                    if not is_selected:
                        invalid_jobs.append(f"{title} [{employment_detail}]")
                    checked_jobs += 1

                self.assertFalse(
                    invalid_jobs,
                    f"고용형태가 {employment_type}이 아닌 공고가 "
                    f"있습니다: {invalid_jobs}",
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
                            item.find_element(By.CSS_SELECTOR, "a.list-item-recruit__link").text
                            for item in driver.find_elements(*job_items)
                        )
                        return bool(current_titles) and current_titles != previous_titles
                    except StaleElementReferenceException:
                        return False

                self.wait.until(is_page_changed)
                page += 1
            except Exception as exc:
                self.fail(
                    f"{page}페이지 {employment_type} 공고 검증 중 오류가 발생했습니다: {exc}"
                )

    def test_apply_employment_type_alba(self):
        """고용형태를 하나씩 선택해 해당 공고가 맞는지 확인한다."""
        for employment_type in self.EMPLOYMENT_TYPES:
            self.load()
            self.select_if_not_selected(
                (By.XPATH, "//input[@id='tab-3']"),
                (By.XPATH, "//label[@role='tab' and @for='tab-3']"),
                "상세조건 탭",
            )
            self.sleep()
            self._select_employment_type(employment_type)
            self._verify_jobs(employment_type)

    def tearDown(self):
        super().dispose()
