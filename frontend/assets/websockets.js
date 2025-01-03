// Función para inicializar un WebSocket y manejar el stream
function initWebSocket(canvasId, websocketUrl) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext("2d");
    const socket = new WebSocket(websocketUrl);
    const image = new Image();

    socket.binaryType = "arraybuffer"; // Recibir datos binarios
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
        console.error(`Error en WebSocket (${websocketUrl}):`, error);
    };

    socket.onclose = () => {
        console.log(`WebSocket cerrado (${websocketUrl})`);
    };
}

// Al cargar la página, inicializamos los 3 streams
document.addEventListener('DOMContentLoaded', () => {
    initWebSocket("poseCanvas", "ws://localhost:8000/ws/poses");
    initWebSocket("objectCanvas", "ws://localhost:8000/ws/objects");
    initWebSocket("faceCanvas", "ws://localhost:8000/ws/faces");
});
