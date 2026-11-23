from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC023(TCBase):
    ADULT_CERTIFICATION_PATH = "/user-account/cert/adult/non-login"
    SELECTED_CLASS = (
        "FilterListColumn_filter-list__column-button--selected__2niWt"
    )

    def setUp(self):
        super().init()

    def _collect_job_categories(self, panel):
        """모든 대분류에서 업직종 ID와 이름을 수집한다."""
        category_items = (
            By.XPATH,
            f"{panel}//li[starts-with(@id, 'category-')]",
        )
        part_items = (
            By.XPATH,
            f"{panel}//li[starts-with(@id, 'part-')]",
        )
        self.wait_for_elements(category_items, "업직종 대분류 목록")
        category_ids = [
            category.get_attribute("id")
            for category in self.browser.find_elements(*category_items)
        ]

        job_categories = []
        previous_part_ids = set()
        for category_id in category_ids:
            category_locator = (By.ID, category_id)
            self.click_element(category_locator, f"'{category_id}' 대분류")
            self.wait_for_elements(part_items, f"'{category_id}' 업직종 목록")
            self.wait.until(
                lambda driver, current_category_id=category_id: self._category_parts_loaded(
                    driver,
                    current_category_id,
                    part_items,
                    previous_part_ids,
                )
            )
            current_parts = self.browser.find_elements(*part_items)
            job_categories.extend(
                (
                    category_id,
                    part.get_attribute("id"),
                    " ".join(part.text.split()),
                )
                for part in current_parts
                if part.text.strip()
                and not part.text.strip().endswith(" 전체")
                and part.get_attribute("id")
            )
            previous_part_ids = {
                part.get_attribute("id") for part in current_parts
            }

        self.assertTrue(job_categories, "업직종 목록을 수집하지 못했습니다.")
        self._log_action(f"전체 업직종 수집 완료: {len(job_categories)}개")
        return tuple(job_categories)

    @staticmethod
    def _category_parts_loaded(driver, category_id, part_items, previous_part_ids):
        """선택한 대분류의 하위 업직종 목록이 갱신됐는지 확인한다."""
        category = driver.find_element(By.ID, category_id)
        if "--selected__" not in (category.get_attribute("class") or ""):
            return False

        current_part_ids = {
            element.get_attribute("id")
            for element in driver.find_elements(*part_items)
        }
        return bool(current_part_ids) and (
            not previous_part_ids or current_part_ids != previous_part_ids
        )

    def _verify_selected_job_category_jobs(self, condition, job_items):
        """선택한 업직종 공고를 최대 MAX_JOBS건까지 검증한다."""
        job_category_details = (
            ".//div[contains(@class, 'list-item-recruit-details__item')]"
            "[.//span[normalize-space()='업직종']]"
            "//span[contains(@class, 'list-item-recruit-details__children')]"
        )
        page = 1
        checked_jobs = 0

        while checked_jobs < self.MAX_JOBS:
            try:
                self.wait_for_elements(job_items, f"{condition} {page}페이지 공고 목록")
                items = self.browser.find_elements(*job_items)
                self.assertTrue(items, f"{condition} {page}페이지에 공고가 없습니다.")
                invalid_jobs = []
                remaining_jobs = self.MAX_JOBS - checked_jobs

                for index in range(1, min(len(items), remaining_jobs) + 1):
                    item = self.browser.find_elements(*job_items)[index - 1]
                    title = item.find_element(
                        By.CSS_SELECTOR,
                        "a.list-item-recruit__link",
                    ).text
                    category_details = item.find_elements(
                        By.XPATH,
                        job_category_details,
                    )
                    category_detail = " ".join(
                        " ".join(element.text.split())
                        for element in category_details
                    ).strip()
                    is_allowed = bool(category_detail) and condition in category_detail
                    self._log_action(
                        f"{condition} {page}페이지 {index}번 공고 | "
                        f"업직종: {category_detail or '확인 불가'} | "
                        f"검증: {'통과' if is_allowed else '실패'}"
                    )
                    if not is_allowed:
                        invalid_jobs.append(
                            f"{title} [업직종: {category_detail or '확인 불가'}]"
                        )
                    checked_jobs += 1

                self.assertFalse(
                    invalid_jobs,
                    f"{condition}이(가) 아닌 공고가 있습니다: {invalid_jobs}",
                )
                self._log_action(
                    f"{condition} 공고 {checked_jobs}/{self.MAX_JOBS}개 확인"
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
                self.wait_for_recruit_list_rendered(
                    job_items,
                    f"{condition} {page + 1}페이지 공고 목록",
                )
                page += 1
            except Exception as exc:
                self.fail(
                    f"{condition} {page}페이지 공고 검증 중 오류가 발생했습니다: {exc}"
                )

    def test_apply_same_job_category_condition(self):
        """모든 대분류의 업직종 조건이 각각 적용되는지 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-1']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-1']"),
            "업직종 탭",
        )
        self.sleep()

        panel = "//div[@role='tabpanel' and @id='panel-1']"
        job_categories = self._collect_job_categories(panel)

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
        self.sleep()

        job_items = (
            By.XPATH,
            "//ul[contains(@class, 'SimpleRecruitList')]//li",
        )
        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "'리스트 펼쳐 보기' 버튼",
        )
        self.wait_for_recruit_list_rendered(job_items, "그리드뷰 전환 후 공고 목록")
        self.sleep()

        counter_locator = (
            By.XPATH,
            f"{panel}//div[contains(@class, 'filter-header__counter')]",
        )
        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )

        for category_id, part_id, condition in job_categories:
            category_locator = (By.ID, category_id)
            self.click_element(category_locator, f"'{category_id}' 대분류")
            condition_locator = (By.ID, part_id)
            self.wait_for_element(condition_locator, f"'{condition}' 조건")
            self.click_element(condition_locator, f"'{condition}' 조건")
            if self.ADULT_CERTIFICATION_PATH in self.browser.current_url:
                self._log_action(
                    f"성인인증 필요 업직종 건너뜀: {condition} | "
                    f"URL: {self.browser.current_url}"
                )
                self.browser.get(self.URL)
                self.wait.until(
                    lambda driver: driver.find_elements(
                        By.XPATH,
                        "//h1[normalize-space()='기간 요일 시간별']",
                    )
                )
                self.select_if_not_selected(
                    (By.XPATH, "//input[@id='tab-1']"),
                    (By.XPATH, "//label[@role='tab' and @for='tab-1']"),
                    "성인인증 후 업직종 탭 복귀",
                )
                self.click_element(page_size_locator, "성인인증 후 공고 목록 노출 개수 선택")
                self.click_element(
                    (By.XPATH, "//button[normalize-space()='50개씩']"),
                    "성인인증 후 공고 50개씩 보기",
                )
                self.wait.until(
                    lambda driver: driver.find_element(*page_size_locator).text.strip()
                    == "50개씩"
                )
                self.click_element(
                    (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
                    "성인인증 후 '리스트 펼쳐 보기' 버튼",
                )
                self.wait_for_recruit_list_rendered(
                    job_items,
                    "성인인증 후 공고 목록 복귀",
                )
                continue

            self.wait_for_selected(
                condition_locator,
                f"'{condition}' 조건",
                self.SELECTED_CLASS,
            )
            self.assert_element_text(
                (By.XPATH, "//label[@role='tab' and @for='tab-1']//em"),
                "1",
                f"{condition} 선택 후 업직종 탭 선택 개수",
            )
            self.assert_element_text(counter_locator, "1/10", f"{condition} 조건 개수")
            self.assert_element_text(
                (By.XPATH, f"{chip_base}[normalize-space(.)={condition!r}]"),
                condition,
                f"조건 리스트의 {condition}",
            )
            self.wait_for_recruit_list_rendered(
                job_items,
                f"{condition} 조건 적용 후 공고 목록",
            )
            self.sleep()

            self._verify_selected_job_category_jobs(condition, job_items)

            self.click_element(condition_locator, f"'{condition}' 조건 해제")
            self.wait_for_not_selected(
                condition_locator,
                f"해제된 '{condition}' 조건",
                self.SELECTED_CLASS,
            )
            self.wait_for_recruit_list_rendered(
                job_items,
                f"{condition} 조건 해제 후 공고 목록",
            )

        self.sleep()

    def tearDown(self):
        super().dispose()
