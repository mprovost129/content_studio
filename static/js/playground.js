(() => {
    const workerUrl = document.body.dataset.pythonWorker;
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
            this.originalCode = this.editor.value;
            this.worker = null;
            this.timeout = null;
            this.pendingId = null;

            this.runButton.addEventListener("click", () => this.run());
            this.stopButton.addEventListener("click", () => this.stop("Execution stopped."));
            this.resetButton.addEventListener("click", () => this.reset());
            this.editor.addEventListener("keydown", (event) => {
                if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                    event.preventDefault();
                    this.run();
                }
            });
        }

        ensureWorker() {
            if (this.worker) return;
            this.worker = new Worker(workerUrl, { type: "module" });
            this.worker.addEventListener("message", (event) => this.receive(event));
            this.worker.addEventListener("error", () => {
                this.finish("The Python runtime could not load. Check your internet connection.", true);
                this.destroyWorker();
            });
        }

        run() {
            if (this.pendingId !== null) return;
            this.ensureWorker();
            this.pendingId = ++requestNumber;
            this.output.textContent = "Loading Python and running your code…";
            this.output.classList.remove("has-error");
            this.runButton.disabled = true;
            this.stopButton.disabled = false;
            this.element.classList.add("is-running");
            this.worker.postMessage({ id: this.pendingId, code: this.editor.value });
            this.timeout = window.setTimeout(() => {
                this.stop("The Python runtime could not load within 60 seconds.", true);
            }, 60000);
        }

        receive(event) {
            if (event.data.id !== this.pendingId) return;
            const { status, stdout, stderr, result, error } = event.data;
            if (status === "running") {
                window.clearTimeout(this.timeout);
                this.output.textContent = "Running…";
                this.timeout = window.setTimeout(() => {
                    this.stop("Execution stopped after 12 seconds. Check for an infinite loop.", true);
                }, 12000);
                return;
            }
            if (status === "error") {
                this.finish(error || "Python returned an unknown error.", true);
                return;
            }
            const parts = [stdout, stderr, result].filter(Boolean);
            this.finish(parts.join("\n") || "Code completed with no output.", Boolean(stderr));
        }

        finish(message, isError = false) {
            window.clearTimeout(this.timeout);
            this.timeout = null;
            this.pendingId = null;
            this.output.textContent = message;
            this.output.classList.toggle("has-error", isError);
            this.runButton.disabled = false;
            this.stopButton.disabled = true;
            this.element.classList.remove("is-running");
        }

        stop(message, isError = false) {
            if (this.pendingId === null) return;
            this.destroyWorker();
            this.finish(message, isError);
        }

        reset() {
            if (this.pendingId !== null) this.stop("Execution stopped and code reset.");
            this.editor.value = this.originalCode;
            this.output.textContent = "Select Run code or press Ctrl+Enter.";
            this.output.classList.remove("has-error");
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
