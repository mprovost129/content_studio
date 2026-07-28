(() => {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(";").shift();
        return "";
    }

    document.querySelectorAll("[data-quiz-card]").forEach((card) => {
        const feedback = card.querySelector("[data-quiz-feedback]");
        card.querySelectorAll("[data-quiz-choice]").forEach((button) => {
            button.addEventListener("click", async () => {
                const isCorrect = button.dataset.correct === "true";
                card.querySelectorAll("[data-quiz-choice]").forEach((choice) => {
                    choice.classList.remove("is-selected", "is-correct", "is-incorrect");
                    if (choice.dataset.correct === "true") choice.classList.add("is-correct");
                });
                button.classList.add("is-selected", isCorrect ? "is-correct" : "is-incorrect");
                let message = isCorrect ? "Correct. Nice work." : "Not quite. Review the choices and try again.";

                if (card.dataset.submitUrl && button.dataset.choiceId) {
                    try {
                        const body = new URLSearchParams({ choice_id: button.dataset.choiceId });
                        const response = await fetch(card.dataset.submitUrl, {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/x-www-form-urlencoded",
                                "X-CSRFToken": getCookie("csrftoken"),
                            },
                            body,
                        });
                        if (response.ok) {
                            const payload = await response.json();
                            message = `${payload.feedback} Saved to your progress.`;
                        }
                    } catch (error) {
                        message += " Your browser could not save this attempt.";
                    }
                }

                if (feedback) {
                    feedback.textContent = message;
                    feedback.classList.toggle("is-correct", isCorrect);
                    feedback.classList.toggle("is-incorrect", !isCorrect);
                }
            });
        });
    });
})();
