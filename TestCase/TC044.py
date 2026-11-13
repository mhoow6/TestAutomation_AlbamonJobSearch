import re

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC044(TCBase):
    """근무요일 목록에서 조건을 단일 선택했을 때 적용되는지 검증한다."""

    WEEKDAY_ORDER = ("월", "화", "수", "목", "금", "토", "일")
    WEEKDAY_CONDITIONS = (
        "월~일",
        "월~토",
        "주말(토,일)",
        "주6일",
        "주5일",
        "주4일",
        "주3일",
        "주1일",
    )

    def setUp(self):
        super().init()

    @staticmethod
    def _extract_displayed_work_day(detail_work_day):
        """근무요일 행 오른쪽의 첫 표시값만 추출한다."""
        normalized = " ".join(detail_work_day.split())
        displayed_match = re.search(
            r"(월~일|월~토|월~금|주말\(토,일\)|주\d일)",
            normalized,
        )
        if displayed_match:
            return displayed_match.group(1)

        displayed = re.split(
            r"\s+(?:협의|평일|근무)|\s+\d+\s*일",
            normalized,
            maxsplit=1,
        )[0].strip()
        repeated_weekday = re.fullmatch(
            r"([월화수목금토일])(?:\s+\1)+",
            displayed,
        )
        return repeated_weekday.group(1) if repeated_weekday else displayed

    @classmethod
    def _extract_detail_weekdays(cls, detail_work_day):
        """상세 근무요일에서 실제 요일 집합을 추출한다."""
        # "토, 일 2일"에서 숫자 뒤의 "일"은 일요일이 아니므로 제외한다.
        weekday_text = re.sub(r"\d+\s*일", "", detail_work_day)
        weekday_ranges = re.findall(
            r"([월화수목금토일])\s*~\s*([월화수목금토일])",
            weekday_text,
        )
        if weekday_ranges:
            weekdays = set()
            for start, end in weekday_ranges:
                start_index = cls.WEEKDAY_ORDER.index(start)
                end_index = cls.WEEKDAY_ORDER.index(end)
                weekdays.update(cls.WEEKDAY_ORDER[start_index : end_index + 1])
            return weekdays

        weekday_text = re.split(r"협의|평일|근무", weekday_text, maxsplit=1)[0]
        weekdays = set(re.findall(r"[월화수목금토일]", weekday_text))
        return weekdays

    @classmethod
    def _is_allowed_detail_work_day(cls, condition, detail_work_day):
        """상세 근무요일이 선택한 목록 조건과 일치하는지 판정한다."""
        normalized_condition = "".join(condition.split())
        normalized_detail = "".join(detail_work_day.split())
        if normalized_detail == normalized_condition:
            return True

        weekdays = cls._extract_detail_weekdays(detail_work_day)
        expected_ranges = {
            "월~일": set(cls.WEEKDAY_ORDER),
            "월~토": set(cls.WEEKDAY_ORDER[:-1]),
            "주말(토,일)": {"토", "일"},
        }
        if condition in expected_ranges:
            return weekdays == expected_ranges[condition]

        day_count_match = re.fullmatch(r"주(\d)일", condition)
        return bool(day_count_match and len(weekdays) == int(day_count_match.group(1)))

    def _select_weekday_condition(self, condition):
        condition_input = (
            By.XPATH,
            f"//label[.//span[normalize-space()={condition!r}]]"
            "//input[@type='checkbox' and @name='dutyWeeks']",
        )
        condition_click = (
            By.XPATH,
            f"//label[.//span[normalize-space()={condition!r}]]"
            "//input[@type='checkbox' and @name='dutyWeeks']"
            "/ancestor::label[1]",
        )
        self.click_element(condition_click, f"'{condition}' 조건")
        self.wait_for_selected(condition_input, f"'{condition}' 조건")
        return condition_input, condition_click

    def _verify_selected_condition_jobs(self, condition, job_items):
        page = 1
        checked_jobs = 0

        while checked_jobs < self.MAX_JOBS:
            try:
                self.wait_for_elements(job_items, f"{condition} {page}페이지 공고 목록")
                items = self.browser.find_elements(*job_items)
                self.assertTrue(
                    items,
                    f"{condition} {page}페이지에 공고가 없습니다.",
                )
                invalid_jobs = []
                remaining_jobs = self.MAX_JOBS - checked_jobs

                for index in range(1, min(len(items), remaining_jobs) + 1):
                    current_items = self.browser.find_elements(*job_items)
                    item = current_items[index - 1]
                    title = item.find_element(
                        By.CSS_SELECTOR,
                        "a.list-item-recruit__link",
                    ).text
                    detail_link = item.find_element(
                        By.CSS_SELECTOR,
                        "a.list-item-recruit__link",
                    )
                    raw_detail_work_day = self._get_detail_work_day(detail_link, title)
                    detail_work_day = (
                        self._extract_displayed_work_day(raw_detail_work_day)
                        if raw_detail_work_day is not None
                        else None
                    )
                    is_allowed = (
                        detail_work_day is not None
                        and self._is_allowed_detail_work_day(
                            condition,
                            detail_work_day,
                        )
                    )

                    self._log_action(
                        f"{condition} {page}페이지 {index}번 공고 | "
                        f"상세 근무요일: {detail_work_day or '확인 불가'} | "
                        f"검증: {'통과' if is_allowed else '실패'}"
                        f"{f' / 상세: {detail_work_day}' if detail_work_day else ''}"
                    )
                    if not is_allowed:
                        invalid_jobs.append(
                            f"{title} [상세 근무요일: {detail_work_day or '확인 불가'}"
                            f"{f' / 상세: {detail_work_day}' if detail_work_day else ''}]"
                        )
                    checked_jobs += 1

                self.assertFalse(
                    invalid_jobs,
                    f"{condition} 조건과 맞지 않는 공고가 있습니다: {invalid_jobs}",
                )
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
                    f"{condition} {page}페이지 공고 검증 중 오류가 발생했습니다: {exc}"
                )

    def test_apply_single_work_day_condition(self):
        """근무요일 조건을 하나씩 선택하고 결과를 확인한 뒤 해제한다."""
        self.load()

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

        self.click_element((By.ID, "select-size"), "공고 목록 노출 개수 선택")
        self.click_element(
            (By.XPATH, "//button[normalize-space()='50개씩']"),
            "공고 50개씩 보기",
        )
        self.wait.until(
            lambda driver: driver.find_element(By.ID, "select-size").text.strip()
            == "50개씩"
        )

        job_items = (By.XPATH, "//ul[contains(@class, 'SimpleRecruitList')]//li")
        self.wait_for_recruit_list_rendered(job_items, "50개 보기 적용 후 공고 목록")
        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "공고 리스트 그리드뷰 전환",
        )
        self.wait_for_recruit_list_rendered(job_items, "그리드뷰 전환 후 공고 목록")

        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )
        weekday_panel = "//div[@role='tabpanel' and @id='panel-2']"
        weekday_counter = (
            By.XPATH,
            f"{weekday_panel}//div[contains(@class, 'filter-work-day__title-box__counter')]",
        )
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

        for condition in self.WEEKDAY_CONDITIONS:
            condition_input, condition_click = self._select_weekday_condition(condition)
            self.sleep()
            self.select_if_not_selected(
                exclude_negotiation,
                exclude_negotiation_click,
                f"'{condition}' 선택 후 근무요일 '협의 제외' 조건",
            )
            self.assert_element_text(
                (By.XPATH, "//label[@role='tab' and @for='tab-2']//em"),
                "1",
                f"{condition} 선택 후 근무기간 탭 선택 개수",
            )
            self.assert_element_text(
                weekday_counter,
                "(1/3)",
                f"{condition} 선택 후 근무요일 조건 개수",
            )
            self.assert_element_text(
                (By.XPATH, f"{chip_base}[normalize-space(.)={condition!r}]"),
                condition,
                f"조건 리스트의 {condition} 조건",
            )
            self.wait_for_recruit_list_rendered(
                job_items,
                f"{condition} 조건 적용 후 공고 목록",
            )
            self._verify_selected_condition_jobs(condition, job_items)

            self.click_element(condition_click, f"'{condition}' 조건 해제")
            self.wait_for_not_selected(condition_input, f"해제된 '{condition}' 조건")
            self.wait_for_recruit_list_rendered(
                job_items,
                f"{condition} 조건 해제 후 공고 목록",
            )

    def tearDown(self):
        super().dispose()
