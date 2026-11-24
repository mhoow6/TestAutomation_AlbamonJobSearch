from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC003(TCBase):
    BROWSER_RESTART_INTERVAL = 100

    def setUp(self):
        super().init()
        self.no_job_regions = set()

    @staticmethod
    def _visible_names(elements, exclude_all=False):
        """지역 버튼에서 공백 및 전체 항목을 제외한 이름을 추출한다."""
        names = []
        for element in elements:
            name = " ".join(element.text.split())
            if not name:
                continue
            if exclude_all and name.endswith("전체"):
                continue
            names.append(name)
        return names

    def _wait_for_region_results(self, name):
        """결과 수 표시가 렌더링될 때까지 기다린다."""
        self.sleep(self.RECRUIT_LIST_RENDER_WAIT)
        result_count_locator = (
            By.XPATH,
            "//*[@id='__next']/div/div[1]/main/div[2]/div[1]/div/"
            "div[2]/div[1]/div[1]/div/span",
        )
        return self.wait.until(
            lambda driver: driver.find_element(*result_count_locator).text.strip()
        )

    def _restart_browser_for_region(
        self,
        panel,
        page_size_locator,
        job_locations,
        province,
        district,
    ):
        """메모리 누적을 줄이고 현재 시·도·구·군까지 복원한다."""
        self._log_action(
            f"지역 {self.BROWSER_RESTART_INTERVAL}건 확인 완료 - "
            f"브라우저 재시작 후 '{province} {district}'부터 이어서 진행"
        )
        self.dispose()
        super().init()
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-0']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-0']"),
            "지역 탭",
        )
        self.sleep()
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
        self.wait_for_recruit_list_rendered(
            job_locations,
            "브라우저 재시작 후 그리드뷰 공고 목록",
        )

        self.click_element(
            self.region_button_locator(panel, province),
            f"'{province}' 시·도 복원",
        )
        self.sleep()
        self.click_element(
            self.region_button_locator(panel, district),
            f"'{province} {district}' 시·구·군 복원",
        )
        self.sleep()

    def _verify_region_jobs(self, region, job_locations):
        """선택한 최하위 지역의 공고를 최대 MAX_JOBS건까지 검증한다."""
        _, district, town = region
        expected_location = f"{district} {town}"
        job_region_locator = (
            ".//div[contains(@class, 'list-item-recruit__contents--keyword-area')]"
        )
        job_workplace_locator = (
            ".//div[contains(@class, 'list-item-recruit-details__item')]"
            "[.//span[normalize-space()='근무지']]"
            "//span[contains(@class, 'list-item-recruit-details__children')]"
        )
        job_category_locator = (
            ".//div[contains(@class, 'list-item-recruit-details__item')]"
            "[.//span[normalize-space()='업직종']]"
            "//span[contains(@class, 'list-item-recruit-details__children')]"
        )
        page = 1
        checked_jobs = 0

        while checked_jobs < self.MAX_JOBS:
            try:
                result_count = self._wait_for_region_results(
                    f"{expected_location} {page}페이지 결과 수"
                )
                normalized_result_count = "".join(result_count.split())
                if "0건" in normalized_result_count:
                    self.no_job_regions.add(expected_location)
                    return

                self.wait_for_elements(
                    job_locations,
                    f"{expected_location} {page}페이지 공고 목록",
                )
                items = self.browser.find_elements(*job_locations)
                if not items:
                    self.no_job_regions.add(expected_location)
                    return
                remaining_jobs = self.MAX_JOBS - checked_jobs
                invalid_jobs = []
                for index, item in enumerate(items[:remaining_jobs], start=1):
                    title = item.find_element(
                        By.CSS_SELECTOR,
                        "a.list-item-recruit__link",
                    ).text
                    region_elements = item.find_elements(
                        By.XPATH,
                        job_region_locator,
                    )
                    workplace_elements = item.find_elements(
                        By.XPATH,
                        job_workplace_locator,
                    )
                    category_elements = item.find_elements(
                        By.XPATH,
                        job_category_locator,
                    )
                    region_text = " ".join(
                        " ".join(element.text.split())
                        for element in region_elements
                    ).strip() or "확인 불가"
                    workplace_text = " ".join(
                        " ".join(element.text.split())
                        for element in workplace_elements
                    ).strip() or "확인 불가"
                    category_text = " ".join(
                        " ".join(element.text.split())
                        for element in category_elements
                    ).strip() or "확인 불가"
                    is_allowed = expected_location in region_text
                    self._log_action(
                        f"{page}페이지 {index}번 공고 | "
                        f"공고 지역: {region_text} | 실제 근무지: {workplace_text} | "
                        f"업직종: {category_text} | "
                        f"검증: {'통과' if is_allowed else '실패'}"
                    )
                    if not is_allowed:
                        invalid_jobs.append(
                            f"{title} [공고 지역={region_text}, "
                            f"실제 근무지={workplace_text}, 업직종={category_text}]"
                        )
                    checked_jobs += 1

                if invalid_jobs:
                    invalid_job_details = "\n".join(
                        f"- {invalid_job}" for invalid_job in invalid_jobs
                    )
                    self.fail(
                        f"{page}페이지에서 {expected_location} 조건 불일치 공고 "
                        f"{len(invalid_jobs)}건이 발견되었습니다.\n"
                        f"조건 불일치 상세:\n{invalid_job_details}"
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
                        current_titles = tuple(
                            item.find_element(
                                By.CSS_SELECTOR,
                                "a.list-item-recruit__link",
                            ).text
                            for item in driver.find_elements(*job_locations)
                        )
                        return bool(current_titles) and current_titles != previous_titles
                    except StaleElementReferenceException:
                        return False

                self.wait.until(is_page_changed)
                self.wait_for_recruit_list_rendered(
                    job_locations,
                    f"{expected_location} {page + 1}페이지 공고 목록",
                )
                page += 1
            except Exception as exc:
                self.fail(
                    f"{expected_location} {page}페이지 공고 지역 검증 중 오류가 "
                    f"발생했습니다: {exc}"
                )

    def test_select_region(self):
        """전체 항목을 제외한 모든 동·읍·면 지역 공고를 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-0']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-0']"),
            "지역 탭",
        )
        self.sleep()

        panel = "//div[@role='tabpanel' and @id='panel-0']"
        province_buttons = (
            By.XPATH,
            f"{panel}//span[normalize-space()='시·도']"
            "/parent::div/following-sibling::ul[1]//li[@role='button']",
        )
        district_buttons = (
            By.XPATH,
            f"{panel}//div[normalize-space()='시·구·군']"
            "/following-sibling::ul[1]//li[@role='button']",
        )
        town_buttons = (
            By.XPATH,
            f"{panel}//div[normalize-space()='동·읍·면']"
            "/following-sibling::ul[1]//li[@role='button']",
        )
        provinces = self._visible_names(
            self.wait_for_elements(province_buttons, "시·도 목록"),
        )
        provinces = [province for province in provinces if province != "전국"]
        self.assertTrue(provinces, "순회할 시·도 목록이 없습니다.")

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

        job_locations = (
            By.XPATH,
            "//ul[contains(@class, 'SimpleRecruitList')]//li",
        )
        self.click_element(
            (By.XPATH, "//button[normalize-space()='리스트 펼쳐 보기']"),
            "공고 리스트 그리드뷰 전환",
        )
        self.wait_for_recruit_list_rendered(
            job_locations,
            "그리드뷰 전환 후 공고 목록",
        )

        counter_locator = (
            By.XPATH,
            f"{panel}//div[contains(@class, 'filter-header__counter')]",
        )
        chip_base = (
            "//div[contains(@class, 'selector-chips__list')]"
            "//button[contains(@class, 'selector-chips__chip')]"
        )

        checked_regions = 0
        for province in provinces:
            self.click_element(
                self.region_button_locator(panel, province),
                f"'{province}' 시·도",
            )
            self.sleep()

            districts = self._visible_names(
                self.wait_for_elements(
                    district_buttons,
                    f"{province} 시·구·군 목록",
                ),
                exclude_all=True,
            )
            self.assertTrue(
                districts,
                f"'{province}'의 시·구·군 목록이 없습니다.",
            )

            for district in districts:
                self.click_element(
                    self.region_button_locator(panel, district),
                    f"'{province} {district}' 시·구·군",
                )
                self.sleep()

                towns = self._visible_names(
                    self.wait_for_elements(
                        town_buttons,
                        f"{province} {district} 동·읍·면 목록",
                    ),
                    exclude_all=True,
                )
                self.assertTrue(
                    towns,
                    f"'{province} {district}'의 동·읍·면 목록이 없습니다.",
                )

                for town in towns:
                    region = f"{province} {district} {town}"
                    town_locator = self.region_button_locator(panel, town)
                    self.click_element(town_locator, f"'{region}' 동·읍·면")

                    self.assert_element_text(
                        (By.XPATH, "//label[@role='tab' and @for='tab-0']//em"),
                        "1",
                        f"{region} 선택 후 지역 탭 선택 개수",
                    )
                    self.assert_element_text(
                        counter_locator,
                        "1/5",
                        f"{region} 지역 조건 개수",
                    )
                    self.assert_element_text(
                        (By.XPATH, f"{chip_base}[normalize-space(.)={town!r}]"),
                        town,
                        f"조건 리스트의 {region}",
                    )
                    self._verify_region_jobs(
                        (province, district, town),
                        job_locations,
                    )

                    self.click_element(town_locator, f"'{region}' 동·읍·면 조건 해제")
                    self.assert_element_text(
                        counter_locator,
                        "0/5",
                        f"{region} 조건 해제 확인",
                    )
                    self.assert_no_elements(
                        (By.XPATH, f"{chip_base}[normalize-space(.)={town!r}]"),
                        f"'{region}' 조건 칩이 해제되지 않았습니다.",
                    )
                    self._wait_for_region_results(f"{region} 조건 해제 후 결과 수")
                    checked_regions += 1

                    if checked_regions % self.BROWSER_RESTART_INTERVAL == 0:
                        self._restart_browser_for_region(
                            panel,
                            page_size_locator,
                            job_locations,
                            province,
                            district,
                        )

        self.assertTrue(checked_regions, "검증한 지역이 없습니다.")

        if self.no_job_regions:
            no_job_regions = ", ".join(sorted(self.no_job_regions))
            self._log_action(f"비고: 조회 공고 0건 지역 - {no_job_regions}")

        self.sleep()

    def tearDown(self):
        super().dispose()
