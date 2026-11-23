import re

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC053(TCBase):
    """복수 근무요일을 직접 선택했을 때 조건이 적용되는지 검증한다."""

    SELECTED_WEEKDAYS = ("월", "화")

    def setUp(self):
        super().init()

    @classmethod
    def _is_allowed_work_day(cls, work_day):
        """월·화 중 하나라도 포함된 상세 근무요일인지 판정한다."""
        normalized = "".join(work_day.split())
        has_specific_period = re.search(
            r"\d{1,2}\.\d{1,2}~\d{1,2}\.\d{1,2}",
            normalized,
        ) is not None

        # 상세 페이지의 특정 근무기간(예: 11.25~11.26)은 선택 요일 조건에
        # 해당하는 공고로 인정한다.
        if has_specific_period:
            return True

        # "12월 28일부터는 화, 수"처럼 날짜에 포함된 '월'을 근무요일로
        # 오인하지 않도록 날짜 표기를 제거한 뒤 실제 요일을 검사한다.
        weekday_text = re.sub(r"\d{1,2}월\d{1,2}일?", "", normalized)

        # 조건을 여러 개 선택하면 공고 전체 일정 중 선택한 요일이 하나라도
        # 포함될 때 조회될 수 있다. 따라서 월·화가 모두 표시될 필요는 없다.
        return any(day in weekday_text for day in cls.SELECTED_WEEKDAYS)

    def test_apply_multiple_direct_work_days(self):
        """직접선택에서 월·화를 선택하면 해당 공고만 조회되는지 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-2']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            "근무기간 탭",
        )
        self.sleep()

        direct_option = (
            By.XPATH,
            "//label[.//span[normalize-space()='직접선택']]"
            "//input[@type='radio' and @name='dayWeeks']",
        )
        direct_option_click = (
            By.XPATH,
            "//label[.//span[normalize-space()='직접선택']]"
            "//input[@type='radio' and @name='dayWeeks']/ancestor::label[1]",
        )
        self.click_element(direct_option_click, "근무요일 '직접선택' 조건")
        self.wait_for_selected(direct_option, "근무요일 직접선택")
        self.sleep()

        for weekday_name, weekday_value in (("월", "MONDAY"), ("화", "TUESDAY")):
            weekday_input = (
                By.XPATH,
                f"//label[.//span[normalize-space()={weekday_name!r}]]"
                "//input[@type='checkbox' and @name='dayOfWeeks' "
                f"and @value='{weekday_value}']",
            )
            weekday_click = (
                By.XPATH,
                f"//label[.//span[normalize-space()={weekday_name!r}]]"
                "//input[@type='checkbox' and @name='dayOfWeeks' "
                f"and @value='{weekday_value}']/ancestor::label[1]",
            )
            self.click_element(weekday_click, f"직접선택 근무요일 '{weekday_name}' 조건")
            self.wait_for_selected(weekday_input, f"직접선택 근무요일 '{weekday_name}' 조건")
            self.sleep()

        exclude_negotiation = (
            By.XPATH,
            "//label[.//span[normalize-space()='협의 제외']]"
            "//input[@type='checkbox' and @name='dfa' and not(@disabled)]",
        )
        exclude_negotiation_click = (
            By.XPATH,
            "//label[.//span[normalize-space()='협의 제외']]"
            "//input[@type='checkbox' and @name='dfa' and not(@disabled)]"
            "/ancestor::label[1]",
        )
        self.select_if_not_selected(
            exclude_negotiation,
            exclude_negotiation_click,
            "근무요일 '협의 제외' 조건",
        )

        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-2']//em"),
            "1",
            "복수 근무요일 선택 후 근무기간 탭 선택 개수",
        )
        self.sleep()

        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )
        combined_weekday = "/".join(self.SELECTED_WEEKDAYS)
        self.assert_element_text(
            (By.XPATH, f"{chip_base}[normalize-space(.)={combined_weekday!r}]"),
            combined_weekday,
            "조건 리스트의 월/화 조건",
        )

        self.click_element((By.ID, "select-size"), "공고 목록 노출 개수 선택")
        self.click_element(
            (By.XPATH, "//button[normalize-space()='50개씩']"),
            "공고 50개씩 보기",
        )
        self.wait.until(
            lambda driver: driver.find_element(By.ID, "select-size").text.strip()
            == "50개씩"
        )
        self.sleep()

        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "공고 리스트 그리드뷰 전환",
        )
        self.sleep()

        job_items = (By.XPATH, "//ul[contains(@class, 'SimpleRecruitList')]//li")
        work_day_details = (
            ".//div[contains(@class, 'list-item-recruit-details__item')]"
            "[.//span[normalize-space()='기간/요일']]"
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
                invalid_jobs = []

                for index in range(1, len(items) + 1):
                    current_items = self.browser.find_elements(*job_items)
                    item = current_items[index - 1]
                    title = item.find_element(
                        By.CSS_SELECTOR,
                        "a.list-item-recruit__link",
                    ).text
                    listed_work_day = " ".join(
                        " ".join(element.text.split())
                        for element in item.find_elements(By.XPATH, work_day_details)
                    ).strip() or "확인 불가"
                    detail_link = item.find_element(
                        By.CSS_SELECTOR,
                        "a.list-item-recruit__link",
                    )
                    detail_work_day = self._get_detail_work_day(detail_link, title)
                    if detail_work_day is None:
                        continue

                    is_allowed_work_day = self._is_allowed_work_day(detail_work_day)
                    self._log_action(
                        f"{page}페이지 {index}번 공고 | "
                        f"목록 기간/요일: {listed_work_day} | "
                        f"상세 근무요일: {detail_work_day} | "
                        f"검증: {'통과' if is_allowed_work_day else '실패'}"
                    )
                    if not is_allowed_work_day:
                        invalid_jobs.append(
                            f"{title} [상세 근무요일: {detail_work_day}]"
                        )

                self.assertFalse(
                    invalid_jobs,
                    f"{page}페이지에 월·화 복수 조건과 맞지 않는 공고가 있습니다: {invalid_jobs}",
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
            except Exception as exc:
                self.fail(
                    f"{page}페이지 월·화 직접선택 공고 검증 중 오류가 발생했습니다: {exc}"
                )

    def tearDown(self):
        super().dispose()
