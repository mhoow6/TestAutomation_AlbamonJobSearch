from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC009(TCBase):
    def setUp(self):
        super().init()

    def test_select_region(self):
        """선택한 하위 지역을 서귀포시 전체 조건으로 변경한다."""
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

        # 사전 조건: 같은 서귀포시의 남원읍 선택
        self.click_element(
            (
                By.XPATH,
                f"{panel}//li[@role='button' and normalize-space(.)='남원읍']",
            ),
            "'남원읍' 지역",
        )
        self.sleep()

        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )

        # 사전 조건 확인: 하위 지역 2개가 선택되어 있어야 한다.
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

        # 테스트 절차: 서귀포시 전체 선택
        self.click_element(
            (
                By.XPATH,
                f"{panel}//li[@role='button' and normalize-space(.)='서귀포시 전체']",
            ),
            "'서귀포시 전체' 지역",
        )
        self.sleep()

        # 기대 결과: 하위 지역 2개가 사라지고 서귀포시 전체가 추가된다.
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
            (By.XPATH, f"{chip_base}[normalize-space()='남원읍']"),
            "남원읍 조건이 삭제되지 않았습니다.",
        )
        self.assert_element_text(
            (By.XPATH, f"{chip_base}[normalize-space()='서귀포시 전체']"),
            "서귀포시 전체",
            "변경 후 선택 지역 조건",
        )
        self.sleep(2)

        job_locations = (
            By.XPATH,
            "//ul[contains(@class, 'SimpleRecruitList')]//li",
        )
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
                    if "서귀포시" not in location
                ]
                self.assertFalse(
                    invalid_locations,
                    f"{page}페이지에 서귀포시 이외의 공고가 있습니다: "
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
