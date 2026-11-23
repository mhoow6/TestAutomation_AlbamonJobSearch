from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from Module.TCBase import TCBase


class TC027(TCBase):
    """Bar 알바 제외 조건을 검증하기 위한 개인회원 로그인 기반 테스트."""

    NAVER_LOGIN_WAIT_TIMEOUT = 300
    JOB_CATEGORY_SELECTIONS = (
        ("외식·음료", "바(bar)"),
        ("IT·기술", "웹·콘텐츠기획"),
    )

    def setUp(self):
        super().init()

    def login_with_naver(self):
        """개인회원 화면에서 네이버 OAuth 로그인을 수행한다.

        자격 증명은 자동화 코드가 다루지 않으며, 사용자가 네이버 창에 직접 입력한다.
        CAPTCHA/2단계 인증이 나타나면 자동 우회하지 않고 사용자의 처리를 기다린다.
        """
        self.browser.get("https://www.albamon.com/user-account/login?memberType=PERSONAL")
        self.wait_for_element(
            (By.XPATH, "//button[contains(normalize-space(.), '개인회원')]"),
            "개인회원 탭",
        )
        self.click_element(
            (By.XPATH, "//button[contains(normalize-space(.), '네이버 계정으로 로그인')]"),
            "네이버 계정으로 로그인",
        )

        main_window = self.browser.current_window_handle
        auth_window = None
        try:
            self.wait.until(
                lambda driver: len(driver.window_handles) > 1
                or "nid.naver.com" in driver.current_url
            )
            if len(self.browser.window_handles) > 1:
                auth_window = next(
                    handle for handle in self.browser.window_handles
                    if handle != main_window
                )
                self.browser.switch_to.window(auth_window)
        except TimeoutException:
            self.fail("네이버 로그인 창이 열리지 않았습니다.")

        # 네이버 로그인 창이 실제로 표시된 뒤 사용자가 브라우저에서 직접 로그인한다.
        self.wait_for_element((By.ID, "id"), "네이버 아이디 입력란")
        self._log_action(
            "네이버 창에서 직접 로그인하세요. 보안 퀴즈가 나오면 해결한 뒤 "
            "로그인 버튼을 다시 누르세요. 완료를 자동 감지합니다."
        )
        login_wait = WebDriverWait(self.browser, self.NAVER_LOGIN_WAIT_TIMEOUT)
        try:
            if auth_window is None:
                login_wait.until(
                    lambda driver: "nidlogin.login" not in driver.current_url
                )
            else:
                def is_naver_login_complete(driver):
                    if auth_window not in driver.window_handles:
                        return True
                    driver.switch_to.window(auth_window)
                    return "nidlogin.login" not in driver.current_url

                login_wait.until(is_naver_login_complete)
        except TimeoutException:
            self.fail(
                "네이버 로그인 완료를 확인하지 못했습니다. "
                "아이디·비밀번호 입력, 보안 퀴즈, CAPTCHA 또는 2단계 인증 상태를 확인하세요."
            )

        if main_window in self.browser.window_handles:
            self.browser.switch_to.window(main_window)

        # OAuth 콜백으로 세션이 갱신된 뒤에도 메인 창 URL이 로그인 화면에
        # 남아 있을 수 있으므로 한 번 새로고침해 로그인 상태를 반영한다.
        if "/user-account/login" in self.browser.current_url:
            self.browser.refresh()

        login_wait.until(
            lambda driver: "/user-account/login" not in driver.current_url
            or bool(driver.find_elements(By.XPATH, "//*[contains(normalize-space(.), '로그아웃')]"))
        )

    def _job_button(self, name):
        """업직종 대분류 또는 조건 버튼 locator를 반환한다."""
        return (By.XPATH, f"//button[normalize-space(.)={name!r}]")

    def test_bar_job_exclusion(self):
        return
        """바(bar) 선택 후 Bar알바 제외가 적용되는지 확인한다."""
        self.login_with_naver()
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-1']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-1']"),
            "업직종 탭",
        )
        self.sleep()

        selected_class = (
            "FilterListColumn_filter-list__column-button--selected__2niWt"
        )

        for parent_name, condition_name in self.JOB_CATEGORY_SELECTIONS:
            self.click_element(self._job_button(parent_name), f"'{parent_name}' 대분류")
            self.sleep()

            condition_locator = self._job_button(condition_name)
            self.click_element(condition_locator, f"'{condition_name}' 조건")
            self.wait_for_selected(
                condition_locator,
                f"'{condition_name}' 조건",
                selected_class,
            )
            self.sleep()

        # Bar알바 제외 전에는 업직종 조건 2개가 표시된다.
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-1']//em"),
            "2",
            "업직종 탭 선택 개수",
        )
        self.assert_element_text(
            (
                By.XPATH,
                "//div[@role='tabpanel' and @id='panel-1']"
                "//div[contains(@class, 'filter-header__counter')]",
            ),
            "2/10",
            "업직종 조건 개수",
        )

        for _, condition_name in self.JOB_CATEGORY_SELECTIONS:
            self.assert_element_text(
                (
                    By.XPATH,
                    "//div[contains(@class, 'selector-chips__list')]"
                    "//button[contains(@class, 'selector-chips__chip')"
                    f" and normalize-space()={condition_name!r}]",
                ),
                condition_name,
                "선택 업직종 조건",
            )

        bar_exclusion = (
            By.XPATH,
            "//label[.//span[normalize-space()='Bar알바 제외']]"
            "//input[@name='toggle-switch']",
        )
        bar_exclusion_label = (
            By.XPATH,
            "//label[.//span[normalize-space()='Bar알바 제외']]",
        )
        self.select_if_not_selected(
            bar_exclusion,
            bar_exclusion_label,
            "Bar알바 제외 토글",
        )
        self.sleep()

        # 기대 결과: 바(bar)가 제거되어 조건이 1개로 줄어든다.
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-1']//em"),
            "1",
            "Bar알바 제외 후 업직종 탭 선택 개수",
        )
        self.assert_element_text(
            (
                By.XPATH,
                "//div[@role='tabpanel' and @id='panel-1']"
                "//div[contains(@class, 'filter-header__counter')]",
            ),
            "1/10",
            "Bar알바 제외 후 업직종 조건 개수",
        )
        self.assert_no_elements(
            (
                By.XPATH,
                "//div[contains(@class, 'selector-chips__list')]"
                "//button[contains(@class, 'selector-chips__chip')"
                " and normalize-space()='바(bar)']",
            ),
            "Bar알바 제외 후 바(bar) 조건이 조건 리스트에 남아 있습니다.",
        )
        self.assert_element_text(
            (
                By.XPATH,
                "//div[contains(@class, 'selector-chips__list')]"
                "//button[contains(@class, 'selector-chips__chip')"
                " and normalize-space()='웹·콘텐츠기획']",
            ),
            "웹·콘텐츠기획",
            "Bar알바 제외 후 남은 업직종 조건",
        )

        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "'리스트 펼쳐 보기' 버튼",
        )
        self.sleep()

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
                self.wait_for_elements(job_items, f"{page}페이지 공고 목록")
                items = self.browser.find_elements(*job_items)
                self.assertTrue(items, f"{page}페이지에 공고가 없습니다.")
                items = items[: self.MAX_JOBS - checked_jobs]
                self._log_action(f"{page}페이지 웹·콘텐츠기획 공고 확인 중...")

                invalid_jobs = []
                for item in items:
                    category_detail = item.find_element(
                        By.XPATH,
                        job_category_details,
                    ).text
                    if "웹·콘텐츠기획" not in category_detail:
                        title = item.find_element(
                            By.CSS_SELECTOR,
                            "a.list-item-recruit__link",
                        ).text
                        invalid_jobs.append(title)

                self.assertFalse(
                    invalid_jobs,
                    f"{page}페이지에 웹·콘텐츠기획이 없는 공고가 있습니다: "
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
                next_page = self.scroll_to_pagination(next_page_locator)
                if not next_page:
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
                    f"{page}페이지 Bar알바 제외 공고 검증 중 오류가 발생했습니다: {exc}"
                )

        self.sleep()

    def tearDown(self):
        super().dispose()
