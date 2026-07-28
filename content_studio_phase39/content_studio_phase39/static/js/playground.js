(() => {
    const workerUrl = document.body.dataset.pythonWorker || document.querySelector("[data-python-worker]")?.dataset.pythonWorker;
    if (!workerUrl || typeof Worker === "undefined") return;

    let requestNumber = 0;

    class PythonPlayground {
        constructor(element) {
            this.element = element;
            this.editor = element.querySelector("[data-python-editor]");
            this.output = element.querySelector("[data-python-output]");
            this.runButton = element.querySelector("[data-python-run]");
            this.stopButton = element.querySelector("[data-python-stop]");
            this.resetButton = element.querySelector("[data-python-reset]");
            this.testButton = element.querySelector("[data-python-run-tests]");
            this.saveButton = element.querySelector("[data-python-save-attempt]");
            this.originalCode = this.editor.value;
            this.lastOutput = "";
            this.lastPassed = false;
            this.lastTestResults = [];
            this.lastTestsPassed = 0;
            this.lastTestsTotal = 0;
            this.worker = null;
            this.timeout = null;
            this.pendingId = null;
            this.pendingResolve = null;

            this.testCases = this.parseTestCases();
            this.runButton.addEventListener("click", () => this.run());
            this.stopButton.addEventListener("click", () => this.stop("Execution stopped."));
            this.resetButton.addEventListener("click", () => this.reset());
            if (this.testButton) this.testButton.addEventListener("click", () => this.runTests());
            if (this.saveButton) this.saveButton.addEventListener("click", () => this.saveAttempt());
            this.editor.addEventListener("keydown", (event) => {
                if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                    event.preventDefault();
                    this.run();
                }
            });
        }

        parseTestCases() {
            const script = this.element.previousElementSibling?.matches?.("[data-challenge-tests]")
                ? this.element.previousElementSibling
                : null;
            if (!script) return [];
            try {
                const parsed = JSON.parse(script.textContent || "[]");
                return Array.isArray(parsed) ? parsed : [];
            } catch (error) {
                return [];
            }
        }

        ensureWorker() {
            if (this.worker) return;
            this.worker = new Worker(workerUrl, { type: "module" });
            this.worker.addEventListener("message", (event) => this.receive(event));
            this.worker.addEventListener("error", () => {
                this.resolvePending({ status: "error", error: "The Python runtime could not load. Check your internet connection." });
                this.destroyWorker();
            });
        }

        setBusy(isBusy, message = "") {
            this.runButton.disabled = isBusy;
            this.stopButton.disabled = !isBusy;
            if (this.testButton) this.testButton.disabled = isBusy;
            if (this.saveButton && isBusy) this.saveButton.disabled = true;
            this.element.classList.toggle("is-running", isBusy);
            if (message) this.output.textContent = message;
        }

        executeCode(code, timeoutMs = 12000) {
            return new Promise((resolve) => {
                if (this.pendingId !== null) {
                    resolve({ status: "error", error: "Another Python run is already in progress." });
                    return;
                }
                this.ensureWorker();
                this.pendingId = ++requestNumber;
                this.pendingResolve = resolve;
                this.worker.postMessage({ id: this.pendingId, code });
                this.timeout = window.setTimeout(() => {
                    this.resolvePending({ status: "error", error: "Execution stopped after 12 seconds. Check for an infinite loop." });
                    this.destroyWorker();
                }, timeoutMs);
            });
        }

        receive(event) {
            if (event.data.id !== this.pendingId) return;
            if (event.data.status === "running") {
                window.clearTimeout(this.timeout);
                this.timeout = window.setTimeout(() => {
                    this.resolvePending({ status: "error", error: "Execution stopped after 12 seconds. Check for an infinite loop." });
                    this.destroyWorker();
                }, 12000);
                return;
            }
            this.resolvePending(event.data);
        }

        resolvePending(payload) {
            window.clearTimeout(this.timeout);
            this.timeout = null;
            this.pendingId = null;
            const resolve = this.pendingResolve;
            this.pendingResolve = null;
            if (resolve) resolve(payload);
        }

        formatResult(payload) {
            if (payload.status === "error") return { message: payload.error || "Python returned an unknown error.", isError: true };
            const parts = [payload.stdout, payload.stderr, payload.result].filter(Boolean);
            return { message: parts.join("\n") || "Code completed with no output.", isError: Boolean(payload.stderr) };
        }

        evaluateOutput(message, isError) {
            if (isError) return { passed: false, message };
            const expected = this.element.dataset.expectedOutput;
            const validationMode = this.element.dataset.validationMode || "exact_output";
            if (!expected || validationMode === "manual") return { passed: false, message };
            if (validationMode === "contains_output" && message.includes(expected.trim())) {
                return { passed: true, message: `${message}\n\n✅ Output contains the expected result.` };
            }
            if (validationMode === "exact_output" && message.trim() === expected.trim()) {
                return { passed: true, message: `${message}\n\n✅ Output matches the expected result.` };
            }
            return { passed: false, message: `${message}\n\nExpected output:\n${expected}` };
        }

        async run() {
            this.output.classList.remove("has-error", "is-match");
            this.lastPassed = false;
            this.lastTestResults = [];
            this.lastTestsPassed = 0;
            this.lastTestsTotal = 0;
            this.setBusy(true, "Loading Python and running your code…");
            const payload = await this.executeCode(this.editor.value, 60000);
            const formatted = this.formatResult(payload);
            const evaluated = this.evaluateOutput(formatted.message, formatted.isError);
            this.lastOutput = evaluated.message;
            this.lastPassed = evaluated.passed;
            this.output.textContent = evaluated.message;
            this.output.classList.toggle("has-error", formatted.isError);
            this.output.classList.toggle("is-match", evaluated.passed);
            this.setBusy(false);
            if (this.saveButton) this.saveButton.disabled = false;
        }

        async runTests() {
            if (!this.testCases.length) {
                await this.run();
                return;
            }
            this.output.classList.remove("has-error", "is-match");
            this.setBusy(true, "Running challenge tests…");
            this.lastTestResults = [];
            this.lastTestsPassed = 0;
            this.lastTestsTotal = this.testCases.length;

            for (const [index, test] of this.testCases.entries()) {
                this.output.textContent = `Running test ${index + 1} of ${this.testCases.length}…`;
                const code = `${this.editor.value}\n\n# --- Code with Michael test case ---\n${test.test_code || ""}`;
                const payload = await this.executeCode(code, 12000);
                const formatted = this.formatResult(payload);
                const expected = (test.expected_output || "").trim();
                const observed = formatted.message.trim();
                const passed = !formatted.isError && (!expected || observed === expected);
                if (passed) this.lastTestsPassed += 1;
                this.lastTestResults.push({
                    id: test.id,
                    name: test.name || `Test ${index + 1}`,
                    passed,
                    expected: test.expected_output || "",
                    observed: formatted.message,
                    error: formatted.isError,
                });
                if (formatted.isError) break;
            }

            this.lastPassed = this.lastTestsPassed === this.lastTestsTotal;
            const lines = this.lastTestResults.map((result, index) => {
                const icon = result.passed ? "✅" : "❌";
                const details = result.passed ? "passed" : `failed\nObserved:\n${result.observed}${result.expected ? `\nExpected:\n${result.expected}` : ""}`;
                return `${icon} ${index + 1}. ${result.name} ${details}`;
            });
            const summary = `${this.lastTestsPassed}/${this.lastTestsTotal} tests passed.`;
            this.lastOutput = `${summary}\n\n${lines.join("\n\n")}`;
            this.output.textContent = this.lastOutput;
            this.output.classList.toggle("has-error", !this.lastPassed);
            this.output.classList.toggle("is-match", this.lastPassed);
            this.setBusy(false);
            if (this.saveButton) this.saveButton.disabled = false;
        }

        stop(message, isError = false) {
            if (this.pendingId === null) return;
            this.destroyWorker();
            this.resolvePending({ status: "error", error: message });
            this.finishStopped(message, isError);
        }

        finishStopped(message, isError = false) {
            this.lastOutput = message;
            this.output.textContent = message;
            this.output.classList.toggle("has-error", isError);
            this.output.classList.remove("is-match");
            this.setBusy(false);
        }

        reset() {
            if (this.pendingId !== null) this.stop("Execution stopped and code reset.");
            this.editor.value = this.originalCode;
            this.output.textContent = "Select Run code or press Ctrl+Enter.";
            this.output.classList.remove("has-error", "is-match");
            this.lastOutput = "";
            this.lastPassed = false;
            this.lastTestResults = [];
            this.lastTestsPassed = 0;
            this.lastTestsTotal = 0;
            if (this.saveButton) this.saveButton.disabled = true;
        }

        getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(";").shift();
            return "";
        }

        async saveAttempt() {
            const url = this.element.dataset.challengeSubmitUrl;
            if (!url || !this.saveButton) return;
            this.saveButton.disabled = true;
            const originalLabel = this.saveButton.textContent;
            this.saveButton.textContent = "Saving…";
            try {
                const body = new URLSearchParams({
                    submitted_code: this.editor.value,
                    observed_output: this.lastOutput,
                    passed: String(this.lastPassed),
                    test_results: JSON.stringify(this.lastTestResults),
                    tests_passed: String(this.lastTestsPassed),
                    tests_total: String(this.lastTestsTotal),
                });
                const response = await fetch(url, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "X-CSRFToken": this.getCookie("csrftoken"),
                    },
                    body,
                });
                if (response.ok) {
                    const payload = await response.json();
                    this.output.textContent = `${this.lastOutput}\n\n${payload.feedback} Saved to your progress.`;
                    this.saveButton.textContent = "Saved";
                    return;
                }
                throw new Error("Save failed");
            } catch (error) {
                this.output.textContent = `${this.lastOutput}\n\nAttempt could not be saved. Log in again and retry.`;
                this.saveButton.disabled = false;
                this.saveButton.textContent = originalLabel;
            }
        }

        destroyWorker() {
            if (this.worker) this.worker.terminate();
            this.worker = null;
        }
    }

    document.querySelectorAll("[data-python-playground]").forEach(
        (element) => new PythonPlayground(element),
    );
})();
