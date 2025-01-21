# dvr_iframe.py

dvr_html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>YOLO & Pose Detection Streams - Vista DVR</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #1D1F21;
            font-family: Arial, sans-serif;
            color: #fff;
            display: flex;
            flex-direction: row;
            height: 100vh;
        }
        /* Sidebar */
        .sidebar {
            width: 280px;
            background-color: #2E2E2E;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 15px;
        }
        .sidebar h2 {
            margin-bottom: 20px;
        }
        .controls {
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
        }
        .controls button {
            background-color: #007bff;
            border: none;
            color: white;
            font-size: 16px;
            padding: 8px 15px;
            cursor: pointer;
            border-radius: 5px;
        }
        .controls button:hover {
            background-color: #0056b3;
        }
        .sidebar button#viewAllBtn {
            width: 100%;
            padding: 12px;
            margin-bottom: 20px;
            background-color: #28a745; /* Verde */
            border: none;
            color: white;
            font-size: 16px;
            cursor: pointer;
            border-radius: 5px;
        }
        .sidebar button#viewAllBtn:hover {
            background-color: #218838;
        }
        .camera-list {
            width: 100%;
        }
        .camera-item {
            background-color: #3A3A3A;
            padding: 10px;
            margin-bottom: 10px;
            cursor: pointer;
            text-align: center;
            border-radius: 5px;
        }
        .camera-item:hover {
            background-color: #4A4A4A;
        }
        .mini-thumb {
            display: block;
            margin: 0 auto 5px auto; 
            border: 1px solid #000;
            width: 120px; 
            height: 90px; 
        }

        /* Main view */
        .main-view {
            flex: 1;
            background-color: #1D1F21;
            display: flex;
            flex-direction: row;
            flex-wrap: nowrap; /* Para mantenerlas en una fila */
            justify-content: center;
            align-items: center;
            position: relative;
        }
        /* En modo "Ver Todo" */
        .multi-camera .camera-view {
            width: 32%;
            margin: 5px;
            box-sizing: border-box;
            border: 1px solid #444;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
        }
        /* En modo "una sola cámara" */
        .single-camera .camera-view {
            width: 95%;
            height: 90%;
            margin: 0 auto;
            border: 1px solid #444;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
        }
        .camera-title {
            background-color: #333;
            width: 100%;
            text-align: center;
            padding: 5px;
            font-weight: bold;
        }
        canvas {
            max-width: 100%;
            max-height: calc(100% - 30px);
        }
        /* Ocultar cámaras */
        .hidden {
            display: none !important;
        }

    </style>
</head>
<body>
    <div class="sidebar">
        <h2>Lista de Cámaras</h2>

        <!-- Controles con flechas -->
        <div class="controls">
            <button id="prevCameraBtn">&#8592;</button>
            <button id="nextCameraBtn">&#8594;</button>
        </div>

        <!-- Botón para ver todas las cámaras -->
        <button id="viewAllBtn">Ver Todo</button>

        <div class="camera-list">
            <div class="camera-item" onclick="showSingleCamera('poseContainer')">
                <!-- Miniatura de la cámara de Poses -->
                <canvas id="poseThumbCanvas" class="mini-thumb"></canvas>
                <span>Cámara Poses</span>
            </div>
            <div class="camera-item" onclick="showSingleCamera('objectContainer')">
                <!-- Miniatura de la cámara de Objetos -->
                <canvas id="objectThumbCanvas" class="mini-thumb"></canvas>
                <span>Cámara Objetos</span>
            </div>
            <div class="camera-item" onclick="showSingleCamera('faceContainer')">
                <!-- Miniatura de la cámara de Rostros -->
                <canvas id="faceThumbCanvas" class="mini-thumb"></canvas>
                <span>Cámara Rostros</span>
            </div>
        </div>
    </div>

    <div class="main-view multi-camera" id="mainView">
        <!-- Cámara de Poses -->
        <div class="camera-view" id="poseContainer">
            <div class="camera-title">Detección de Poses</div>
            <canvas id="poseCanvas"></canvas>
        </div>
        <!-- Cámara de Objetos -->
        <div class="camera-view" id="objectContainer">
            <div class="camera-title">Detección de Objetos</div>
            <canvas id="objectCanvas"></canvas>
        </div>
        <!-- Cámara de Rostros -->
        <div class="camera-view" id="faceContainer">
            <div class="camera-title">Detección de Rostros</div>
            <canvas id="faceCanvas"></canvas>
        </div>
    </div>

    <script>
        // ----- WebSocket Initialization for main view -----
        function initWebSocket(canvasId, websocketUrl) {
            const canvas = document.getElementById(canvasId);
            const ctx = canvas.getContext("2d");
            const socket = new WebSocket(websocketUrl);
            const image = new Image();

            socket.binaryType = "arraybuffer";
            socket.onmessage = (event) => {
                const blob = new Blob([event.data], { type: "image/jpeg" });
                const url = URL.createObjectURL(blob);
                image.onload = () => {
                    canvas.width = image.width;
                    canvas.height = image.height;
                    ctx.drawImage(image, 0, 0);
                    URL.revokeObjectURL(url);
                };
                image.src = url;
            };
            socket.onerror = (error) => {
                console.error(`Error en el WebSocket (${websocketUrl}):`, error);
            };
            socket.onclose = () => {
                console.log(`Conexión WebSocket cerrada (${websocketUrl})`);
            };
        }

        // ----- WebSocket Initialization for thumbnails -----
        function initWebSocketThumb(canvasId, websocketUrl) {
            const canvas = document.getElementById(canvasId);
            const ctx = canvas.getContext("2d");
            const socket = new WebSocket(websocketUrl);
            const image = new Image();

            socket.binaryType = "arraybuffer";
            socket.onmessage = (event) => {
                const blob = new Blob([event.data], { type: "image/jpeg" });
                const url = URL.createObjectURL(blob);
                image.onload = () => {
                    // Ajustamos el tamaño del lienzo al tamaño de la miniatura
                    canvas.width = 120; 
                    canvas.height = 90; 
                    // Dibuja la imagen ajustada a la miniatura
                    ctx.drawImage(image, 0, 0, 120, 90);
                    URL.revokeObjectURL(url);
                };
                image.src = url;
            };
            socket.onerror = (error) => {
                console.error(`Error en WebSocket THUMB (${websocketUrl}):`, error);
            };
            socket.onclose = () => {
                console.log(`Conexión WebSocket cerrada (THUMB) (${websocketUrl})`);
            };
        }

        // Inicializar WebSockets para vistas principales
        initWebSocket("poseCanvas", "ws://localhost:8000/ws/poses");
        initWebSocket("objectCanvas", "ws://localhost:8000/ws/objects");
        initWebSocket("faceCanvas", "ws://localhost:8000/ws/faces");

        // Inicializar WebSockets para miniaturas
        initWebSocketThumb("poseThumbCanvas", "ws://localhost:8000/ws/poses");
        initWebSocketThumb("objectThumbCanvas", "ws://localhost:8000/ws/objects");
        initWebSocketThumb("faceThumbCanvas", "ws://localhost:8000/ws/faces");

        // ----- IDs de cámaras principales -----
        const cameras = ["poseContainer", "objectContainer", "faceContainer"];
        let currentIndex = 0;

        const mainView = document.getElementById("mainView");

        // Mostrar todas las cámaras en modo horizontal
        function showAllCameras() {
            mainView.classList.add("multi-camera");
            mainView.classList.remove("single-camera");

            // Mostramos todas las cámaras
            cameras.forEach((camId) => {
                document.getElementById(camId).classList.remove("hidden");
            });
        }

        // Mostrar cámara única en fullscreen
        function showSingleCamera(containerId) {
            mainView.classList.remove("multi-camera");
            mainView.classList.add("single-camera");

            // Ocultamos todas menos la seleccionada
            cameras.forEach((camId) => {
                document.getElementById(camId).classList.add("hidden");
            });
            document.getElementById(containerId).classList.remove("hidden");

            // Actualizamos el currentIndex
            currentIndex = cameras.indexOf(containerId);
        }

        // Botón "Ver Todo"
        document.getElementById("viewAllBtn").addEventListener("click", () => {
            showAllCameras();
        });

        // Botones de navegación (flechas)
        document.getElementById("prevCameraBtn").addEventListener("click", () => {
            // Si estamos en single-camera, vamos a la anterior
            if (mainView.classList.contains("single-camera")) {
                currentIndex = (currentIndex - 1 + cameras.length) % cameras.length;
                showSingleCamera(cameras[currentIndex]);
            }
        });

        document.getElementById("nextCameraBtn").addEventListener("click", () => {
            // Si estamos en single-camera, vamos a la siguiente
            if (mainView.classList.contains("single-camera")) {
                currentIndex = (currentIndex + 1) % cameras.length;
                showSingleCamera(cameras[currentIndex]);
            }
        });

        // Tecla flecha derecha e izquierda
        document.addEventListener("keydown", (event) => {
            // Para que funcione, debes hacer clic dentro del iframe y luego presionar la tecla
            if (mainView.classList.contains("single-camera")) {
                if (event.key === "ArrowRight") {
                    // siguiente
                    currentIndex = (currentIndex + 1) % cameras.length;
                    showSingleCamera(cameras[currentIndex]);
                }
                else if (event.key === "ArrowLeft") {
                    // anterior
                    currentIndex = (currentIndex - 1 + cameras.length) % cameras.length;
                    showSingleCamera(cameras[currentIndex]);
                }
            }
        });
    </script>
</body>
</html>
"""
