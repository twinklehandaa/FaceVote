const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const captureButton = document.getElementById('capture');
const verificationResult = document.getElementById('verification-result');

let registeredFaces = [];

Promise.all([
    faceapi.nets.tinyFaceDetector.loadFromUri('/static/models'),
    faceapi.nets.faceLandmark68Net.loadFromUri('/static/models'),
    faceapi.nets.faceRecognitionNet.loadFromUri('/static/models'),
]).then(startVideo).then(loadRegisteredFaces);

function startVideo() {
    navigator.mediaDevices.getUserMedia({ video: {} })
        .then(stream => video.srcObject = stream)
        .catch(console.error);
}

async function loadRegisteredFaces() {
    try {
        const response = await fetch('/get_registered_faces');
        const data = await response.json();

        registeredFaces = data.map(face => ({
            name: face.name,
            descriptors: face.descriptors.map(descriptor => new Float32Array(descriptor))
        }));

    } catch (error) {
        console.error('Error loading registered faces:', error);
        verificationResult.textContent = 'Error loading registered faces.';
    }
}

captureButton.addEventListener('click', async () => {
    const displaySize = { width: video.width, height: video.height };
    faceapi.matchDimensions(canvas, displaySize);
    const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions()).withFaceLandmarks().withFaceDescriptors();

    if (detections.length === 0) {
        verificationResult.textContent = 'No face detected.';
        return;
    }

    const resizedDetections = faceapi.resizeResults(detections, displaySize);
    faceapi.draw.drawDetections(canvas, resizedDetections);
    faceapi.draw.drawFaceLandmarks(canvas, resizedDetections);

    const capturedDescriptor = resizedDetections[0].descriptor;

    if (registeredFaces.length === 0) {
        verificationResult.textContent = 'No registered faces found.';
        return;
    }

    let bestMatch = null;
    let minDistance = Infinity;

    registeredFaces.forEach(registeredFace => {
        if (registeredFace.descriptors && registeredFace.descriptors.length > 0) {
            registeredFace.descriptors.forEach(registeredDescriptor => {
                const distance = faceapi.euclideanDistance(capturedDescriptor, registeredDescriptor);
                if (distance < minDistance) {
                    minDistance = distance;
                    bestMatch = registeredFace.name;
                }
            });
        }
    });

    const recognitionThreshold = 0.6;

    if (bestMatch && minDistance < recognitionThreshold) {
        verificationResult.textContent = `Face verified. Matched with ${bestMatch}.`;
    } else {
        verificationResult.textContent = 'Face not recognized.';
    }
});