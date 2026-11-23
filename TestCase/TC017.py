from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC017(TCBase):
    def setUp(self):
        super().init()

    def test_delete_town_condition(self):
        """동·읍·면 조건을 다시 선택해 삭제한 뒤 남은 지역 공고만 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-0']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-0']"),
            "지역 탭",
        )
        self.sleep()

        panel = (
            "//div[@role='tabpanel' and "
            ".//input[@name='group-similar']]"
        )
        counter = (
            By.XPATH,
            f"{panel}//div[contains(@class, 'filter-header__counter')]",
        )
        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )

        # 사전 조건: 제주 → 서귀포시 → 강정동, 남원읍을 선택한다.
        self.click_element(
            self.region_button_locator(panel, "제주"),
            "'제주' 지역",
        )
        self.sleep()
        self.click_element(
            self.region_button_locator(panel, "서귀포시"),
            "'서귀포시' 지역",
        )
        self.sleep()
        for town in ("강정동", "남원읍"):
            self.click_element(
                self.region_button_locator(panel, town),
                f"'{town}' 지역",
            )
            self.sleep()

        self.assert_element_text(counter, "2/5", "사전 조건 지역 조건 개수")
        for town in ("강정동", "남원읍"):
            self.assert_element_text(
                (By.XPATH, f"{chip_base}[normalize-space(.)={town!r}]"),
                town,
                f"사전 조건 '{town}' 선택 지역",
            )

        # 테스트 절차: 선택된 강정동을 다시 선택해 조건을 삭제한다.
        delete_town_locator = self.region_button_locator(panel, "강정동")
        self.highlight_element(delete_town_locator, "조건 삭제 대상 강정동")
        self.sleep()
        self.click_element(
            delete_town_locator,
            "'강정동' 지역 조건 삭제",
        )
        self.sleep()

        # 기대 결과: 선택 개수와 조건 리스트에서 강정동이 사라지고 남원읍만 남는다.
        self.assert_element_text(counter, "1/5", "조건 삭제 후 지역 조건 개수")
        self.assert_no_elements(
            (By.XPATH, f"{chip_base}[normalize-space(.)='강정동']"),
            "강정동 조건이 삭제되지 않았습니다.",
        )
        self.assert_element_text(
            (By.XPATH, f"{chip_base}[normalize-space(.)='남원읍']"),
            "남원읍",
            "조건 삭제 후 남은 지역 조건",
        )

        job_locations = (
            By.XPATH,
            "//ul[contains(@class, 'SimpleRecruitList')]//li",
        )
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
                    if "서귀포시 남원읍" not in location
                ]
                self.assertFalse(
                    invalid_locations,
                    f"{page}페이지에 남원읍 이외의 공고가 있습니다: "
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
                    f"{page}페이지 남원읍 공고 검증 중 오류가 발생했습니다: {exc}"
                )

        self.sleep()

    def tearDown(self):
        super().dispose()
