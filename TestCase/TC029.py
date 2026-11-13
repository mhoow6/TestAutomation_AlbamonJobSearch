import re

from selenium.webdriver.common.by import By

from Module.TCBase import TCBase


class TC029(TCBase):
    """업직종 키워드 검색 결과가 실제 업직종 목록에 포함되는지 확인한다."""

    def setUp(self):
        super().init()

    def test_keyword_search_serving(self):
        """조건 미선택 상태에서 서빙 검색 결과가 업직종 목록에 존재하는지 확인한다."""
        super().load()

        self.select_if_not_selected(
            (By.XPATH, "//input[@id='tab-1']"),
            (By.XPATH, "//label[@role='tab' and @for='tab-1']"),
            "업직종 탭",
        )
        self.sleep()

        # 업직종 하위 목록은 선택된 대분류만 DOM에 렌더링되므로,
        # 검색 전 모든 대분류를 순회해 전체 업직종 목록을 수집한다.
        category_panel = "//div[@role='tabpanel' and @id='panel-1']"
        category_items = (
            By.XPATH,
            f"{category_panel}//li[starts-with(@id, 'category-')]",
        )
        self.wait_for_elements(category_items, "업직종 대분류 목록")

        category_ids = [
            category.get_attribute("id")
            for category in self.browser.find_elements(*category_items)
        ]
        part_items = (
            By.XPATH,
            f"{category_panel}//li[starts-with(@id, 'part-')]",
        )
        job_type_names = []
        previous_part_ids = set()
        for category_id in category_ids:
            category_locator = (By.ID, category_id)
            category = self.browser.find_element(*category_locator)
            if "--selected__" not in (category.get_attribute("class") or ""):
                self.click_element(category_locator, f"'{category_id}' 대분류")

            self.wait_for_elements(part_items, f"'{category_id}' 업직종 목록")
            self.wait.until(
                lambda driver: self._category_parts_loaded(
                    driver,
                    category_id,
                    part_items,
                    previous_part_ids,
                )
            )
            current_part_items = self.browser.find_elements(*part_items)
            job_type_names.extend(
                re.sub(r"\s+", " ", element.text).strip()
                for element in current_part_items
                if element.text.strip()
            )
            previous_part_ids = {
                element.get_attribute("id") for element in current_part_items
            }

        self.assertTrue(job_type_names, "업직종 목록을 수집하지 못했습니다.")

        keyword_input = (
            By.CSS_SELECTOR,
            "input[name='filter-search'][placeholder*='키워드 검색']",
        )
        self.wait_for_element(keyword_input, "업직종 키워드 검색창")
        self.browser.find_element(*keyword_input).send_keys("서빙")

        search_results = (
            By.XPATH,
            "//div[@role='tabpanel' and @id='panel-1']"
            "//ul[contains(@class, 'autocomplete-list')]"
            "//li",
        )
        self.wait_for_elements(search_results, "서빙 키워드 검색 결과")

        result_names = {
            re.sub(r"\s+", " ", element.text).strip()
            for element in self.browser.find_elements(*search_results)
            if element.text.strip()
        }
        self.assertTrue(result_names, "서빙 키워드 검색 결과를 수집하지 못했습니다.")

        invalid_results = sorted(result_names - set(job_type_names))
        self.assertFalse(
            invalid_results,
            "키워드 검색 결과에 업직종 목록에 없는 항목이 있습니다: "
            f"{invalid_results}",
        )

    @staticmethod
    def _category_parts_loaded(driver, category_id, part_items, previous_part_ids):
        """선택 대분류가 활성화되고 하위 업직종 DOM이 교체되었는지 확인한다."""
        category = driver.find_element(By.ID, category_id)
        if "--selected__" not in (category.get_attribute("class") or ""):
            return False

        current_part_ids = {
            element.get_attribute("id") for element in driver.find_elements(*part_items)
        }
        return bool(current_part_ids) and (
            not previous_part_ids or current_part_ids != previous_part_ids
        )

    def tearDown(self):
        super().dispose()
