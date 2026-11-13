from contextlib import redirect_stderr, redirect_stdout
from importlib import import_module
import os
import re
import sys
import threading
import time
import unittest
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

BASE_DIR = Path(__file__).resolve().parent
TEST_DIR = BASE_DIR / "TestCase"
LOG_DIR = BASE_DIR / "TestLogs"

class LiveLogStream:
    """백그라운드 테스트 스레드의 로그를 Tkinter UI에 실시간으로 전달한다."""

    def __init__(self, write_callback):
        self.write_callback = write_callback

    def write(self, text):
        if text:
            self.write_callback(text)
        return len(text)

    def flush(self):
        pass


class PerTestLogStream(LiveLogStream):
    """화면 로그를 유지하면서 TC별 텍스트 파일에도 로그를 저장한다."""

    def __init__(self, write_callback, test_names):
        super().__init__(write_callback)
        LOG_DIR.mkdir(exist_ok=True)
        self.current_test = None
        self.log_files = {
            name: (LOG_DIR / f"{name}.txt").open(
                "w",
                encoding="utf-8",
            )
            for name in test_names
        }

    def write(self, text, persist=True):
        if persist and text:
            for name in self.log_files:
                if (
                    f"TestCase.{name}." in text
                    or re.search(rf"\b{re.escape(name)}\b", text)
                ):
                    self.current_test = name

            if self.current_test is not None:
                log_file = self.log_files[self.current_test]
                log_file.write(text)
                log_file.flush()

        return super().write(text)

    def close(self):
        for log_file in self.log_files.values():
            log_file.close()


class StoppableTestResult(unittest.TextTestResult):
    """각 테스트 케이스가 끝난 뒤 중단 요청을 반영하는 테스트 결과 객체."""

    def __init__(self, *args, stop_event=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_event = stop_event

    def _stop_if_requested(self):
        if self.stop_event is not None and self.stop_event.is_set():
            self.stop()

    def addSuccess(self, test):
        super().addSuccess(test)
        self._stop_if_requested()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._stop_if_requested()

    def addError(self, test, err):
        super().addError(test, err)
        self._stop_if_requested()

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._stop_if_requested()


def get_test_names():
    """TestCase 폴더에서 TC*.py 파일명을 숫자 순서로 가져온다."""
    test_files = TEST_DIR.glob("TC*.py")
    return sorted(
        (file.stem for file in test_files if file.stem[2:].isdigit()),
        key=lambda name: int(name[2:]),
    )


class TestSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Albamon 테스트 선택기")
        self.geometry("760x700")
        self.minsize(620, 500)
        self.test_vars = {}
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="실행할 테스트를 선택하세요.")
        self.stop_event = threading.Event()
        self._build_ui()
        self.search_var.trace_add("write", self._filter_tests)

    def _build_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="테스트 검색:").pack(side="left")
        ttk.Entry(top, textvariable=self.search_var, width=24).pack(
            side="left", padx=(6, 12)
        )
        ttk.Button(top, text="전체 선택", command=self.select_all).pack(side="left")
        ttk.Button(top, text="전체 해제", command=self.clear_all).pack(
            side="left", padx=6
        )

        list_frame = ttk.LabelFrame(self, text="실행할 테스트 선택", padding=8)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.canvas = tk.Canvas(list_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.canvas.yview
        )
        self.checkbox_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.checkbox_frame, anchor="nw"
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.checkbox_frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            ),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfigure(
                self.canvas_window, width=event.width
            ),
        )

        for name in get_test_names():
            variable = tk.BooleanVar(value=False)
            self.test_vars[name] = variable
            ttk.Checkbutton(
                self.checkbox_frame, text=name, variable=variable
            ).pack(anchor="w", padx=8, pady=2)

        bottom = ttk.Frame(self, padding=(10, 0, 10, 10))
        bottom.pack(fill="both", expand=True)
        ttk.Label(bottom, textvariable=self.status_var).pack(anchor="w", pady=(0, 5))
        button_frame = ttk.Frame(bottom)
        button_frame.pack(fill="x", pady=(0, 8))
        self.run_button = ttk.Button(
            button_frame, text="선택한 테스트 실행", command=self.run_selected_tests
        )
        self.run_button.pack(side="left", fill="x", expand=True)
        self.stop_button = ttk.Button(
            button_frame,
            text="테스트 중단",
            command=self.stop_tests,
            state="disabled",
        )
        self.stop_button.pack(side="left", fill="x", expand=True, padx=(8, 0))

        terminal_frame = ttk.LabelFrame(bottom, text="터미널 로그", padding=5)
        terminal_frame.pack(fill="both", expand=True, pady=(0, 8))
        self.terminal_output = ScrolledText(
            terminal_frame, height=12, state="disabled"
        )
        self.terminal_output.pack(fill="both", expand=True)

        result_frame = ttk.LabelFrame(bottom, text="실행 결과 요약", padding=5)
        result_frame.pack(fill="x")
        self.output = ScrolledText(result_frame, height=4, state="disabled")
        self.output.pack(fill="x")

    def _filter_tests(self, *_args):
        keyword = self.search_var.get().strip().lower()
        children = self.checkbox_frame.winfo_children()

        # 검색 후 다시 표시할 때도 TC001부터 원래 순서를 유지한다.
        for child in children:
            child.pack_forget()
        for child in children:
            if keyword in child.cget("text").lower():
                child.pack(anchor="w", padx=8, pady=2)

        self.canvas.yview_moveto(0)

    def select_all(self):
        for variable in self.test_vars.values():
            variable.set(True)

    def clear_all(self):
        for variable in self.test_vars.values():
            variable.set(False)

    def _write_output(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def _write_terminal_log(self, text):
        self.terminal_output.configure(state="normal")
        self.terminal_output.insert("end", text)
        self.terminal_output.see("end")
        self.terminal_output.configure(state="disabled")

    def run_selected_tests(self):
        selected = [
            name for name, variable in self.test_vars.items() if variable.get()
        ]
        if not selected:
            messagebox.showwarning("테스트 미선택", "실행할 테스트를 하나 이상 선택하세요.")
            return
        self.stop_event.clear()
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")
        self.terminal_output.configure(state="normal")
        self.terminal_output.delete("1.0", "end")
        self.terminal_output.configure(state="disabled")
        self.status_var.set(f"{len(selected)}개 테스트 실행 중...")
        threading.Thread(
            target=self._run_tests, args=(selected,), daemon=True
        ).start()

    def stop_tests(self):
        """현재 실행 중인 테스트가 끝나면 다음 테스트 실행을 중단하도록 요청한다."""
        if not self.stop_event.is_set():
            self.stop_event.set()
            self.stop_button.configure(state="disabled")
            self.status_var.set("중단 요청됨: 현재 테스트가 끝나면 실행을 중단합니다...")
            self._write_terminal_log("\n[중단 요청] 현재 테스트가 끝나면 실행을 중단합니다.\n")

    def _run_tests(self, selected):
        start_time = time.perf_counter()
        terminal_stream = PerTestLogStream(
            lambda text: self.after(0, self._write_terminal_log, text),
            selected,
        )
        suite = unittest.TestSuite()
        if str(BASE_DIR) not in sys.path:
            sys.path.insert(0, str(BASE_DIR))
        for name in selected:
            # 모듈 안에서 import한 부모 테스트 클래스까지 수집하지 않고,
            # 선택한 파일명과 같은 테스트 클래스만 실행한다.
            module = import_module(f"TestCase.{name}")
            test_class = getattr(module, name)
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromTestCase(test_class)
            )
        with redirect_stdout(terminal_stream), redirect_stderr(terminal_stream):
            result = unittest.TextTestRunner(
                stream=terminal_stream,
                verbosity=2,
                resultclass=lambda *args, **kwargs: StoppableTestResult(
                    *args, stop_event=self.stop_event, **kwargs
                ),
            ).run(suite)
        elapsed = time.perf_counter() - start_time
        stopped = self.stop_event.is_set()
        summary = (
            f"\n실행 결과: 총 {result.testsRun}개, "
            f"성공 {result.testsRun - len(result.failures) - len(result.errors)}개, "
            f"실패 {len(result.failures)}개, 오류 {len(result.errors)}개\n"
            f"소요 시간: {int(elapsed // 60)}분 {elapsed % 60:.2f}초\n"
        )
        if stopped:
            summary += "결과: 사용자 요청으로 테스트 실행을 중단했습니다.\n"
        terminal_stream.write(summary, persist=False)
        terminal_stream.close()
        self.after(0, self._finish_run, summary, result.wasSuccessful(), stopped)

    def _finish_run(self, output, success, stopped):
        self._write_output(output)
        if stopped:
            self.status_var.set("테스트 실행이 중단되었습니다.")
        else:
            self.status_var.set(
                "테스트 실행 완료" if success else "실패한 테스트가 있습니다."
            )
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    TestSelector().mainloop()
