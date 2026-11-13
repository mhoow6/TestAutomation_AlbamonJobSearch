import re

from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC011(TCBase):
    def setUp(self):
        super().init()

    def test_group_similar_dong(self):
        """초기 상태에서 모든 지역의 유사동 묶기 결과를 검증한다."""
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
        similar_dong_checkbox = (
            By.XPATH,
            f"{panel}//input[@name='group-similar']",
        )
        similar_dong_label = (
            By.XPATH,
            f"{panel}//label[.//input[@name='group-similar']]",
        )

        # 사전 조건: 지역 조건을 선택하지 않은 초기 상태여야 한다.
        self.assert_for_not_selected(
            similar_dong_checkbox,
            "초기 상태에서 유사동 묶기가 선택되어 있습니다.",
        )

        # 테스트 절차: 유사동 묶기를 선택한다.
        self.select_if_not_selected(
            similar_dong_checkbox,
            similar_dong_label,
            "유사동 묶기",
        )
        self.sleep()

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

        provinces = [
            button.text.strip()
            for button in self.wait_for_elements(
                province_buttons,
                "시·도 목록",
            )
            if button.text.strip() and button.text.strip() != "전국"
        ]
        self.assertTrue(provinces, "순회할 시·도 목록이 없습니다.")

        numeric_town_pattern = re.compile(r"\d+(?:동|읍|면)")
        allowed_numeric_towns = {
            "경기 광주시": {"오포1동", "오포2동"},
        }
        checked_regions = []

        for province in provinces:
            self.click_element(
                (
                    By.XPATH,
                    f"{panel}//li[@role='button' and "
                    f"normalize-space()={province!r}]",
                ),
                f"'{province}' 시·도",
            )
            self.sleep()

            districts = [
                button.text.strip()
                for button in self.wait_for_elements(
                    district_buttons,
                    f"{province} 시·구·군 목록",
                )
                if button.text.strip()
                and not button.text.strip().endswith("전체")
            ]
            self.assertTrue(
                districts,
                f"'{province}'의 시·구·군 목록이 없습니다.",
            )

            for district in districts:
                self.click_element(
                    (
                        By.XPATH,
                        f"{panel}//li[@role='button' and "
                        f"normalize-space()={district!r}]",
                    ),
                    f"'{province} {district}' 시·구·군",
                )
                self.sleep()

                towns = [
                    button.text.strip()
                    for button in self.browser.find_elements(*town_buttons)
                    if button.text.strip()
                ]
                self.assertTrue(
                    towns,
                    f"'{province} {district}'의 동·읍·면 목록이 없습니다.",
                )
                invalid_towns = [
                    town
                    for town in towns
                    if numeric_town_pattern.search(town)
                    and town not in allowed_numeric_towns.get(
                        f"{province} {district}",
                        set(),
                    )
                ]
                self.assertFalse(
                    invalid_towns,
                    f"'{province} {district}'의 동·읍·면에 숫자 표기가 "
                    f"남아 있습니다: {invalid_towns}",
                )
                checked_regions.append(f"{province} {district}")

        self.assertTrue(
            checked_regions,
            "시·도 및 시·구·군 순회가 수행되지 않았습니다.",
        )
        self.sleep()

    def tearDown(self):
        super().dispose()
