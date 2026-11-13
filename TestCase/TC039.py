from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC039(TCBase):
    """근무기간 하루 조건의 공고를 검증한다."""

    def setUp(self):
        super().init()

    def test_apply_one_day(self):
        """하루(1일) 조건의 공고만 조회되는지 확인한다."""
        super().load()

        # 테스트 절차: 근무기간 탭에서 하루(1일)을 선택한다.
        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-2']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            "근무기간 탭",
        )
        self.sleep()
        duration_input = (
            By.XPATH,
            "//input[@type='checkbox' and @name='dutyTerms' and @value='ONE_DAY']",
        )
        duration_click_target = (
            By.XPATH,
            "//input[@type='checkbox' and @name='dutyTerms' and @value='ONE_DAY']"
            "/ancestor::*[1]",
        )
        self.click_element(duration_click_target, "'하루(1일)' 조건")
        self.wait_for_selected(duration_input, "'하루(1일)' 조건")

        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-2']//em"),
            "1",
            "근무기간 탭 선택 개수",
        )
        self.assert_element_text(
            (
                By.XPATH,
                "//div[@role='tabpanel' and @id='panel-2']"
                "//div[contains(@class, 'filter-toggle__title-box__counter')]",
            ),
            "(1/6)",
            "근무기간 조건 개수",
        )

        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )
        self.assert_element_text(
            (By.XPATH, f"{chip_base}[normalize-space()='하루(1일)']"),
            "하루(1일)",
            "조건 리스트의 하루(1일)",
        )

        # 공고 목록을 50개씩 표시하고 리스트 그리드뷰로 전환한다.
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

        job_items = (
            By.XPATH,
            "//ul[contains(@class, 'SimpleRecruitList')]//li",
        )
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
                self._log_action(f"{page}페이지 하루(1일) 공고 확인 중...")
                self._log_action(f"{page}페이지 현재 공고 카드 수: {len(items)}개")

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
                    # 화면/공고 유형에 따라 근무기간 상세 요소가 생략될 수
                    # 있으므로, 상세 요소가 없으면 카드 전체 텍스트를 확인한다.
                    duration_detail = " ".join(
                        element.text for element in duration_elements
                    ) or item.text
                    if "하루(1일)" not in duration_detail:
                        invalid_jobs.append(title)

                self.assertFalse(
                    invalid_jobs,
                    f"{page}페이지에 하루(1일) 조건이 아닌 공고가 있습니다: "
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
                    f"{page}페이지 하루(1일) 공고 검증 중 오류가 발생했습니다: "
                    f"{exc}"
                )

        self.sleep()

    def tearDown(self):
        super().dispose()
