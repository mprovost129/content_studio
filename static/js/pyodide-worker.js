import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v314.0.2/full/pyodide.mjs";

const pyodideReady = loadPyodide();

self.onmessage = async (event) => {
    const { id, code } = event.data;
    try {
        const pyodide = await pyodideReady;
        await pyodide.loadPackagesFromImports(code);
        self.postMessage({ id, status: "running" });

        const stdout = [];
        const stderr = [];
        pyodide.setStdout({ batched: (message) => stdout.push(message) });
        pyodide.setStderr({ batched: (message) => stderr.push(message) });

        const result = await pyodide.runPythonAsync(code);
        let expressionResult = "";
        if (result !== undefined && result !== null) {
            expressionResult = String(result);
            if (typeof result.destroy === "function") {
                result.destroy();
            }
        }
        self.postMessage({
            id,
            status: "complete",
            stdout: stdout.join("\n"),
            stderr: stderr.join("\n"),
            result: expressionResult,
        });
    } catch (error) {
        self.postMessage({
            id,
            status: "error",
            error: error instanceof Error ? error.message : String(error),
        });
    }
};
