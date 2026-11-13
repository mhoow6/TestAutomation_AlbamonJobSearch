from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC035(TCBase):
    """조건 리스트의 X 버튼으로 업직종 조건을 삭제했을 때를 확인한다."""

    def setUp(self):
        super().init()

    def test_delete_job_category_condition_from_chip(self):
        """웹·콘텐츠기획 칩 삭제 후 사이트관리·기술지원 공고만 검증한다."""
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
        parent_locator = (
            By.XPATH,
            "//li[@role='button' and normalize-space(.)='IT·기술']",
        )
        self.click_element(parent_locator, "'IT·기술' 대분류")
        self.sleep()

        web_condition = (
            By.XPATH,
            "//li[@role='button' and normalize-space(.)='웹·콘텐츠기획']",
        )
        site_condition = (
            By.XPATH,
            "//li[@role='button' and normalize-space(.)='사이트관리·기술지원']",
        )
        for condition_locator, condition_name in (
            (web_condition, "웹·콘텐츠기획"),
            (site_condition, "사이트관리·기술지원"),
        ):
            self.click_element(condition_locator, f"'{condition_name}' 조건")
            self.wait_for_selected(
                condition_locator,
                f"'{condition_name}' 조건",
                selected_class,
            )

        counter_locator = (
            By.XPATH,
            "//div[@role='tabpanel' and @id='panel-1']"
            "//div[contains(@class, 'filter-header__counter')]",
        )
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-1']//em"),
            "2",
            "삭제 전 업직종 탭 선택 개수",
        )
        self.assert_element_text(counter_locator, "2/10", "삭제 전 업직종 조건 개수")

        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )
        web_chip = (
            By.XPATH,
            f"{chip_base}[normalize-space(.)='웹·콘텐츠기획']",
        )
        self.highlight_element(web_chip, "삭제할 웹·콘텐츠기획 조건")
        self.click_element(web_chip, "조건 리스트의 웹·콘텐츠기획 X 버튼")

        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-1']//em"),
            "1",
            "삭제 후 업직종 탭 선택 개수",
        )
        self.assert_element_text(counter_locator, "1/10", "삭제 후 업직종 조건 개수")

        self.wait.until(
            lambda driver: not any(
                chip.is_displayed()
                for chip in driver.find_elements(*web_chip)
            )
        )
        self.assert_element_text(
            (
                By.XPATH,
                f"{chip_base}[normalize-space(.)='사이트관리·기술지원']",
            ),
            "사이트관리·기술지원",
            "삭제 후 남은 사이트관리·기술지원 조건",
        )

        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "공고 리스트 그리드뷰 전환",
        )

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

        while True:
            try:
                self.wait_for_elements(job_items, f"{page}페이지 공고 목록")
                items = self.browser.find_elements(*job_items)
                self.assertTrue(items, f"{page}페이지에 공고가 없습니다.")
                self._log_action(f"{page}페이지 공고 업직종 확인 중...")

                invalid_jobs = []
                for item in items:
                    category_detail = item.find_element(
                        By.XPATH,
                        job_category_details,
                    ).text
                    if "사이트관리·기술지원" not in category_detail:
                        invalid_jobs.append(
                            item.find_element(
                                By.CSS_SELECTOR,
                                "a.list-item-recruit__link",
                            ).text
                        )

                self.assertFalse(
                    invalid_jobs,
                    f"{page}페이지에 사이트관리·기술지원이 없는 공고가 있습니다: "
                    f"{invalid_jobs}",
                )

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
                    f"{page}페이지 조건 리스트 삭제 후 공고 검증 중 오류가 발생했습니다: "
                    f"{exc}"
                )

        self.sleep()

    def tearDown(self):
        super().dispose()
