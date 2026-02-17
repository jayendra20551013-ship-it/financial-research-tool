async function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const statusDiv = document.getElementById("status");

    if (fileInput.files.length === 0) {
        alert("Please select at least one PDF file.");
        return;
    }

    statusDiv.innerHTML = "Processing... Please wait ⏳";

    const formData = new FormData();

    // IMPORTANT: field name must be "files"
    for (let i = 0; i < fileInput.files.length; i++) {
        formData.append("files", fileInput.files[i]);
    }

    try {
        const response = await fetch("https://financial-research-tool-ruyt.onrender.com/extract", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Server error: " + response.status);
        }

        const result = await response.json();

        console.log(result);

        statusDiv.innerHTML = `
            <p style="color:green;">Extraction Completed ✅</p>
            <p>Saved File: ${result.file_saved_as}</p>
        `;

    } catch (error) {
        console.error(error);
        statusDiv.innerHTML = `
            <p style="color:red;">Error occurred ❌</p>
            <p>${error.message}</p>
        `;
    }
}
