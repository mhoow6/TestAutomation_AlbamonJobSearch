import re

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC049(TCBase):
    """협의 제외를 해제했을 때 요일 협의 공고가 함께 조회되는지 검증한다."""

    EXPECTED_WEEKDAY_TYPES = ("주말(토,일)", "주2일", "요일 협의")

    def setUp(self):
        super().init()

    def test_include_negotiable_work_day_jobs(self):
        """협의 제외 해제 후 주말·주2일·요일 협의 공고를 확인한다."""
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

        # 테스트 절차: 협의 제외를 해제해 요일 협의 공고를 포함한다.
        self.highlight_element(
            exclude_negotiation_click,
            "협의 제외 체크박스 해제",
        )
        self.click_element(exclude_negotiation_click, "협의 제외 체크박스 해제")
        self.wait_for_not_selected(exclude_negotiation, "해제된 협의 제외")
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
                self._log_action(f"{page}페이지 공고 기간/요일 확인 중...")

                invalid_jobs = []
                for index in range(1, len(items) + 1):
                    # 상세 페이지 방문 후 목록 DOM이 갱신되므로 매번 다시 찾는다.
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
                    work_day_detail = " ".join(
                        " ".join(element.text.split())
                        for element in item.find_elements(By.XPATH, work_day_details)
                    ).strip() or "확인 불가"
                    normalized_work_day = "".join(work_day_detail.split())
                    detail_work_day = ""

                    is_two_day_job = "주2일" in normalized_work_day
                    if is_two_day_job:
                        detail_link = item.find_element(
                            By.CSS_SELECTOR,
                            "a.list-item-recruit__link",
                        )
                        detail_work_day = self._get_detail_work_day(detail_link, title)
                        if detail_work_day is None:
                            continue
                        normalized_detail_work_day = "".join(
                            (detail_work_day or "").split()
                        )
                        weekday_count = sum(
                            day in normalized_detail_work_day
                            for day in ("월", "화", "수", "목", "금", "토", "일")
                        )
                        is_allowed_work_day = weekday_count >= 2
                    else:
                        is_allowed_work_day = any(
                            "".join(weekday_type.split()) in normalized_work_day
                            for weekday_type in self.EXPECTED_WEEKDAY_TYPES
                        )
                    self._log_action(
                        f"{page}페이지 {index}번 공고 | "
                        f"기간/요일: {work_day_detail} | "
                        f"검증: {'통과' if is_allowed_work_day else '실패'}"
                        f"{f' / 상세 근무요일: {detail_work_day}' if detail_work_day else ''}"
                    )
                    if not is_allowed_work_day:
                        invalid_jobs.append(
                            f"{title} [기간/요일: {work_day_detail}]"
                        )

                self.assertFalse(
                    invalid_jobs,
                    f"{page}페이지에 조건과 맞지 않는 공고가 있습니다: {invalid_jobs}",
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

                items = self.browser.find_elements(*job_items)
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
                    f"{page}페이지 요일 협의 공고 검증 중 오류가 발생했습니다: "
                    f"{exc}"
                )

        # 조회된 공고가 허용된 3가지 근무요일 유형 중 하나인지 여부는
        # 각 공고를 처리하는 동안 invalid_jobs로 검증한다.

    def tearDown(self):
        super().dispose()
