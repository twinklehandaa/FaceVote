function uploadImage(endpoint) {
    let fileInput = document.getElementById("imageUpload").files[0];
    let formData = new FormData();
    formData.append("image", fileInput);

    let nameInput = document.getElementById("name");
    if (nameInput && endpoint === '/register') {
        formData.append("name", nameInput.value);
    }

    fetch(endpoint, { method: "POST", body: formData })
        .then(response => response.json()) // Parse the JSON response
        .then(data => {
            let resultElement = document.getElementById("result");
            if (resultElement) {
                resultElement.textContent = data.message; // Access the message property
            } else {
                alert(data.message);
            }
        })
        .catch(error => console.error("Error:", error));
}


const verifyButton = document.getElementById('verifyButton');
const videoFeed = document.getElementById('videoFeed');
const verificationResult = document.getElementById('verification-result');

verifyButton.addEventListener('click', () => {
    videoFeed.style.display = 'block'; // Show the video feed
    verifyButton.style.display = 'none'; // hide the button
    videoFeed.src = '/video_feed'; 

    // You can add face recognition logic here if needed.
    // However, the current Flask app.py only streams the video, it doesn't do recognition.
    // If you want recognition, you'll need to modify app.py to include that.

    // Example (placeholder):
    verificationResult.textContent = 'Webcam opened. Face recognition logic needs implementation on the server side.';

    // If you want to capture a frame and send it to the server for processing, you can do something like this:
    // (This requires modifications to app.py to receive and process the image.)

    // setTimeout(() => { // Capture a frame after a delay (e.g., 3 seconds)
    //     const canvas = document.createElement('canvas');
    //     const context = canvas.getContext('2d');
    //     canvas.width = videoFeed.videoWidth; // Use the video's actual dimensions
    //     canvas.height = videoFeed.videoHeight;
    //     context.drawImage(videoFeed, 0, 0, canvas.width, canvas.height); // Draw the current video frame onto the canvas
    //     const imageDataURL = canvas.toDataURL('image/jpeg'); // Get the image data as a data URL
    //
    //     fetch('/process_image', { // Create a Flask route named /process_image
    //         method: 'POST',
    //         headers: { 'Content-Type': 'application/json' },
    //         body: JSON.stringify({ image: imageDataURL }), // Send the image data to the server
    //     })
    //     .then(response => response.json())
    //     .then(data => {
    //         verificationResult.textContent = data.result; // Display the result from the server
    //     })
    //     .catch(error => {
    //         verificationResult.textContent = 'Error processing image.';
    //         console.error(error);
    //     });
    // }, 3000); // Delay of 3 seconds.
});

// Important Notes:
// 1.  The Flask app.py currently only streams the video feed.
// 2.  The JavaScript code above is a placeholder for face recognition.
// 3.  To perform actual face recognition, you'll need to:
//     * Modify app.py to include face recognition logic (e.g., using face_recognition or other libraries).
//     * Modify the JavaScript to capture a frame from the video feed and send it to the server.
//     * Create a Flask route to receive and process the image data.
//     * Display the results from the server in the verificationResult div.
// 4.  The setTimeout function is just for example, and could be replaced with an button to trigger the capture.