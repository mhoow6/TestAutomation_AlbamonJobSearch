from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC037(TCBase):
    """최대 개수의 동일 업직종 조건을 전체 조건으로 전환한다."""

    CONDITIONS = (
        "입시·보습학원",
        "외국어·어학원",
        "독서·논술·스피치학원",
        "컴퓨터·정보통신",
        "요가·필라테스 강사",
        "피트니스 트레이너",
        "레져스포츠 강사",
        "예체능 강사",
        "유아·유치원",
        "등하원·승하차도우미",
    )
    SELECTED_CLASS = (
        "FilterListColumn_filter-list__column-button--selected__2niWt"
    )

    def setUp(self):
        super().init()

    def test_switch_to_all_same_job_category_condition(self):
        """10개 조건을 교육·강사 전체 조건으로 전환하고 공고를 검증한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-1']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-1']"),
            "업직종 탭",
        )
        self.sleep()
        self.click_element(
            (By.XPATH, "//li[@role='button' and normalize-space(.)='교육·강사']"),
            "'교육·강사' 대분류",
        )
        self.sleep()

        panel = "//div[@role='tabpanel' and @id='panel-1']"
        condition_items = (
            By.XPATH,
            f"{panel}//li[starts-with(@id, 'part-')]",
        )
        self.wait_for_elements(condition_items, "교육·강사 업직종 목록")

        # 교육 강사 업직종 목록 수집
        excluded_labels = {"교육·강사", "교육·강사 전체", "초기화"}
        education_job_categories = tuple(
            item.text.strip()
            for item in self.browser.find_elements(*condition_items)
            if item.text.strip() not in excluded_labels
        )
        self.assertGreaterEqual(
            len(education_job_categories),
            10,
            "교육·강사 업직종 목록이 10개보다 적습니다.",
        )

        # 테스트 절차: 테스트 케이스에 지정된 10개 조건을 선택한다.
        for condition_name in self.CONDITIONS:
            condition_locator = (
                By.XPATH,
                f"{panel}//*[self::li or self::button]["
                f"(@role='button' or self::button) and "
                f"normalize-space(.)={condition_name!r}]",
            )
            self.click_element(condition_locator, f"'{condition_name}' 조건")
            self.wait_for_selected(
                condition_locator,
                f"'{condition_name}' 조건",
                self.SELECTED_CLASS,
            )
            self.sleep()

        counter_locator = (
            By.XPATH,
            f"{panel}"
            "//div[contains(@class, 'filter-header__counter')]",
        )
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-1']//em"),
            "10",
            "전체 전환 전 업직종 탭 선택 개수",
        )
        self.assert_element_text(counter_locator, "10/10", "전체 전환 전 업직종 조건 개수")

        all_condition = (
            By.XPATH,
            f"{panel}//*[self::li or self::button]["
            "(@role='button' or self::button) and "
            "normalize-space(.)='교육·강사 전체']",
        )
        self.click_element(all_condition, "'교육·강사 전체' 조건")
        self.wait_for_selected(all_condition, "'교육·강사 전체' 조건", self.SELECTED_CLASS)

        # 기대 결과: 기존 10개 조건이 전체 조건 1개로 전환된다.
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-1']//em"),
            "1",
            "전체 전환 후 업직종 탭 선택 개수",
        )
        self.assert_element_text(counter_locator, "1/10", "전체 전환 후 업직종 조건 개수")

        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )
        self.assert_element_text(
            (By.XPATH, f"{chip_base}[normalize-space(.)='교육·강사 전체']"),
            "교육·강사 전체",
            "조건 리스트의 교육·강사 전체",
        )
        for condition_name in self.CONDITIONS:
            old_chip = (
                By.XPATH,
                f"{chip_base}[normalize-space(.)={condition_name!r}]",
            )
            self.wait.until(
                lambda driver, locator=old_chip: not any(
                    chip.is_displayed()
                    for chip in driver.find_elements(*locator)
                )
            )

        # 공고 목록 노출 개수를 20개에서 50개로 변경한다.
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

        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "공고 리스트 그리드뷰 전환",
        )

        # 기대 결과: 모든 페이지의 공고가 교육·강사 하위 업직종 중 하나를 포함한다.
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
                self._log_action(f"{page}페이지 교육·강사 전체 공고 확인 중...")

                invalid_jobs = []
                for item in items:
                    category_detail = item.find_element(
                        By.XPATH,
                        job_category_details,
                    ).text
                    if not any(
                        category in category_detail
                        for category in education_job_categories
                    ):
                        invalid_jobs.append(
                            item.find_element(
                                By.CSS_SELECTOR,
                                "a.list-item-recruit__link",
                            ).text
                        )

                self.assertFalse(
                    invalid_jobs,
                    f"{page}페이지에 교육·강사 업직종이 없는 공고가 있습니다: "
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
                    f"{page}페이지 교육·강사 전체 공고 검증 중 오류가 발생했습니다: "
                    f"{exc}"
                )

        self.sleep()

    def tearDown(self):
        super().dispose()
