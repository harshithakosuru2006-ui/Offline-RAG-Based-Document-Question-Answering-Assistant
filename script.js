const uploadForm =
    document.getElementById("uploadForm");

const fileInput =
    document.getElementById("fileInput");

const uploadStatus =
    document.getElementById("uploadStatus");

const askButton =
    document.getElementById("askButton");

const question =
    document.getElementById("question");

const answerBox =
    document.getElementById("answerBox");

const answer =
    document.getElementById("answer");

const sources =
    document.getElementById("sources");


// -----------------------------
// Upload PDF
// -----------------------------

uploadForm.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();


        if (!fileInput.files.length) {

            uploadStatus.textContent =
                "Please select a PDF.";

            return;
        }


        const formData =
            new FormData();


        formData.append(
            "file",
            fileInput.files[0]
        );


        uploadStatus.textContent =
            "Uploading and indexing document...";


        try {

            const response =
                await fetch(
                    "/upload",
                    {
                        method: "POST",
                        body: formData
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.error
                );
            }


            uploadStatus.textContent =
                `${data.message} ${data.chunks} text chunks indexed.`;


        } catch (error) {

            uploadStatus.textContent =
                error.message;
        }

    }
);


// -----------------------------
// Ask Question
// -----------------------------

askButton.addEventListener(
    "click",
    async function () {

        const userQuestion =
            question.value.trim();


        if (!userQuestion) {

            alert(
                "Please enter a question."
            );

            return;
        }


        askButton.disabled = true;

        askButton.textContent =
            "Thinking...";


        try {

            const response =
                await fetch(
                    "/ask",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            question:
                                userQuestion
                        })
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.error
                );
            }


            answer.textContent =
                data.answer;


            sources.innerHTML = "";


            data.sources.forEach(
                function (source) {

                    const listItem =
                        document.createElement(
                            "li"
                        );


                    listItem.textContent =
                        `${source.file} — Page ${source.page} — Similarity: ${source.score}`;


                    sources.appendChild(
                        listItem
                    );

                }
            );


            answerBox.classList.remove(
                "hidden"
            );


        } catch (error) {

            answer.textContent =
                error.message;

            sources.innerHTML = "";

            answerBox.classList.remove(
                "hidden"
            );


        } finally {

            askButton.disabled = false;

            askButton.textContent =
                "Ask Question";

        }

    }
);