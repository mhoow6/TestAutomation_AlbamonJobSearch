from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC042(TCBase):
    """근무기간 조건을 삭제한 뒤 공고를 확인한다."""

    def setUp(self):
        super().init()

    def test_delete_duration_condition_from_chip(self):
        """하루(1일) 조건을 삭제하면 공고가 조회되는지 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-2']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            "근무기간 탭",
        )
        self.sleep()

        duration_panel = "//div[@role='tabpanel' and @id='panel-2']"
        one_day_input = (
            By.XPATH,
            "//input[@type='checkbox' and @name='dutyTerms' and @value='ONE_DAY']",
        )
        one_day_condition = (
            By.XPATH,
            f"{duration_panel}"
            "//input[@type='checkbox' and @name='dutyTerms' and @value='ONE_DAY']"
            "/ancestor::*[1]",
        )
        self.click_element(
            one_day_condition,
            "'하루(1일)' 조건",
        )
        self.wait_for_selected(one_day_input, "'하루(1일)' 조건")

        duration_counter = (
            By.XPATH,
            f"{duration_panel}//div[contains(@class, 'filter-toggle__title-box__counter')]",
        )
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-2']//em"),
            "1",
            "삭제 전 근무기간 탭 선택 개수",
        )
        self.assert_element_text(duration_counter, "(1/6)", "삭제 전 근무기간 조건 개수")

        # 근무기간 목록에서 선택된 '하루(1일)'을 다시 클릭해 해제한다.
        self.highlight_element(
            one_day_condition,
            "해제할 근무기간 목록의 '하루(1일)' 조건",
        )
        self.sleep()
        self.click_element(one_day_condition, "근무기간 목록의 '하루(1일)' 조건 해제")
        self.wait_for_not_selected(one_day_input, "근무기간 목록의 '하루(1일)' 조건")

        self.assert_no_elements(
            (By.XPATH, "//label[@role='tab' and @for='tab-2']//em"),
            "삭제 후 근무기간 탭 숫자가 남아 있습니다.",
        )
        self.assert_element_text(duration_counter, "(0/6)", "삭제 후 근무기간 조건 개수")

        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )

        self.click_element(
            (By.ID, "select-size"),
            "공고 목록 노출 개수 선택",
        )
        self.click_element(
            (By.XPATH, "//button[normalize-space()='50개씩']"),
            "공고 50개씩 보기",
        )
        self.wait.until(
            lambda driver: driver.find_element(By.ID, "select-size").text.strip()
            == "50개씩"
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
        page = 1

        while True:
            try:
                self.wait_for_elements(job_items, f"{page}페이지 공고 목록")
                items = self.browser.find_elements(*job_items)
                self.assertTrue(items, f"{page}페이지에 공고가 없습니다.")
                self._log_action(f"{page}페이지 공고 기간/요일 확인 중...")

                invalid_jobs = []
                for index, item in enumerate(items, start=1):
                    title = item.find_element(
                        By.CSS_SELECTOR,
                        "a.list-item-recruit__link",
                    ).text
                    duration_elements = item.find_elements(
                        By.XPATH,
                        duration_details,
                    )
                    duration_detail = " ".join(
                        " ".join(element.text.split())
                        for element in duration_elements
                    ).strip() or "확인 불가"
                    self._log_action(
                        f"{page}페이지 {index}번 공고 기간/요일: {duration_detail}"
                    )

                self.assertFalse(
                    invalid_jobs,
                    f"{page}페이지에 공고가 있습니다: {invalid_jobs}",
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
                    f"{page}페이지 근무기간 조건 삭제 후 공고 검증 중 오류가 발생했습니다: "
                    f"{exc}"
                )

        self.sleep()

    def tearDown(self):
        super().dispose()
