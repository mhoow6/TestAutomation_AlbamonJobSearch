import json
from pathlib import Path

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


IT_JOB_CATEGORIES = (
    "웹·콘텐츠기획",
    "사이트관리·기술지원",
    "프로그래머",
    "HTML코딩",
    "QA·테스터·검증",
    "시스템·네트워크·보안",
    "PC·디지털기기 설치·관리",
)


def _load_region_names():
    """TC012 데이터를 서울 지역명과 타 시·도명 목록으로 변환한다."""
    expected_data_path = Path(__file__).with_name("TC012_ExpectedData.json")
    with expected_data_path.open(encoding="utf-8") as expected_file:
        region_data = json.load(expected_file)["data"]

    seoul_data = region_data["서울"]

    region_names = set(seoul_data)
    for neighborhoods in seoul_data.values():
        region_names.update(
            neighborhood.removesuffix(" 전체")
            for neighborhood in neighborhoods
        )
    return (
        tuple(sorted(region_names, key=len, reverse=True)),
        tuple(name for name in region_data if name != "서울"),
    )


SEOUL_REGION_NAMES, NON_SEOUL_REGION_NAMES = _load_region_names()


class TC077(TCBase):
    """서로 다른 카테고리의 필터를 동시에 적용했을 때를 검증한다."""

    SELECTED_CLASS = (
        "FilterListColumn_filter-list__column-button--selected__2niWt"
    )

    def setUp(self):
        super().init()

    def test_apply_region_and_job_category_filters(self):
        """서울 전체와 IT·기술 전체를 함께 선택하고 공고를 검증한다."""
        self.load()

        region_panel = "//div[@role='tabpanel' and @id='panel-0']"
        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-0']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-0']"),
            "지역 탭",
        )
        self.sleep()

        seoul = (
            By.XPATH,
            f"{region_panel}//li[@role='button' and "
            "normalize-space(.)='서울']",
        )
        self.click_element(seoul, "'서울' 지역")
        self.sleep()

        seoul_all = (
            By.XPATH,
            f"{region_panel}//li[@role='button' and "
            "normalize-space(.)='서울 전체']",
        )
        self.click_element(seoul_all, "'서울 전체' 지역")
        self.wait_for_selected(seoul_all, "'서울 전체' 지역", self.SELECTED_CLASS)

        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-0']//em"),
            "1",
            "지역 탭 선택 개수",
        )

        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )
        self.assert_element_text(
            (By.XPATH, f"{chip_base}[normalize-space(.)='서울 전체']"),
            "서울 전체",
            "조건 리스트의 서울 전체",
        )

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-1']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-1']"),
            "업직종 탭",
        )
        self.sleep()

        job_panel = "//div[@role='tabpanel' and @id='panel-1']"
        it_category = (
            By.XPATH,
            f"{job_panel}//li[@role='button' and "
            "normalize-space(.)='IT·기술']",
        )
        self.click_element(it_category, "'IT·기술' 대분류")
        self.sleep()

        it_all = (
            By.XPATH,
            f"{job_panel}//li[@role='button' and "
            "normalize-space(.)='IT·기술 전체']",
        )
        self.click_element(it_all, "'IT·기술 전체' 업직종")
        self.wait_for_selected(it_all, "'IT·기술 전체' 업직종", self.SELECTED_CLASS)

        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-1']//em"),
            "1",
            "업직종 탭 선택 개수",
        )
        self.assert_element_text(
            (By.XPATH, f"{chip_base}[normalize-space(.)='IT·기술 전체']"),
            "IT·기술 전체",
            "조건 리스트의 IT·기술 전체",
        )

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

        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "공고 리스트 그리드뷰 전환",
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
        job_region_locator = (
            ".//div[contains(@class, 'list-item-recruit__contents--keyword-area')]"
        )
        job_workplace_locator = (
            ".//div[contains(@class, 'list-item-recruit-details__item')]"
            "[.//span[normalize-space()='근무지']]"
            "//span[contains(@class, 'list-item-recruit-details__children')]"
        )
        page = 1
        checked_jobs = 0
        while checked_jobs < self.MAX_JOBS:
            try:
                self.wait_for_elements(job_items, f"{page}페이지 서울·IT·기술 공고 목록")
                items = self.browser.find_elements(*job_items)
                self.assertTrue(items, f"{page}페이지 서울·IT·기술 공고가 없습니다.")
                self._log_action(f"{page}페이지 서울·IT·기술 공고 확인 중...")

                invalid_jobs = []
                remaining_jobs = self.MAX_JOBS - checked_jobs
                for index, item in enumerate(
                    items[:remaining_jobs],
                    start=1,
                ):
                    title = item.find_element(
                        By.CSS_SELECTOR,
                        "a.list-item-recruit__link",
                    ).text
                    region_text = " ".join(
                        item.find_element(By.XPATH, job_region_locator).text.split()
                    )
                    workplace_text = " ".join(
                        item.find_element(By.XPATH, job_workplace_locator).text.split()
                    )
                    category_text = item.find_element(
                        By.XPATH,
                        job_category_details,
                    ).text
                    is_seoul_job = "서울" in region_text or any(
                        region in region_text for region in SEOUL_REGION_NAMES
                    )
                    is_it_job = any(
                        category in category_text for category in IT_JOB_CATEGORIES
                    )
                    is_seoul_workplace = not any(
                        region in workplace_text
                        for region in NON_SEOUL_REGION_NAMES
                    )
                    is_allowed_job = (
                        is_seoul_job and is_seoul_workplace and is_it_job
                    )
                    self._log_action(
                        f"{page}페이지 {index}번 공고 | "
                        f"공고 지역: {region_text} | 실제 근무지: {workplace_text} | "
                        f"업직종: {category_text} | "
                        f"검증: {'통과' if is_allowed_job else '실패'}"
                    )
                    if not is_allowed_job:
                        invalid_jobs.append(
                            f"{title} [공고 지역={region_text}, "
                            f"실제 근무지={workplace_text}, 업직종={category_text}]"
                        )
                    checked_jobs += 1

                if invalid_jobs:
                    self._log_action(
                        f"{page}페이지 조건 불일치 공고 {len(invalid_jobs)}건 기록:"
                    )
                    for invalid_job in invalid_jobs:
                        self._log_action(f"- {invalid_job}")
                    invalid_job_details = "\n".join(
                        f"- {invalid_job}" for invalid_job in invalid_jobs
                    )
                    self.fail(
                        f"{page}페이지에서 조건 불일치 공고 "
                        f"{len(invalid_jobs)}건이 발견되었습니다.\n"
                        f"조건 불일치 상세:\n{invalid_job_details}"
                    )
                else:
                    self._log_action(
                        f"{page}페이지 공고가 서울·IT·기술 조건에 모두 일치합니다."
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
                    f"{page}페이지 서울·IT·기술 공고 검증 중 오류가 발생했습니다: "
                    f"{exc}"
                )

    def tearDown(self):
        super().dispose()
