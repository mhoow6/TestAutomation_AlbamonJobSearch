import json
from datetime import datetime
from pathlib import Path

from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC012(TCBase):
    URL = f"{TCBase.URL}&similarDongJoin=true"

    # 최초 1회 기준 데이터를 생성할 때만 True로 변경한다.
    # 생성 후에는 반드시 False로 되돌리고 테스트를 실행한다.
    GENERATE_BASELINE = False

    BASELINE_PATH = Path(__file__).with_name("TC012_ExpectedData.json")

    def setUp(self):
        super().init()

    def region_button_locator(self, panel, name):
        """지역명으로 시·도 또는 시·구·군 항목을 찾는 XPath를 생성한다."""
        return (
            By.XPATH,
            f"{panel}//li[@role='button' and normalize-space()={name!r}]",
        )

    def _read_towns(self, town_buttons, region):
        """현재 선택된 지역의 동·읍·면 목록을 읽는다."""
        try:
            return self.wait.until(
                lambda driver: self._towns_ready(driver, town_buttons)
            )
        except Exception as exc:
            self.fail(f"'{region}'의 동·읍·면 목록을 읽을 수 없습니다: {exc}")

    @staticmethod
    def _towns_ready(driver, town_buttons):
        """동·읍·면 목록이 표시되면 텍스트 목록을 반환한다."""
        towns = [
            button.text.strip()
            for button in driver.find_elements(*town_buttons)
            if button.text.strip()
        ]
        return towns if towns else False

    @staticmethod
    def _visible_region_names(elements, exclude_all=False):
        """지역 버튼에서 공백 및 전체 항목을 제외한 이름을 추출한다."""
        names = []
        for element in elements:
            name = element.text.strip()
            if not name:
                continue
            if exclude_all and name.endswith("전체"):
                continue
            names.append(name)
        return names

    def _collect_all_towns(
        self,
        panel,
        provinces,
        district_buttons,
        town_buttons,
    ):
        """
        유사동 묶기가 해제된 상태에서 전국 지역을 순회해
        시·도 > 시·구·군 > 동·읍·면 구조로 수집한다.
        """
        collected_data = {}

        for province in provinces:
            self.click_element(
                self.region_button_locator(panel, province),
                f"'{province}' 시·도 선택",
            )
            self.sleep()

            districts = self._visible_region_names(
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

            collected_data[province] = {}

            for district in districts:
                region = f"{province} {district}"

                self.click_element(
                    self.region_button_locator(panel, district),
                    f"'{region}' 시·구·군 선택",
                )
                self.sleep()

                towns = self._read_towns(town_buttons, region)

                # 중복 여부는 set 변환 전에 확인할 수 있도록 원본 목록을 보존한다.
                collected_data[province][district] = towns

        return collected_data

    def _save_baseline(self, data):
        """UI에서 수집한 OFF 상태의 전국 목록을 기준 JSON으로 저장한다."""
        baseline = {
            "description": (
                "유사동 묶기 OFF 상태에서 UI를 통해 수집한 "
                "시·도/시·구·군별 동·읍·면 기준 목록"
            ),
            "collected_at": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "source": "UI",
            "data": data,
        }

        with self.BASELINE_PATH.open("w", encoding="utf-8") as file:
            json.dump(baseline, file, ensure_ascii=False, indent=2)

    def _load_baseline(self):
        """기준 JSON을 읽는다. 파일이 없으면 생성 절차를 안내하고 실패한다."""
        if not self.BASELINE_PATH.exists():
            self.fail(
                "기준 데이터 파일이 없습니다.\n"
                f"파일 위치: {self.BASELINE_PATH}\n"
                "최초 1회 기준 데이터 생성이 필요합니다. "
                "TC012.GENERATE_BASELINE = True로 변경해 실행한 뒤, "
                "다시 False로 변경하고 테스트를 실행하세요."
            )

        try:
            with self.BASELINE_PATH.open("r", encoding="utf-8") as file:
                baseline = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            self.fail(f"기준 데이터 파일을 읽을 수 없습니다: {exc}")

        data = baseline.get("data")
        self.assertIsInstance(data, dict, "기준 데이터의 data 구조가 올바르지 않습니다.")
        self.assertTrue(data, "기준 데이터에 지역 정보가 없습니다.")
        return data

    def _assert_region_data(self, expected_data, actual_data):
        """기준 데이터와 실제 UI 목록을 지역별로 비교한다."""
        expected_provinces = set(expected_data)
        actual_provinces = set(actual_data)

        self.assertFalse(
            expected_provinces - actual_provinces,
            f"누락된 시·도: {sorted(expected_provinces - actual_provinces)}",
        )
        self.assertFalse(
            actual_provinces - expected_provinces,
            f"기준 데이터에 없는 시·도: {sorted(actual_provinces - expected_provinces)}",
        )

        errors = []

        for province, expected_districts in expected_data.items():
            actual_districts = actual_data[province]

            missing_districts = set(expected_districts) - set(actual_districts)
            unexpected_districts = set(actual_districts) - set(expected_districts)

            if missing_districts:
                errors.append(
                    f"[{province}] 누락된 시·구·군: {sorted(missing_districts)}"
                )
            if unexpected_districts:
                errors.append(
                    f"[{province}] 기준 데이터에 없는 시·구·군: "
                    f"{sorted(unexpected_districts)}"
                )

            for district, expected_towns in expected_districts.items():
                if district not in actual_districts:
                    continue

                actual_towns = actual_districts[district]
                region = f"{province} {district}"

                duplicated_towns = sorted({
                    town for town in actual_towns
                    if actual_towns.count(town) > 1
                })
                if duplicated_towns:
                    errors.append(
                        f"[{region}] 중복 표시된 동·읍·면: {duplicated_towns}"
                    )

                missing_towns = set(expected_towns) - set(actual_towns)
                unexpected_towns = set(actual_towns) - set(expected_towns)

                if missing_towns:
                    errors.append(
                        f"[{region}] 누락된 동·읍·면: {sorted(missing_towns)}"
                    )
                if unexpected_towns:
                    errors.append(
                        f"[{region}] 기준 데이터에 없는 동·읍·면: "
                        f"{sorted(unexpected_towns)}"
                    )

        self.assertFalse(
            errors,
            "유사동 묶기 해제 후 기준 데이터와 실제 목록이 일치하지 않습니다.\n"
            + "\n".join(errors),
        )

    def test_ungroup_similar_dong(self):
        """유사동 묶기 해제 후 전국의 개별 동·읍·면이 표시되는지 확인한다."""
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

        # 사전 조건: URL의 similarDongJoin=true에 따라 유사동 묶기가 선택되어 있어야 한다.
        self.wait_for_selected(
            similar_dong_checkbox,
            "사전 조건 유사동 묶기 선택 상태",
        )

        provinces = self._visible_region_names(
            self.wait_for_elements(province_buttons, "시·도 목록"),
        )
        provinces = [province for province in provinces if province != "전국"]
        self.assertTrue(provinces, "순회할 시·도 목록이 없습니다.")

        # 테스트 수행: 유사동 묶기를 해제한다.
        self.click_element(similar_dong_label, "유사동 묶기 해제")
        self.wait_for_not_selected(
            similar_dong_checkbox,
            "유사동 묶기 해제 상태",
        )
        self.sleep()

        # 기준 데이터 생성 모드: 최초 1회 OFF 상태의 UI 목록을 수집해 JSON으로 저장한다.
        if self.GENERATE_BASELINE:
            baseline_data = self._collect_all_towns(
                panel,
                provinces,
                district_buttons,
                town_buttons,
            )
            self._save_baseline(baseline_data)
            self.skipTest(
                "기준 데이터 생성을 완료했습니다. "
                "GENERATE_BASELINE을 False로 변경한 뒤 테스트를 실행하세요."
            )

        # 일반 테스트 모드: 기존 기준 데이터와 OFF 상태의 실제 UI 목록을 비교한다.
        expected_data = self._load_baseline()
        actual_data = self._collect_all_towns(
            panel,
            provinces,
            district_buttons,
            town_buttons,
        )

        self._assert_region_data(expected_data, actual_data)

    def tearDown(self):
        super().dispose()
