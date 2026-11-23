from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


# 디버깅 시 대분류와 업직종 조건을 이 목록에서 바꿀 수 있다.
JOB_CATEGORY_SELECTIONS = (
    ("IT·기술", "웹·콘텐츠기획"),
    ("디자인", "웹·모바일디자인"),
)


class TC026(TCBase):
    def setUp(self):
        super().init()

    def test_apply_different_job_category_conditions(self):
        """서로 다른 직업 분류의 업직종 조건이 적용되는지 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-1']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-1']"),
            "업직종 탭",
        )
        self.sleep()

        selected_class = (
            "FilterListColumn_filter-list__column-button--selected__2niWt"
        )

        # 테스트 절차: 서로 다른 대분류에서 각각 업직종 조건을 선택한다.
        for parent_name, condition_name in JOB_CATEGORY_SELECTIONS:
            self.click_element(
                (
                    By.XPATH,
                    f"//li[@role='button' and normalize-space(.)={parent_name!r}]",
                ),
                f"'{parent_name}' 대분류",
            )
            self.sleep()

            condition_locator = (
                By.XPATH,
                f"//li[@role='button' and normalize-space(.)={condition_name!r}]",
            )
            self.click_element(condition_locator, f"'{condition_name}' 조건")
            self.wait_for_selected(
                condition_locator,
                f"'{condition_name}' 조건",
                selected_class,
            )
            self.sleep()

        # 기대 결과: 업직종 탭과 조건 개수가 2로 표시된다.
        expected_count = str(len(JOB_CATEGORY_SELECTIONS))
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-1']//em"),
            expected_count,
            "업직종 탭 선택 개수",
        )
        self.assert_element_text(
            (
                By.XPATH,
                "//div[@role='tabpanel' and @id='panel-1']"
                "//div[contains(@class, 'filter-header__counter')]",
            ),
            f"{expected_count}/10",
            "업직종 조건 개수",
        )

        # 기대 결과: 조건 리스트에 선택한 업직종 조건이 모두 추가된다.
        for _, condition_name in JOB_CATEGORY_SELECTIONS:
            self.assert_element_text(
                (
                    By.XPATH,
                    "//div[contains(@class, 'selector-chips__list')]"
                    "//button[contains(@class, 'selector-chips__chip')"
                    f" and normalize-space()={condition_name!r}]",
                ),
                condition_name,
                "선택 업직종 조건",
            )

        # 테스트 절차: 공고 목록을 확장 보기로 전환해 업직종 상세를 표시한다.
        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "'리스트 펼쳐 보기' 버튼",
        )
        self.sleep()

        # 기대 결과: 각 공고가 선택한 업직종 중 하나 이상을 포함한다.
        selected_conditions = tuple(
            condition_name for _, condition_name in JOB_CATEGORY_SELECTIONS
        )
        job_items = (
            By.XPATH,
            "//ul[contains(@class, 'SimpleRecruitList')]//li",
        )
        job_category_details = (
            ".//div[contains(@class, 'list-item-recruit-details__item')]"
            "[.//span[normalize-space()='업직종']]"
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
                self._log_action(f"{page}페이지 공고 확인 중...")

                invalid_jobs = []
                for item in items:
                    category_detail = item.find_element(
                        By.XPATH,
                        job_category_details,
                    ).text
                    if not any(
                        condition in category_detail
                        for condition in selected_conditions
                    ):
                        title = item.find_element(
                            By.CSS_SELECTOR,
                            "a.list-item-recruit__link",
                        ).text
                        invalid_jobs.append(title)

                self.assertFalse(
                    invalid_jobs,
                    f"{page}페이지에 선택한 업직종이 없는 공고가 있습니다: "
                    f"{invalid_jobs}",
                )

                checked_jobs += len(items)
                if checked_jobs >= self.MAX_JOBS:
                    break

                next_page_locator = (
                    By.XPATH,
                    f"//*[@role='navigation']//button["
                    f"contains(@aria-label, 'goto {page + 1} in')]",
                )
                next_page = self.scroll_to_pagination(next_page_locator)
                if not next_page:
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
                    f"{page}페이지 서로 다른 업직종 공고 검증 중 오류가 발생했습니다: "
                    f"{exc}"
                )

        self.sleep()

    def tearDown(self):
        super().dispose()
