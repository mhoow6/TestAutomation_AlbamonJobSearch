import re
import time
import unittest
from datetime import datetime

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoAlertPresentException,
    StaleElementReferenceException,
)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TCBase(unittest.TestCase):
    URL = "https://www.albamon.com/jobs/range?page=1"
    URL_FAKE = "https://www.naver.com"
    SEC_WAIT_TIMEOUT = 10
    DEBUG_WAIT_TIME = 1
    RECRUIT_LIST_RENDER_WAIT = 2
    MAX_JOBS = 500

    def init(self):
        """Selenium WebDriver와 공통 명시적 대기를 초기화한다."""
        self._log_action(f"{self.__class__.__name__} 실행")
        self.browser = webdriver.Chrome(
            service=Service(),
            options=Options(),
        )
        self.wait = WebDriverWait(self.browser, self.SEC_WAIT_TIMEOUT)

    def _log_action(self, action):
        """자동화 도구가 수행한 액션을 터미널에 기록한다."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {action}", flush=True)

    def load(self):
        """테스트 대상 페이지에 접속하고 페이지 제목으로 로딩을 확인한다."""
        try:
            self._log_action(f"페이지 접속: {self.URL}")
            self.browser.get(self.URL)
            self.wait_for_element(
                (By.XPATH, "//h1[normalize-space()='기간 요일 시간별']"),
                "기간 요일 시간별 페이지 제목",
            )
        except Exception as exc:
            self.fail(f"검색 조건 페이지 로딩 확인 중 오류가 발생했습니다: {exc}")

    def _get_detail_work_day(self, detail_link, title):
        """공고 상세를 새 탭에서 확인하고 목록 탭으로 돌아온다."""
        original_handle = self.browser.current_window_handle
        original_handles = set(self.browser.window_handles)
        detail_handle = None

        try:
            self._log_action(f"공고 상세 새 탭 여는 중: {title}")
            detail_url = detail_link.get_attribute("href")
            if not detail_url:
                self.fail(f"공고 상세 URL을 찾을 수 없습니다: {title}")

            self.browser.execute_script("window.open(arguments[0], '_blank');", detail_url)
            self.wait.until(
                lambda driver: len(set(driver.window_handles) - original_handles) == 1
            )
            detail_handle = next(
                handle
                for handle in self.browser.window_handles
                if handle not in original_handles
            )
            self.browser.switch_to.window(detail_handle)
            self.sleep(2)

            alert = self.get_alert(self.browser)
            if alert:
                alert_message = alert.text
                alert.accept()
                self._log_action(
                    f"마감 공고 알림 확인 후 검증 제외: {alert_message} "
                    f"(공고: {title})"
                )
                return None

            detail_work_day_locator = (
                By.XPATH,
                "//dt[normalize-space()='근무요일']/following-sibling::dd[1]",
            )
            self.wait_for_element(detail_work_day_locator, f"'{title}' 상세 근무요일")
            detail_work_day = " ".join(
                self.browser.find_element(*detail_work_day_locator).text.split()
            )
            self._log_action(
                f"상세 근무요일 확인: {detail_work_day}"
            )
            return detail_work_day
        finally:
            if detail_handle and detail_handle in self.browser.window_handles:
                self.browser.close()
            if original_handle in self.browser.window_handles:
                self.browser.switch_to.window(original_handle)
                self.wait_for_elements(
                    (By.XPATH, "//ul[contains(@class, 'SimpleRecruitList')]//li"),
                    "공고 목록 유지",
                )

    def dispose(self):
        """WebDriver를 종료한다."""
        browser = getattr(self, "browser", None)
        if browser is not None:
            #self._log_action("브라우저 종료")
            browser.quit()

    def read_job_locations(self, job_locations, retry_count=3):
        """DOM 갱신으로 요소 참조가 만료되면 공고 목록을 다시 조회한다."""
        for attempt in range(retry_count):
            try:
                elements = self.browser.find_elements(*job_locations)
                return [
                    re.sub(r"\s+", " ", element.text).strip()
                    for element in elements
                ]
            except StaleElementReferenceException:
                if attempt == retry_count - 1:
                    raise
                self.sleep()

        return []

    def sleep(self, sec = DEBUG_WAIT_TIME):
        """디버깅을 위해 고정 시간 동안 대기한다."""
        time.sleep(sec)

    # ------------------------------------------------------------------
    # 공통 요소 탐색 및 조작
    # ------------------------------------------------------------------
    def region_button_locator(self, panel, name):
        """지역명으로 시·도, 시·구·군 또는 동·읍·면 버튼 XPath를 생성한다."""
        return (
            By.XPATH,
            f"{panel}//li[@role='button' and normalize-space(.)={name!r}]",
        )

    def wait_for_element(self, locator, name="요소"):
        """요소가 DOM에 나타날 때까지 기다린 뒤 반환한다."""
        try:
            return self.wait.until(EC.presence_of_element_located(locator))
        except Exception as exc:
            self.fail(f"'{name}' 요소를 찾을 수 없습니다: {exc}")

    def dismiss_interfering_layer(self):
        """화면을 가리는 알바몬 레이어를 닫고 클릭을 재시도할 수 있게 한다."""
        try:
            self.browser.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass

        try:
            layers = self.browser.find_elements(
                By.CSS_SELECTOR,
                "[class*='HeaderRecruitLayer']",
            )
            for layer in layers:
                if not layer.is_displayed():
                    continue

                close_buttons = layer.find_elements(
                    By.XPATH,
                    ".//button[contains(translate(@aria-label, "
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
                    "'close') or contains(@title, '닫기') or "
                    "contains(normalize-space(.), '닫기')]",
                )
                for close_button in close_buttons:
                    if close_button.is_displayed() and close_button.is_enabled():
                        close_button.click()
                        return
        except Exception:
            pass

    def click_element(self, locator, name="요소"):
        """요소가 클릭 가능해질 때까지 기다린 뒤 클릭한다."""
        last_intercepted = None
        for attempt in range(2):
            try:
                self._log_action(
                    f"클릭 시도: {name} | 재시도={attempt}"
                )
                element = self.wait.until(EC.element_to_be_clickable(locator))
                element.click()
                self._log_action(f"클릭 완료: {name}")
                return element
            except ElementClickInterceptedException as exc:
                last_intercepted = exc
                self._log_action(f"클릭 가로막힘: {name}")
                if attempt == 0:
                    self.dismiss_interfering_layer()
                    self.sleep(0.2)
                    continue
                self.fail(f"'{name}' 클릭 중 오류가 발생했습니다: {exc}")
            except Exception as exc:
                self.fail(f"'{name}' 클릭 중 오류가 발생했습니다: {exc}")

        self.fail(f"'{name}' 클릭 중 오류가 발생했습니다: {last_intercepted}")

    def wait_for_elements(self, locator, name="요소 목록"):
        """locator에 해당하는 요소가 하나 이상 나타날 때까지 기다린다."""
        try:
            return self.wait.until(
                lambda driver: driver.find_elements(*locator) or False
            )
        except Exception as exc:
            self.fail(f"'{name}'이(가) 표시되지 않았습니다: {exc}")

    def wait_for_recruit_list_rendered(self, locator, name="공고 목록"):
        """목록 보기 변경 후 공고 목록이 다시 렌더링될 때까지 기다린다."""
        self.sleep(self.RECRUIT_LIST_RENDER_WAIT)
        return self.wait_for_elements(locator, name)

    def get_alert(self, driver):
        """native alert 또는 confirm 창이 표시되면 반환하고, 없으면 재시도한다."""
        try:
            return driver.switch_to.alert
        except NoAlertPresentException:
            return False

    def scroll_to_pagination(self, next_page_locator):
        """페이지네이션 영역으로 스크롤하고 다음 페이지 버튼 목록을 반환한다."""
        try:
            next_page = self.browser.find_elements(*next_page_locator)
            if next_page:
                scroll_target = next_page[0]
            else:
                scroll_target = self.browser.find_element(
                    By.XPATH,
                    "//*[@role='navigation']",
                )

            self.browser.execute_script(
                "arguments[0].scrollIntoView({"
                "behavior: 'smooth', block: 'center'});",
                scroll_target,
            )
            self.sleep()
            return next_page
        except Exception as exc:
            self.fail(f"페이지네이션 영역 스크롤 중 오류가 발생했습니다: {exc}")

    # ------------------------------------------------------------------
    # 선택 상태 처리
    # ------------------------------------------------------------------
    def is_element_selected(self, locator, selected_class=None):
        """
        요소의 선택 상태를 반환한다.
        selected_class가 주어지면 class 속성에서 해당 클래스 토큰을 확인하고,
        그렇지 않으면 Selenium의 is_selected()를 사용한다.
        """
        element = self.browser.find_element(*locator)

        if selected_class:
            classes = (element.get_attribute("class") or "").split()
            return selected_class in classes

        return element.is_selected()

    def wait_for_selected(self, locator, name="요소", selected_class=None):
        """요소가 선택 상태가 될 때까지 기다린다."""
        #self.highlight_element(locator, name)
        try:
            self.wait.until(
                lambda driver: self.is_element_selected(locator, selected_class)
            )
        except Exception as exc:
            self.fail(f"'{name}'이(가) 선택 상태가 되지 않았습니다: {exc}")

    def wait_for_not_selected(self, locator, name="요소", selected_class=None):
        """요소가 선택 해제 상태가 될 때까지 기다린다."""
        #self.highlight_element(locator, name)
        try:
            self.wait.until(
                lambda driver: not self.is_element_selected(locator, selected_class)
            )
        except Exception as exc:
            self.fail(f"'{name}'이(가) 여전히 선택되어 있습니다: {exc}")

    def select_if_not_selected(
        self,
        state_locator,
        click_locator,
        name="요소",
        selected_class=None,
    ):
        """
        선택되지 않은 경우 클릭하고 선택 상태가 될 때까지 기다린다.

        state_locator: 선택 여부를 확인할 요소의 locator
        click_locator: 실제 클릭할 요소의 locator (예: 탭 label)
        selected_class: 일반 요소가 CSS 클래스로 선택 상태를 표현할 때 사용
        """
        try:
            self.wait_for_element(state_locator, name)

            if not self.is_element_selected(state_locator, selected_class):
                self.click_element(click_locator, name)
                self.wait_for_selected(state_locator, name, selected_class)
        except Exception as exc:
            self.fail(f"'{name}' 선택 중 오류가 발생했습니다: {exc}")

    # ------------------------------------------------------------------
    # 화면에서 요소를 확인하기 위한 하이라이트
    # ------------------------------------------------------------------
    def highlight_element(self, locator, name="확인 대상", color="#ff4d4f"):
        """
        현재 화면 위치를 유지하면서 일정 시간 동안 배경색으로 강조한다.
        """
        try:
            element = self.wait.until(EC.visibility_of_element_located(locator))
            self.browser.execute_script(
                """
                const element = arguments[0];
                element.scrollIntoView({behavior: 'smooth', block: 'center'});
                const previousBackgroundColor = element.style.getPropertyValue('background-color');
                const previousBackgroundPriority = element.style.getPropertyPriority('background-color');
                const previousOutline = element.style.getPropertyValue('outline');
                const previousOutlinePriority = element.style.getPropertyPriority('outline');
                clearTimeout(element.__seleniumHighlightTimer);
                element.style.setProperty('background-color', 'rgba(144, 238, 144, 0.35)', 'important');
                element.style.setProperty('outline', '3px solid #ff4d4f', 'important');
                element.setAttribute('data-selenium-highlight', 'true');
                element.__seleniumHighlightTimer = window.setTimeout(() => {
                    if (!element.isConnected) return;
                    if (previousBackgroundColor) {
                        element.style.setProperty(
                            'background-color',
                            previousBackgroundColor,
                            previousBackgroundPriority,
                        );
                    } else {
                        element.style.removeProperty('background-color');
                    }
                    if (previousOutline) {
                        element.style.setProperty('outline', previousOutline, previousOutlinePriority);
                    } else {
                        element.style.removeProperty('outline');
                    }
                    element.removeAttribute('data-selenium-highlight');
                    delete element.__seleniumHighlightTimer;
                }, Math.max(arguments[2], 2) * 1000);
                """,
                element,
                color,
                self.DEBUG_WAIT_TIME,
            )
            return element
        except Exception as exc:
            self._log_action(f"하이라이트 실패: {exc}")
            return None

    def highlight_elements(self, locator, name="확인 대상 목록", color="#ff4d4f"):
        """현재 존재하는 locator 일치 요소들을 모두 강조한다."""
        try:
            elements = self.browser.find_elements(*locator)
            for element in elements:
                self.browser.execute_script(
                    """
                    const element = arguments[0];
                    const previousBackgroundColor = element.style.getPropertyValue('background-color');
                    const previousBackgroundPriority = element.style.getPropertyPriority('background-color');
                    clearTimeout(element.__seleniumHighlightTimer);
                    element.style.setProperty('background-color', 'rgba(144, 238, 144, 0.35)', 'important');
                    element.setAttribute('data-selenium-highlight', 'true');
                    element.__seleniumHighlightTimer = window.setTimeout(() => {
                        if (!element.isConnected) return;
                        if (previousBackgroundColor) {
                            element.style.setProperty(
                                'background-color',
                                previousBackgroundColor,
                                previousBackgroundPriority,
                            );
                        } else {
                            element.style.removeProperty('background-color');
                        }
                        element.removeAttribute('data-selenium-highlight');
                        delete element.__seleniumHighlightTimer;
                    }, arguments[2] * 1000);
                    """,
                    element,
                    color,
                    self.DEBUG_WAIT_TIME,
                )
            return elements
        except Exception as exc:
            self._log_action(f"하이라이트 실패: {exc}")
            return []

    # ------------------------------------------------------------------
    # 공통 검증
    # ------------------------------------------------------------------
    def assert_element_text(self, locator, expected_text, name="요소"):
        """요소를 하이라이트한 뒤 텍스트를 기다려 검증한다."""
        self.highlight_element(locator, name)
        try:
            self.wait.until(
                lambda driver: driver.find_element(*locator).text.strip()
                == expected_text
            )
        except Exception as exc:
            self.fail(
                f"'{name}'의 텍스트가 '{expected_text}'(으)로 표시되지 않았습니다: {exc}"
            )

    def assert_no_elements(self, locator, message, highlight_locator=None, name="확인 영역"):
        """해당 locator의 요소가 모두 사라질 때까지 기다린다.

        대상이 없어야 하는 검증이므로, 필요하면 highlight_locator로 상위 영역을 강조한다.
        """
        if highlight_locator is not None:
            self.highlight_element(highlight_locator, name)
        try:
            self.wait.until(lambda driver: len(driver.find_elements(*locator)) == 0)
        except Exception:
            self.fail(message)

    def assert_elements_exist(self, locator, message):
        """해당 locator의 요소가 하나 이상 표시되는지 검증한다."""
        self.highlight_elements(locator, message)
        try:
            elements = self.wait_for_elements(locator, message)
            self.assertGreater(len(elements), 0, message)
        except Exception as exc:
            self.fail(f"{message}: {exc}")

    def assert_element_disabled(self, locator, message):
        """요소가 비활성화될 때까지 기다린다."""
        self.highlight_element(locator, message)
        try:
            self.wait.until(
                lambda driver: not driver.find_element(*locator).is_enabled()
            )
        except Exception:
            self.fail(message)

    def assert_for_not_selected(
        self,
        locator,
        message,
        selected_class=None,
        highlight_locator=None,
    ):
        """요소가 선택되지 않은 상태인지 즉시 검증한다."""
        self.highlight_element(highlight_locator or locator, message)
        try:
            is_selected = self.is_element_selected(locator, selected_class)
        except Exception as exc:
            self.fail(f"{message}: 선택 상태 확인 중 오류가 발생했습니다: {exc}")

        self.assertFalse(is_selected, message)
