import re

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from TestCase.TC044 import TC044


class TC045(TC044):
    """근무요일 복수 조건을 선택했을 때 공고를 검증한다."""

    @staticmethod
    def _is_allowed_detail_work_day(detail_work_day):
        """상세 근무요일이 월~금 또는 토·일인지 판정한다."""
        normalized = "".join(detail_work_day.split())
        return (
            "월~금" in normalized
            or ("월" in normalized and "화" in normalized and "수" in normalized
                and "목" in normalized and "금" in normalized)
            or ("토" in normalized and "일" in normalized)
        )

    def test_apply_single_work_day_condition(self):
        """월~금과 주말(토,일) 선택 후 허용된 공고만 조회되는지 확인한다."""
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

        weekday_names = ("월~금", "주말(토,일)")
        for weekday_name in weekday_names:
            weekday_input = (
                By.XPATH,
                f"//label[.//span[normalize-space()={weekday_name!r}]]"
                "//input[@type='checkbox' and @name='dutyWeeks']",
            )
            weekday_click_target = (
                By.XPATH,
                f"//label[.//span[normalize-space()={weekday_name!r}]]"
                "//input[@type='checkbox' and @name='dutyWeeks']"
                "/ancestor::label[1]",
            )
            self.sleep()
            self.click_element(weekday_click_target, f"'{weekday_name}' 조건")
            self.wait_for_selected(weekday_input, f"'{weekday_name}' 조건")
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
            "근무요일 '협의 제외' 기본 선택",
        )

        weekday_panel = "//div[@role='tabpanel' and @id='panel-2']"
        weekday_counter = (
            By.XPATH,
            f"{weekday_panel}//div[contains(@class, 'filter-work-day__title-box__counter')]",
        )
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-2']//em"),
            "2",
            "근무요일 복수 선택 후 근무기간 탭 선택 개수",
        )
        self.assert_element_text(weekday_counter, "(2/3)", "근무요일 조건 개수")

        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )
        for weekday_name in weekday_names:
            self.assert_element_text(
                (By.XPATH, f"{chip_base}[normalize-space(.)={weekday_name!r}]"),
                weekday_name,
                f"조건 리스트의 {weekday_name} 조건",
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
                self._log_action(f"{page}페이지 복수 근무요일 공고 확인 중...")

                invalid_jobs = []
                item_count = len(items)
                for index in range(1, item_count + 1):
                    current_items = self.browser.find_elements(*job_items)
                    self.assertGreaterEqual(
                        len(current_items),
                        index,
                        f"{page}페이지 {index}번 공고를 다시 찾지 못했습니다.",
                    )
                    item = current_items[index - 1]
                    title = item.find_element(
                        By.CSS_SELECTOR,
                        "a.list-item-recruit__link",
                    ).text
                    detail_link = item.find_element(
                        By.CSS_SELECTOR,
                        "a.list-item-recruit__link",
                    )
                    work_day_detail = " ".join(
                        " ".join(element.text.split())
                        for element in item.find_elements(By.XPATH, work_day_details)
                    ).strip() or "확인 불가"
                    weekday_match = re.search(
                        r"(월~금|주말\(토,일\)|주\d일|요일\s*협의)\s*$",
                        work_day_detail,
                    )
                    weekday_detail = (
                        weekday_match.group(1)
                        if weekday_match
                        else "확인 불가"
                    )
                    duration_detail = (
                        work_day_detail[:weekday_match.start()].strip()
                        if weekday_match
                        else work_day_detail
                    )

                    detail_work_day = ""
                    if weekday_detail not in weekday_names:
                        detail_work_day = self._get_detail_work_day(detail_link, title)
                        if detail_work_day is None:
                            continue
                        is_allowed_work_day = self._is_allowed_detail_work_day(
                            detail_work_day
                        )
                    else:
                        is_allowed_work_day = True

                    self._log_action(
                        f"{page}페이지 {index}번 공고 기간: {duration_detail}, "
                        f"근무요일: {weekday_detail}, "
                        f"검증: {'통과' if is_allowed_work_day else '실패'}"
                        f"{f' / 상세: {detail_work_day}' if detail_work_day else ''} "
                        f"(공고: {title})"
                    )
                    if not is_allowed_work_day:
                        invalid_jobs.append(
                            f"{title} [기간: {duration_detail} / "
                            f"근무요일: {weekday_detail}]"
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

                def get_current_titles(driver):
                    try:
                        current_items = driver.find_elements(*job_items)
                        current_titles = tuple(
                            item.find_element(
                                By.CSS_SELECTOR,
                                "a.list-item-recruit__link",
                            ).text
                            for item in current_items
                        )
                        return current_titles or False
                    except StaleElementReferenceException:
                        return False

                previous_titles = self.wait.until(get_current_titles)
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
                    f"{page}페이지 근무요일 복수 조건 공고 검증 중 오류가 발생했습니다: "
                    f"{exc}"
                )

        self.sleep()
