from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC007(TCBase):
    def setUp(self):
        super().init()

    def test_select_region(self):
        """제주 전체를 선택하고 제주 지역 공고가 조회되는지 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-0']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-0']"),
            "지역 탭",
        )
        self.sleep()

        panel = "//div[@role='tabpanel' and @id='panel-0']"
        self.click_element(
            (
                By.XPATH,
                f"{panel}//li[@role='button' and normalize-space(.)='제주']",
            ),
            "'제주' 지역",
        )
        self.sleep()

        self.click_element(
            (
                By.XPATH,
                f"{panel}//li[@role='button' and normalize-space(.)='제주 전체']",
            ),
            "'제주 전체' 지역",
        )
        self.sleep()

        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-0']//em"),
            "1",
            "지역 탭 선택 개수",
        )
        self.assert_element_text(
            (By.XPATH, f"{panel}//div[contains(@class, 'filter-header__counter')]"),
            "1/5",
            "지역 조건 개수",
        )
        self.assert_element_text(
            (
                By.XPATH,
                "//div[contains(@class, 'selector-chips__list')]"
                "//button[contains(@class, 'selector-chips__chip')]",
            ),
            "제주 전체",
            "선택 지역 조건",
        )
        self.sleep()

        job_locations = (
            By.XPATH,
            "//ul[contains(@class, 'SimpleRecruitList')]//li",
        )
        allowed_regions = ("제주시", "서귀포시", "제주 전체")
        page = 1
        checked_jobs = 0

        while checked_jobs < self.MAX_JOBS:
            try:
                self.wait.until(
                    lambda driver: driver.find_elements(*job_locations)
                )
                locations = self.read_job_locations(job_locations)
                locations = locations[: self.MAX_JOBS - checked_jobs]
                checked_jobs += len(locations)
                self._log_action(f"{page}페이지 공고 확인 중...")
                self.assertTrue(locations, f"{page}페이지에 공고가 없습니다.")

                if checked_jobs >= self.MAX_JOBS:
                    break

                invalid_locations = [
                    location
                    for location in locations
                    if not any(region in location for region in allowed_regions)
                ]
                self.assertFalse(
                    invalid_locations,
                    f"{page}페이지에 제주 이외의 공고가 있습니다: "
                    f"{invalid_locations}",
                )

                next_page_locator = (
                    By.XPATH,
                    f"//*[@role='navigation']//button["
                    f"contains(@aria-label, 'goto {page + 1} in')]",
                )
                next_page = self.scroll_to_pagination(next_page_locator)

                if not next_page:
                    break

                previous_locations = tuple(locations)
                self.wait.until(
                    lambda driver: driver.find_elements(*next_page_locator)
                )
                self.browser.find_element(*next_page_locator).click()

                def is_page_changed(driver):
                    try:
                        current_locations = self.read_job_locations(job_locations)
                        return (
                            bool(current_locations)
                            and tuple(current_locations) != previous_locations
                        )
                    except StaleElementReferenceException:
                        return False

                self.wait.until(is_page_changed)
                page += 1
            except Exception as exc:
                self.fail(
                    f"{page}페이지 공고 지역 검증 중 오류가 발생했습니다: {exc}"
                )

        self.sleep()

    def tearDown(self):
        super().dispose()
