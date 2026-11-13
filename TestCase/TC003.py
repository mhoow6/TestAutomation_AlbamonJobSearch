from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC003(TCBase):
    def setUp(self):
        super().init()

    def test_select_region(self):
        """제주 서귀포시 강정동을 선택하고 지역 공고가 조회되는지 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-0']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-0']"),
            "지역 탭",
        )
        self.sleep()

        panel = "//div[@role='tabpanel' and @id='panel-0']"
        # 테스트 절차: 제주 선택
        self.click_element(
            (
                By.XPATH,
                f"{panel}//li[@role='button' and normalize-space(.)='제주']"
            ),
            "'제주' 지역",
        )
        self.sleep()

        # 테스트 절차: 서귀포시 선택
        self.click_element(
            (
                By.XPATH,
                f"{panel}//li[@role='button' and normalize-space(.)='서귀포시']"
            ),
            "'서귀포시' 지역",
        )
        self.sleep()

        # 테스트 절차: 강정동 선택
        self.click_element(
            (
                By.XPATH,
                f"{panel}//li[@role='button' and normalize-space(.)='강정동']"
            ),
            "'강정동' 지역",
        )
        self.sleep()

        # 기대 결과: 지역 탭에 1 표기
        self.assert_element_text(
            (By.XPATH, "//label[@role='tab' and @for='tab-0']//em"),
            "1",
            "지역 탭 선택 개수",
        )
        self.sleep()

        # 기대 결과: 조건 개수 1/5 표기
        self.assert_element_text(
            (By.XPATH, f"{panel}//div[contains(@class, 'filter-header__counter')]"),
            "1/5",
            "지역 조건 개수",
        )
        self.sleep()

        # 기대 결과: 조건 리스트에 강정동 추가
        self.assert_element_text(
            (
                By.XPATH,
                "//div[contains(@class, 'selector-chips__list')]"
                "//button[contains(@class, 'selector-chips__chip')]",
            ),
            "강정동",
            "선택 지역 조건",
        )
        self.sleep()

        # 공고 리스트에 서귀포시 강정동에 있는 공고들만 조회됨
        job_locations = (
            By.XPATH,
            "//ul[contains(@class, 'SimpleRecruitList')]//li",
        )
        page = 1

        while True:
            try:
                # 현재 페이지의 공고 목록을 읽는다.
                self.wait.until(
                    lambda driver: driver.find_elements(*job_locations)
                )
                locations = self.read_job_locations(job_locations)
                self._log_action(f"{page}페이지 공고 확인 중...")

                self.assertTrue(
                    locations,
                    f"{page}페이지에 공고가 없습니다.",
                )

                # 현재 페이지의 모든 공고가 선택한 지역인지 검증한다.
                invalid_locations = [
                    location
                    for location in locations
                    if "서귀포시 강정동" not in location
                ]
                self.assertFalse(
                    invalid_locations,
                    f"{page}페이지에 강정동 이외의 공고가 있습니다: "
                    f"{invalid_locations}",
                )

                # 다음 페이지 버튼을 찾는다.
                next_page_locator = (
                    By.XPATH,
                    f"//*[@role='navigation']//button["
                    f"contains(@aria-label, 'goto {page + 1} in')]",
                )
                next_page = self.scroll_to_pagination(next_page_locator)

                # 마지막 페이지라면 스크롤 후 테스트를 종료한다.
                if not next_page:
                    break

                previous_locations = tuple(locations)

                # 스크롤 중 DOM이 갱신됐을 수 있으므로 버튼을 다시 조회한다.
                self.wait.until(
                    lambda driver: driver.find_elements(*next_page_locator)
                )
                self.browser.find_element(*next_page_locator).click()

                # 새 페이지의 공고 목록이 이전 페이지와 달라질 때까지 기다린다.
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
