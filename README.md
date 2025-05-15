# FaceVote
FaceVote is an innovative voting system that integrates facial recognition technology to authenticate 
voters before they cast their votes

The primary objective of FaceVote is to develop a reliable, secure, and efficient voting system that: 
* Authenticates voters using facial recognition technology.
* Matches the voter's face with pre-registered voter ID data.
* Prevents duplicate voting or impersonation attempts.
* Streamlines the voting process for ease of use.

## System Implementation: 
### Backend: 
* A server-side application built using a framework called Flask  
* A database management system (DBMS) such as sqlite3 for storing voter data, election 
information, and vote records. 
* A facial recognition library, OpenCV (Open Source Computer Vision Library) for face 
detection and feature extraction. 
### Frontend: 
* A web application developed using HTML, CSS, and JavaScript. 
* Libraries for handling form submissions, data display, and communication with the 
backend. 
### Facial Recognition Module Implementation: 
* Implementation of face detection algorithms to locate faces in images/video frames. 
* Implementation of feature extraction techniques to obtain unique facial features. 
* Implementation of face comparison algorithms to match captured faces with registered 
faces. 
