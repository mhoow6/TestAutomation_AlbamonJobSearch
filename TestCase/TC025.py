from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


# IT·기술 전체 조건의 공고에 표시될 수 있는 하위 업직종 목록이다.
IT_JOB_CATEGORIES = (
    "웹·콘텐츠기획",
    "사이트관리·기술지원",
    "프로그래머",
    "HTML코딩",
    "QA·테스터·검증",
    "시스템·네트워크·보안",
    "PC·디지털기기 설치·관리",
)


class TC025(TCBase):
    def setUp(self):
        super().init()

    def test_apply_all_same_job_category_condition(self):
        """동일 직업 분류의 전체 업직종 조건이 적용되는지 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-1']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-1']"),
            "업직종 탭",
        )
        self.sleep()

        # 테스트 절차: IT·기술 분류에서 전체 조건을 선택한다.
        self.click_element(
            (By.XPATH, "//li[@role='button' and @id='category-9000']"),
            "'IT·기술' 대분류",
        )
        self.sleep()

        all_condition_locator = (
            By.XPATH,
            "//li[@role='button' and normalize-space(.)='IT·기술 전체']",
        )
        selected_class = (
            "FilterListColumn_filter-list__column-button--selected__2niWt"
        )
        self.click_element(all_condition_locator, "'IT·기술 전체' 조건")
        self.wait_for_selected(
            all_condition_locator,
            "'IT·기술 전체' 조건",
            selected_class,
        )
        self.sleep()

        # 기대 결과: 업직종 탭과 조건 개수가 1로 표시된다.
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-1']//em"),
            "1",
            "업직종 탭 선택 개수",
        )
        self.assert_element_text(
            (
                By.XPATH,
                "//div[@role='tabpanel' and @id='panel-1']"
                "//div[contains(@class, 'filter-header__counter')]",
            ),
            "1/10",
            "업직종 조건 개수",
        )

        # 기대 결과: 조건 리스트에 IT·기술 전체가 추가된다.
        self.assert_element_text(
            (
                By.XPATH,
                "//div[contains(@class, 'selector-chips__list')]"
                "//button[contains(@class, 'selector-chips__chip')"
                " and normalize-space()='IT·기술 전체']",
            ),
            "IT·기술 전체",
            "선택 업직종 조건",
        )

        # 테스트 절차: 공고 목록을 확장 보기로 전환해 업직종 상세를 표시한다.
        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "'리스트 펼쳐 보기' 버튼",
        )
        self.sleep()

        # 기대 결과: 각 공고가 IT·기술 하위 업직종 중 하나 이상을 포함한다.
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

        while True:
            try:
                self.wait_for_elements(job_items, f"{page}페이지 공고 목록")
                items = self.browser.find_elements(*job_items)
                self.assertTrue(items, f"{page}페이지에 공고가 없습니다.")
                self._log_action(f"{page}페이지 공고 확인 중...")

                invalid_jobs = []
                for item in items:
                    category_detail = item.find_element(
                        By.XPATH,
                        job_category_details,
                    ).text
                    if not any(
                        category in category_detail
                        for category in IT_JOB_CATEGORIES
                    ):
                        title = item.find_element(
                            By.CSS_SELECTOR,
                            "a.list-item-recruit__link",
                        ).text
                        invalid_jobs.append(title)

                self.assertFalse(
                    invalid_jobs,
                    f"{page}페이지에 IT·기술 업직종이 없는 공고가 있습니다: "
                    f"{invalid_jobs}",
                )

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
                    f"{page}페이지 IT·기술 전체 공고 검증 중 오류가 발생했습니다: "
                    f"{exc}"
                )

        self.sleep()

    def tearDown(self):
        super().dispose()
