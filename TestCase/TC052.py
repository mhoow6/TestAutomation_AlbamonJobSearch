from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC052(TCBase):
    """단일 근무요일을 직접 선택했을 때 해당 조건이 적용되는지 검증한다."""

    WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")

    def setUp(self):
        super().init()

    @staticmethod
    def _is_single_weekday(work_day, weekday):
        """상세 공고의 근무요일 행 오른쪽에 표시된 요일만 판정한다."""
        # TCBase가 근무요일 행 전체를 읽으면 "화 화 1일"처럼
        # 오른쪽 표시값과 하단 보조 문구가 함께 반환될 수 있다.
        displayed_weekday = work_day.split(maxsplit=1)[0] if work_day else ""
        return displayed_weekday == weekday

    def test_apply_single_direct_work_day(self):
        """직접선택에서 각 요일을 단독 선택하고 해당 공고만 조회되는지 확인한다."""
        job_items = (By.XPATH, "//ul[contains(@class, 'SimpleRecruitList')]//li")

        for weekday in self.WEEKDAYS:
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

            weekday_value = {
                "월": "MONDAY",
                "화": "TUESDAY",
                "수": "WEDNESDAY",
                "목": "THURSDAY",
                "금": "FRIDAY",
                "토": "SATURDAY",
                "일": "SUNDAY",
            }[weekday]
            weekday_input = (
                By.XPATH,
                f"//label[.//span[normalize-space()='{weekday}']]"
                f"//input[@type='checkbox' and @name='dayOfWeeks' and @value='{weekday_value}']",
            )
            weekday_click = (
                By.XPATH,
                f"//label[.//span[normalize-space()='{weekday}']]"
                f"//input[@type='checkbox' and @name='dayOfWeeks' and @value='{weekday_value}']"
                "/ancestor::label[1]",
            )
            self.click_element(weekday_click, f"직접선택 근무요일 '{weekday}' 조건")
            self.wait_for_selected(weekday_input, f"직접선택 근무요일 '{weekday}' 조건")
            self.sleep()

            chip_base = (
                "//div[contains(@class, 'selector-chips__list')]"
                "//button[contains(@class, 'selector-chips__chip')]"
            )
            self.assert_element_text(
                (By.XPATH, f"{chip_base}[normalize-space(.)='{weekday}']"),
                weekday,
                f"조건 리스트의 {weekday} 조건",
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
            self.wait_for_recruit_list_rendered(
                job_items, f"{weekday} 50개 보기 적용 후 공고 목록"
            )

            self.click_element(
                (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
                "공고 리스트 그리드뷰 전환",
            )
            self.wait_for_recruit_list_rendered(
                job_items, f"{weekday} 그리드뷰 전환 후 공고 목록"
            )

            page = 1
            checked_jobs = 0
            while checked_jobs < self.MAX_JOBS:
                try:
                    self.wait_for_elements(job_items, f"{weekday} {page}페이지 공고 목록")
                    items = self.browser.find_elements(*job_items)
                    self.assertTrue(items, f"{weekday} {page}페이지에 공고가 없습니다.")
                    invalid_jobs = []
                    remaining = self.MAX_JOBS - checked_jobs

                    for index in range(1, min(len(items), remaining) + 1):
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
                        detail_work_day = self._get_detail_work_day(detail_link, title)
                        checked_jobs += 1
                        if detail_work_day is None:
                            continue

                        is_single_weekday = self._is_single_weekday(
                            detail_work_day, weekday
                        )
                        self._log_action(
                            f"{weekday} {page}페이지 {index}번 공고 | "
                            f"상세 근무요일: {detail_work_day} | "
                            f"검증: {'통과' if is_single_weekday else '실패'}"
                        )
                        if not is_single_weekday:
                            invalid_jobs.append(
                                f"{title} [근무요일: {detail_work_day}]"
                            )

                    self.assertFalse(
                        invalid_jobs,
                        f"{weekday} 단일 조건과 맞지 않는 공고가 있습니다: {invalid_jobs}",
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
                        f"{weekday} {page}페이지 직접선택 공고 검증 중 오류가 발생했습니다: {exc}"
                    )

    def tearDown(self):
        super().dispose()
