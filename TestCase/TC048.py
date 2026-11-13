from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC048(TCBase):
    """조건 리스트에서 근무요일 조건을 삭제했을 때의 동작을 검증한다."""

    def setUp(self):
        super().init()

    def test_delete_work_day_condition_from_chip(self):
        """주말 조건을 칩의 X 버튼으로 삭제하면 모든 근무요일 공고를 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-2']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            "근무기간 탭",
        )
        self.sleep()

        weekday_list_radio = (
            By.XPATH,
            "//input[@type='radio' and @name='dutyWeeks']",
        )
        self.wait_for_selected(weekday_list_radio, "근무요일 목록에서 선택")

        weekend_input = (
            By.XPATH,
            "//input[@type='checkbox' and @name='dutyWeeks' "
            "and @value='SATURDAY_AND_SUNDAY']",
        )
        weekend_click = (
            By.XPATH,
            "//input[@type='checkbox' and @name='dutyWeeks' "
            "and @value='SATURDAY_AND_SUNDAY']/ancestor::label[1]",
        )
        self.click_element(weekend_click, "'주말(토,일)' 조건")
        self.wait_for_selected(weekend_input, "'주말(토,일)' 조건")
        self.sleep()

        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )
        weekend_chip = (
            By.XPATH,
            f"{chip_base}[normalize-space(.)='주말(토,일)']",
        )
        self.assert_element_text(
            weekend_chip,
            "주말(토,일)",
            "사전 조건의 주말(토,일) 조건",
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
        self.sleep()

        # 테스트 절차: 조건 리스트의 주말(토,일) 칩 자체가 X 버튼이다.
        self.highlight_element(weekend_chip, "조건 리스트의 주말(토,일) X 버튼")
        self.click_element(weekend_chip, "조건 리스트의 주말(토,일) X 버튼")
        self.sleep()

        weekday_panel = "//div[@role='tabpanel' and @id='panel-2']"
        weekday_counter = (
            By.XPATH,
            f"{weekday_panel}//div[contains(@class, 'filter-work-day__title-box__counter')]",
        )
        self.assert_no_elements(
            (By.XPATH, "//label[@role='tab' and @for='tab-2']//em"),
            "삭제 후 근무요일 탭 숫자가 남아 있습니다.",
        )
        self.assert_element_text(weekday_counter, "(0/3)", "삭제 후 근무요일 조건 개수")
        self.assert_no_elements(
            weekend_chip,
            "조건 리스트에서 주말(토,일) 조건이 삭제되지 않았습니다.",
        )

        job_items = (By.XPATH, "//ul[contains(@class, 'SimpleRecruitList')]//li")
        work_day_details = (
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
                    work_day_detail = " ".join(
                        " ".join(element.text.split())
                        for element in item.find_elements(By.XPATH, work_day_details)
                    ).strip() or "확인 불가"
                    self._log_action(
                        f"{page}페이지 {index}번 공고 | "
                        f"기간/요일: {work_day_detail} | "
                        "검증: 통과"
                    )

                self.assertFalse(
                    invalid_jobs,
                    f"{page}페이지에 조건과 맞지 않는 공고가 있습니다: {invalid_jobs}",
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
                    f"{page}페이지 근무요일 조건 삭제 후 공고 검증 중 오류가 발생했습니다: "
                    f"{exc}"
                )

    def tearDown(self):
        super().dispose()
