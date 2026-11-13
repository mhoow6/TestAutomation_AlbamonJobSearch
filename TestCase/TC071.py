import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from Module.TCBase import TCBase


class TC071(TCBase):
    """상세조건의 포함 키워드가 공고 검색에 적용되는지 검증한다."""

    KEYWORDS = ("AI",)

    def setUp(self):
        super().init()

    def _get_detail_text(self, detail_link, title, job_items):
        """공고 상세 본문을 새 탭에서 확인하고 목록 탭으로 돌아온다."""
        original_handle = self.browser.current_window_handle
        original_handles = set(self.browser.window_handles)
        detail_handle = None

        try:
            detail_url = detail_link.get_attribute("href")
            self.assertTrue(detail_url, f"공고 상세 URL을 찾을 수 없습니다: {title}")
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
                self._log_action(f"마감 공고 알림 확인: {alert_message} (공고: {title})")
                return None

            body = self.wait_for_element(
                (By.TAG_NAME, "body"),
                f"'{title}' 상세 본문",
            )
            return " ".join(body.text.split())
        finally:
            if detail_handle and detail_handle in self.browser.window_handles:
                self.browser.close()
            if original_handle in self.browser.window_handles:
                self.browser.switch_to.window(original_handle)
                self.wait_for_elements(job_items, "공고 목록 유지")

    def _select_include_keywords_only(self):
        """업직종 조건을 선택하지 않고 상세조건 포함 키워드만 입력한다."""
        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-3']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-3']"),
            "상세조건 탭",
        )
        self.sleep()

        keyword_input = (
            By.XPATH,
            "//input[@placeholder='입력 단어 포함 공고만 검색합니다.']",
        )
        self.wait_for_element(keyword_input, "포함 키워드 입력란")
        for keyword in self.KEYWORDS:
            self.browser.find_element(*keyword_input).send_keys(keyword, Keys.ENTER)
            self.wait.until(
                lambda driver, value=keyword: driver.find_element(*keyword_input)
                .get_attribute("value") == value
            )


    def _go_to_next_page(self, next_page_locator, current_page, job_items):
        """다음 페이지로 이동하고 SPA 전환이 실패하면 현재 조건 URL을 유지해 재접속한다."""
        target_page = current_page + 1
        items = self.browser.find_elements(*job_items)
        previous_title = items[0].find_element(By.CSS_SELECTOR, "a.list-item-recruit__link").text
        current_url = self.browser.current_url
        self.click_element(next_page_locator, f"{target_page}페이지 공고 목록 이동")

        def page_changed(driver):
            try:
                if f"page={target_page}" in driver.current_url:
                    return True
                current_items = driver.find_elements(*job_items)
                if not current_items:
                    return False
                title = current_items[0].find_element(By.CSS_SELECTOR, "a.list-item-recruit__link").text
                return bool(title) and title != previous_title
            except StaleElementReferenceException:
                return False

        try:
            self.wait.until(page_changed)
        except Exception:
            parts = urlsplit(current_url)
            query = [(key, str(target_page) if key == "page" else value)
                     for key, value in parse_qsl(parts.query, keep_blank_values=True)]
            if not any(key == "page" for key, _ in query):
                query.append(("page", str(target_page)))
            target_url = urlunsplit((parts.scheme, parts.netloc, parts.path,
                                     urlencode(query, doseq=True), parts.fragment))
            self._log_action(f"페이지 전환 미감지, 조건 유지 URL로 이동: {target_url}")
            self.browser.get(target_url)
            self.wait_for_elements(job_items, f"{target_page}페이지 공고 목록")
        return target_page

    def _run_include_keyword_test(self):
        """설정된 포함 키워드가 공고에 적용되는지 검증한다."""
        self.load()
        self._select_include_keywords_only()

        job_items = (By.XPATH, "//ul[contains(@class, 'SimpleRecruitList')]//li")
        page = 1
        checked_jobs = 0
        while checked_jobs < self.MAX_JOBS:
            try:
                self.wait_for_elements(job_items, f"{page}페이지 공고 목록")
                items = self.browser.find_elements(*job_items)
                self.assertTrue(items, f"{page}페이지에 공고가 없습니다.")
                invalid_jobs = []
                remaining_jobs = self.MAX_JOBS - checked_jobs
                for item in items[:remaining_jobs]:
                    title = item.find_element(By.CSS_SELECTOR, "a.list-item-recruit__link").text
                    detail = self._get_detail_text(
                        item.find_element(By.CSS_SELECTOR, "a.list-item-recruit__link"),
                        title,
                        job_items,
                    )
                    valid = detail is not None and all(
                        keyword in detail for keyword in self.KEYWORDS
                    )
                    if not valid:
                        invalid_jobs.append(title)
                    checked_jobs += 1
                self.assertFalse(invalid_jobs, f"조건에 맞지 않는 공고가 있습니다: {invalid_jobs}")

                if checked_jobs >= self.MAX_JOBS:
                    break

                next_page = (By.XPATH,
                              f"//*[@role='navigation']//button[contains(@aria-label, 'goto {page + 1} in')]")
                if not self.scroll_to_pagination(next_page):
                    break
                page = self._go_to_next_page(next_page, page, job_items)
            except Exception as exc:
                self.fail(f"{page}페이지 포함 키워드 공고 검증 중 오류가 발생했습니다: {exc}")

    def test_apply_include_keyword(self):
        """AI 포함 키워드 적용 후 공고가 1개 이상 조회되는지만 확인한다."""
        self.load()
        self._select_include_keywords_only()

        total_count = self._read_total_job_count()
        self._log_action(f"전체 공고 수 확인: 총{total_count}건")
        self.assertGreaterEqual(
            total_count,
            1,
            "AI 포함 키워드 적용 후 전체 공고 수가 1건 미만입니다.",
        )
        self.sleep()

    def _read_total_job_count(self):
        """화면의 '총 439건' 표시에서 전체 공고 수를 읽는다."""
        total_count_locator = (
            By.XPATH,
            "//*[contains(normalize-space(.), '총') "
            "and contains(normalize-space(.), '건')]",
        )

        return self.wait.until(
            lambda driver: self._extract_total_count(driver, total_count_locator)
        )

    @staticmethod
    def _extract_total_count(driver, locator):
        """주어진 locator에서 가장 작은 '총 N건' 숫자를 반환한다."""
        counts = []
        for element in driver.find_elements(*locator):
            match = re.search(r"총\s*([\d,]+)\s*건", element.text)
            if match:
                counts.append(int(match.group(1).replace(",", "")))
        return min(counts) if counts else False

    def tearDown(self):
        super().dispose()
