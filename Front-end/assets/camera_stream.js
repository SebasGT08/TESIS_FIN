window.onload = function() {
    const checkCanvas = setInterval(() => {
        const canvas = document.getElementById("videoCanvas");
        if (canvas) {
            clearInterval(checkCanvas);
            const ctx = canvas.getContext("2d");
            const socket = new WebSocket("ws://localhost:8000/ws/video");
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
                console.error("Error en el WebSocket:", error);
            };

            socket.onclose = () => {
                console.log("Conexión WebSocket cerrada");
            };
        } else {
            console.log("Esperando a que el canvas esté disponible en el DOM...");
        }
    }, 500);
};
