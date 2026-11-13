import re

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC054(TCBase):
    """시간대 조건을 하나씩 선택했을 때 조건이 적용되는지 검증한다."""

    TIME_PARTS = (("오전 파트", "AM"),)
    ALLOWED_TIME_RANGES = ((6 * 60, 12 * 60),)
    SINGLE_TIME_PART_CASES = (
        ((("오전 파트", "AM"),), ((6 * 60, 12 * 60),)),
        ((("오후 파트", "PM"),), ((12 * 60, 18 * 60),)),
        ((("저녁 파트", "EVENING"),), ((18 * 60, 24 * 60),)),
        ((("새벽 파트", "DAWN"),), ((0, 6 * 60),)),
    )
    CURRENT_ALLOWED_TIME_RANGES = None

    def setUp(self):
        super().init()

    @classmethod
    def _is_allowed_work_time(cls, work_time):
        """근무시간이 파트와 겹치는지 판정한다."""
        normalized = "".join(work_time.split())
        time_matches = re.findall(
            r"(?P<start>\d{1,2}:\d{2})~(?P<end>\d{1,2}:\d{2})",
            normalized,
        )
        if not time_matches:
            return False

        for start_time, end_time in time_matches:
            start_hour, start_minute = map(int, start_time.split(":"))
            end_hour, end_minute = map(int, end_time.split(":"))
            start = start_hour * 60 + start_minute
            end = end_hour * 60 + end_minute
            if end <= start:
                end += 24 * 60

            # 자정을 넘기는 근무시간도 고려해 선택 구간을 하루씩 비교한다.
            for day_offset in (0, 24 * 60):
                allowed_ranges = (
                    getattr(cls, "CURRENT_ALLOWED_TIME_RANGES", None)
                    or cls.ALLOWED_TIME_RANGES
                )
                for range_start, range_end in allowed_ranges:
                    selected_start = range_start + day_offset
                    selected_end = range_end + day_offset
                    if start < selected_end and end > selected_start:
                        return True

        return False

    def _run_work_time_test(self):
        """설정된 근무시간 조건과 겹치는 공고만 조회되는지 확인한다."""
        # 특정 상속 순서에 의존하지 않게 하기 위해 super()대신 self.load()
        self.load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-2']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-2']"),
            "근무기간 탭",
        )
        self.sleep()

        for time_part_name, time_part_value in self.TIME_PARTS:
            time_condition = (
                By.XPATH,
                f"//label[.//span[normalize-space()={time_part_name!r}]]"
                "//input[@type='checkbox' and @name='workTimeType' "
                f"and @value='{time_part_value}']",
            )
            time_click = (
                By.XPATH,
                f"//label[.//span[normalize-space()={time_part_name!r}]]"
                "//input[@type='checkbox' and @name='workTimeType' "
                f"and @value='{time_part_value}']/ancestor::label[1]",
            )
            self.select_if_not_selected(
                time_condition,
                time_click,
                f"근무시간 '{time_part_name}' 조건",
            )
            self.sleep()

        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-2']//em"),
            str(len(self.TIME_PARTS)),
            "근무시간 조건 선택 후 근무기간 탭 선택 개수",
        )
        for time_part_name, _ in self.TIME_PARTS:
            self.assert_element_text(
                (
                    By.XPATH,
                    "//div[contains(@class, 'selector-chips__list')]"
                    "//button[contains(@class, 'selector-chips__chip') and "
                    f"normalize-space()={time_part_name!r}]",
                ),
                time_part_name,
                f"조건 리스트의 {time_part_name} 조건",
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
        job_items = (By.XPATH, "//ul[contains(@class, 'SimpleRecruitList')]//li")
        listed_work_times = (
            ".//div[contains(@class, 'list-item-recruit__contents--time')]//p"
        )
        self.wait_for_recruit_list_rendered(
            job_items,
            "50개 보기 적용 후 공고 목록",
        )
        self.wait.until(
            lambda driver: bool(driver.find_elements(*job_items))
            and all(
                item.find_elements(By.XPATH, listed_work_times)
                for item in driver.find_elements(*job_items)
            )
        )
        page = 1
        checked_jobs = 0

        while checked_jobs < self.MAX_JOBS:
            try:
                self.wait_for_elements(job_items, f"{page}페이지 공고 목록")
                items = self.browser.find_elements(*job_items)
                self.assertTrue(items, f"{page}페이지에 공고가 없습니다.")
                invalid_jobs = []

                remaining_jobs = self.MAX_JOBS - checked_jobs
                for index in range(1, min(len(items), remaining_jobs) + 1):
                    current_items = self.browser.find_elements(*job_items)
                    item = current_items[index - 1]
                    listed_work_time = " ".join(
                        " ".join(element.text.split())
                        for element in item.find_elements(
                            By.XPATH,
                            listed_work_times,
                        )
                        if ":" in element.text
                    ).strip() or "확인 불가"

                    is_allowed_work_time = self._is_allowed_work_time(
                        listed_work_time
                    )
                    self._log_action(
                        f"{page}페이지 {index}번 공고 | 목록 근무시간: {listed_work_time} | "
                        f"검증: {'통과' if is_allowed_work_time else '실패'}"
                    )
                    if not is_allowed_work_time:
                        invalid_jobs.append(
                            f"{index}번 공고 [목록 근무시간: {listed_work_time}]"
                        )
                    checked_jobs += 1

                self.assertFalse(
                    invalid_jobs,
                    f"{page}페이지에 근무시간 조건과 맞지 않는 공고가 있습니다: "
                    f"{invalid_jobs}",
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
                    f"{page}페이지 근무시간 공고 검증 중 오류가 발생했습니다: {exc}"
                )

    def test_apply_morning_work_time(self):
        """각 시간대 조건을 하나씩 선택해 해당 공고만 조회되는지 확인한다."""
        original_time_parts = self.TIME_PARTS
        original_ranges = type(self).CURRENT_ALLOWED_TIME_RANGES
        try:
            for time_parts, allowed_ranges in self.SINGLE_TIME_PART_CASES:
                self.TIME_PARTS = time_parts
                type(self).CURRENT_ALLOWED_TIME_RANGES = allowed_ranges
                self._run_work_time_test()
        finally:
            self.TIME_PARTS = original_time_parts
            type(self).CURRENT_ALLOWED_TIME_RANGES = original_ranges

    def tearDown(self):
        super().dispose()
