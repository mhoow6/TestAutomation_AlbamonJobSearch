from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC022(TCBase):
    def setUp(self):
        super().init()

    def test_convert_province_conditions_to_province_all(self):
        """제주 하위 지역과 가람동을 제주 전체 및 가람동으로 전환한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-0']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-0']"),
            "지역 탭",
        )
        self.sleep()

        panel = "//div[@role='tabpanel' and @id='panel-0']"
        counter = (
            By.XPATH,
            f"{panel}//div[contains(@class, 'filter-header__counter')]",
        )
        tab_counter = (By.XPATH, "//label[@role='tab' and @for='tab-0']//em")
        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )

        # 사전 조건: 제주 서귀포시 하위 지역 4개를 선택한다.
        for name in ("제주", "서귀포시"):
            self.click_element(
                self.region_button_locator(panel, name),
                f"'{name}' 지역",
            )
            self.sleep()

        child_regions = ("강정동", "남원읍", "대정읍", "대포동")
        for name in child_regions:
            self.click_element(
                self.region_button_locator(panel, name),
                f"'{name}' 지역 조건",
            )
            self.sleep()

        # 사전 조건: 세종 → 세종시 → 가람동을 선택한다.
        for name in ("세종", "세종시", "가람동"):
            self.click_element(
                self.region_button_locator(panel, name),
                f"'{name}' 지역",
            )
            self.sleep()

        self.assert_element_text(tab_counter, "5", "사전 조건 지역 탭 선택 개수")
        self.assert_element_text(counter, "5/5", "사전 조건 지역 조건 개수")

        # 테스트 절차: 제주 하위 지역을 제주 전체 조건으로 전환한다.
        self.click_element(
            self.region_button_locator(panel, "제주"),
            "'제주' 지역",
        )
        self.sleep()
        self.click_element(
            self.region_button_locator(panel, "제주 전체"),
            "'제주 전체' 지역",
        )
        self.sleep()

        # 기대 결과: 제주 전체와 가람동만 남는다.
        self.assert_element_text(tab_counter, "2", "변경 후 지역 탭 선택 개수")
        self.assert_element_text(counter, "2/5", "변경 후 지역 조건 개수")
        for name in child_regions:
            self.assert_no_elements(
                (By.XPATH, f"{chip_base}[normalize-space()={name!r}]"),
                f"{name} 조건이 삭제되지 않았습니다.",
            )
        for name in ("제주 전체", "가람동"):
            self.assert_element_text(
                (By.XPATH, f"{chip_base}[normalize-space()={name!r}]"),
                name,
                f"변경 후 선택 지역 조건 '{name}'",
            )

        # 기대 결과: 제주 및 세종시 가람동 공고만 조회된다.
        job_locations = (
            By.XPATH,
            "//ul[contains(@class, 'SimpleRecruitList')]//li",
        )
        allowed_locations = ("제주시", "서귀포시", "세종시 가람동")
        page = 1

        while True:
            try:
                self.wait.until(lambda driver: driver.find_elements(*job_locations))
                locations = self.read_job_locations(job_locations)
                self._log_action(f"{page}페이지 공고 확인 중...")
                self.assertTrue(locations, f"{page}페이지에 공고가 없습니다.")

                invalid_locations = [
                    location
                    for location in locations
                    if not any(allowed in location for allowed in allowed_locations)
                ]
                self.assertFalse(
                    invalid_locations,
                    f"{page}페이지에 선택 지역 이외의 공고가 있습니다: "
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
                    f"{page}페이지 제주 및 가람동 공고 검증 중 오류가 발생했습니다: "
                    f"{exc}"
                )

        self.sleep()

    def tearDown(self):
        super().dispose()
