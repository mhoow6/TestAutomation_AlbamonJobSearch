from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC010(TCBase):
    def setUp(self):
        super().init()

    def test_select_region(self):
        """제주 내 서로 다른 시·구·군 조건을 제주 전체 조건으로 변경한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-0']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-0']"),
            "지역 탭",
        )
        self.sleep()

        panel = "//div[@role='tabpanel' and @id='panel-0']"

        # 사전 조건: 제주 → 서귀포시 → 강정동 선택
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
                f"{panel}//li[@role='button' and normalize-space(.)='서귀포시']",
            ),
            "'서귀포시' 지역",
        )
        self.sleep()
        self.click_element(
            (
                By.XPATH,
                f"{panel}//li[@role='button' and normalize-space(.)='강정동']",
            ),
            "'강정동' 지역",
        )
        self.sleep()

        # 사전 조건: 제주 → 제주시 → 건입동 선택
        self.click_element(
            (
                By.XPATH,
                f"{panel}//li[@role='button' and normalize-space(.)='제주시']",
            ),
            "'제주시' 지역",
        )
        self.sleep()
        self.click_element(
            (
                By.XPATH,
                f"{panel}//li[@role='button' and normalize-space(.)='건입동']",
            ),
            "'건입동' 지역",
        )
        self.sleep()

        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )

        # 사전 조건 확인: 제주 내 서로 다른 시·구·군 조건 2개가 선택되어 있어야 한다.
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-0']//em"),
            "2",
            "사전 조건 지역 탭 선택 개수",
        )
        self.assert_element_text(
            (By.XPATH, f"{panel}//div[contains(@class, 'filter-header__counter')]"),
            "2/5",
            "사전 조건 지역 조건 개수",
        )

        # 테스트 절차: 제주 → 제주 전체 선택
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

        # 기대 결과: 기존 하위 조건들이 사라지고 제주 전체가 추가된다.
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-0']//em"),
            "1",
            "변경 후 지역 탭 선택 개수",
        )
        self.assert_element_text(
            (By.XPATH, f"{panel}//div[contains(@class, 'filter-header__counter')]"),
            "1/5",
            "변경 후 지역 조건 개수",
        )
        self.assert_no_elements(
            (By.XPATH, f"{chip_base}[normalize-space()='강정동']"),
            "강정동 조건이 삭제되지 않았습니다.",
        )
        self.assert_no_elements(
            (By.XPATH, f"{chip_base}[normalize-space()='건입동']"),
            "건입동 조건이 삭제되지 않았습니다.",
        )
        self.assert_element_text(
            (By.XPATH, f"{chip_base}[normalize-space()='제주 전체']"),
            "제주 전체",
            "변경 후 선택 지역 조건",
        )
        self.sleep()

        job_locations = (
            By.XPATH,
            "//ul[contains(@class, 'SimpleRecruitList')]//li",
        )
        allowed_regions = ("제주시", "서귀포시", "제주 전체")
        page = 1

        while True:
            try:
                self.wait.until(
                    lambda driver: driver.find_elements(*job_locations)
                )
                locations = self.read_job_locations(job_locations)
                self._log_action(f"{page}페이지 공고 확인 중...")
                self.assertTrue(locations, f"{page}페이지에 공고가 없습니다.")

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
