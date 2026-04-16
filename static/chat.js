const initChat = () => {
    // Polling de elementos críticos
    const getElements = () => ({
        chatButton: document.getElementById('chat-button'),
        chatWindow: document.getElementById('chat-window'),
        closeChat: document.getElementById('close-chat'),
        sendBtn: document.getElementById('send-btn'),
        micBtn: document.getElementById('mic-btn'),
        userInput: document.getElementById('user-input'),
        chatMessages: document.getElementById('chat-messages')
    });

    let els = getElements();
    // VERIFICACIÓN CRÍTICA: Si falta alguno, no iniciamos nada para evitar errores
    if (!els.chatButton || !els.chatWindow || !els.sendBtn || !els.userInput || !els.chatMessages) {
        return;
    }

    // BASE URL de Railway (Si no está definida, usa local)
    const baseUrl = window.RAILWAY_URL || "";

    // CARGA DE LOGO DINÁMICO
    const botLogo = document.getElementById('bot-logo');
    if (botLogo) {
        botLogo.src = `${baseUrl}/static/logo.png`;
    }

    const bubbleLogo = document.getElementById('bubble-logo');
    if (bubbleLogo) {
        bubbleLogo.src = `${baseUrl}/static/logo.png`;
    }

    // Toggle Chat Window
    els.chatButton.addEventListener('click', () => {
        els = getElements(); // Refrescamos por si acaso
        els.chatWindow.classList.remove('hidden');
        els.chatButton.style.display = 'none';
        if (els.userInput) els.userInput.focus();
    });

    if (els.closeChat) {
        els.closeChat.addEventListener('click', () => {
            els.chatWindow.classList.add('hidden');
            els.chatButton.style.display = 'flex';
        });
    }

    // Audio Recording Logic v14.0
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;

    if (els.micBtn) {
        els.micBtn.addEventListener('click', async () => {
            els = getElements();
            if (!isRecording) {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];

                    mediaRecorder.ondataavailable = e => {
                        if (e.data.size > 0) audioChunks.push(e.data);
                    };

                    mediaRecorder.onstop = async () => {
                        let ext = 'webm';
                        if (mediaRecorder.mimeType.includes('mp4')) ext = 'm4a';
                        if (mediaRecorder.mimeType.includes('ogg')) ext = 'ogg';
                        const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
                        sendAudioMessage(audioBlob, ext);
                    };

                    mediaRecorder.start();
                    isRecording = true;
                    els.micBtn.style.backgroundColor = 'rgba(255, 60, 60, 0.8)';
                    els.micBtn.innerHTML = '🛑';
                    els.userInput.disabled = true;
                    els.userInput.placeholder = "Grabando nota de voz...";

                } catch (err) {
                    console.error("Error al acceder al micrófono:", err);
                    alert("Por favor habilita el acceso al micrófono en tu navegador para enviar audios.");
                }
            } else {
                // Parar grabación
                mediaRecorder.stop();
                isRecording = false;
                els.micBtn.style.backgroundColor = 'transparent';
                els.micBtn.innerHTML = '🎤';
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
                els.userInput.disabled = false;
                els.userInput.placeholder = "Procesando audio...";
            }
        });
    }

    const sendAudioMessage = async (audioBlob, ext = 'webm') => {
        try {
            els = getElements();
            const formData = new FormData();
            formData.append('audio', audioBlob, `voice.${ext}`);
            formData.append('context', 'tienda');

            // Renderizar un spinner mientras procesa (simula un mensaje de bot)
            const typingId = appendMessage('bot', '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>', true);

            const response = await fetch(`${baseUrl}/chat/audio`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            // Eliminar spinner
            const typingEl = document.getElementById(typingId);
            if (typingEl) typingEl.remove();

            // Mostramos lo que escuchó Whisper como si fuera un mensaje del usuario
            if (data.recognized_text) {
                appendMessage('user', '🎙️ ' + data.recognized_text);
            }

            // Renderizar la respuesta bot (Texto y productos)
            let botText = data.text;
            if (data.products && data.products.length > 0) {
                botText = "¡Excelente! He encontrado estas opciones para ti:";
            }
            appendMessage('bot', botText);

            if (data.products && data.products.length > 0) {
                renderProducts(data.products);
            }
            
            els.userInput.placeholder = "Pregúntame algo...";
        } catch (err) {
            console.error('Error enviando nota de voz:', err);
            els.userInput.placeholder = "Pregúntame algo...";
            alert("Error de conexión al procesar el audio.");
        }
    };

    // Send Message (Text o Detener Audio)
    const sendMessage = async () => {
        if (isRecording) {
            // El usuario apretó la flecha mientras grababa. Detenemos y mandamos el audio.
            els.micBtn.click();
            return;
        }

        try {
            els = getElements();
            const text = els.userInput.value.trim();
            if (!text) return;

            // User Message UI
            appendMessage('user', text);
            els.userInput.value = '';

            // Bot Thinking indicator
            const typingId = appendMessage('bot', '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>', true);

            try {
                const response = await fetch(`${baseUrl}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text, context: 'tienda' })
                });

                const data = await response.json();
                
                // Remove typing indicator
                const typingEl = document.getElementById(typingId);
                if (typingEl) typingEl.remove();

                // Bot Message UI
                let botText = data.text;
                if (data.products && data.products.length > 0) {
                    botText = "¡Excelente! He encontrado estas opciones para ti:";
                }
                appendMessage('bot', botText);

                // Render Products if available
                if (data.products && data.products.length > 0) {
                    renderProducts(data.products);
                }

            } catch (innerError) {
                console.error('❌ Error de conexión con Railway:', innerError);
                const typingEl = document.getElementById(typingId);
                if (typingEl) typingEl.innerHTML = 'Lo siento, hubo un error conectando con el asistente. Verificá tu conexión o si el servidor de Railway está activo.';
            }
        } catch (outerError) {
            console.error('❌ Error fatal en el widget:', outerError);
            alert("El asistente de ventas encontró un error interno. Por favor recarga la página.");
        }
    };

    els.sendBtn.addEventListener('click', sendMessage);
    els.userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    function appendMessage(role, content, isHtml = false) {
        const id = 'msg-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        msgDiv.id = id;
        
        if (isHtml) {
            msgDiv.innerHTML = content;
        } else {
            // SEGURIDAD: Si la librería 'marked' falla o no carga, usamos el texto normal
            if (typeof marked !== 'undefined' && typeof marked.parse === 'function') {
                msgDiv.innerHTML = marked.parse(content);
            } else {
                console.warn("⚠️ [DEBUG] Librería 'marked' no disponible. Usando texto plano.");
                msgDiv.textContent = content;
            }

            // Aseguramos que todas las imágenes en el texto también sean links clickeables
            const images = msgDiv.querySelectorAll('img');
            images.forEach(img => {
                const src = img.getAttribute('src');
                if (src) {
                    const link = document.createElement('a');
                    link.href = src;
                    link.target = '_blank';
                    img.parentNode.insertBefore(link, img);
                    link.appendChild(img);
                }
            });

            // Convertir links de WhatsApp y Productos en botones reales
            const links = msgDiv.querySelectorAll('a');
            links.forEach(a => {
                const href = a.href;
                if (href.includes('wa.me')) {
                    a.className = 'whatsapp-btn';
                    a.innerHTML = `<span>💬 Hablar con un experto</span>`;
                } else if (href.includes('bitcomunicaciones.com/producto')) {
                    // Si el bot escribe un link de producto en el texto, lo convertimos en botón
                    a.className = 'buy-link';
                    a.style.display = 'block';
                    a.style.marginTop = '10px';
                    a.style.textAlign = 'center';
                    a.innerHTML = 'COMPRAR AHORA';
                }
            });
        }
        
        els.chatMessages.appendChild(msgDiv);
        
        // Scroll inmediato
        els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
        
        return id;
    }

    function renderProducts(products) {
        const carousel = document.createElement('div');
        carousel.className = 'catalog-carousel';
        
        products.forEach(p => {
            const card = document.createElement('div');
            card.className = 'product-card';
            
            const img = p.images && p.images.length > 0 ? p.images[0] : 'https://via.placeholder.com/150?text=No+Image';
            
            // La imagen h4 y el botón ahora redireccionan directamente a la página del producto
            card.innerHTML = `
                <a href="${p.permalink}" target="_blank" style="text-decoration: none; color: inherit; display: block;">
                    <img src="${img}" alt="${p.name}">
                    <h4>${p.name}</h4>
                    <p class="price">$${p.price}</p>
                </a>
                <a href="${p.permalink}" target="_blank" class="buy-link">COMPRAR AHORA</a>
            `;
            carousel.appendChild(card);
        });
        
        els.chatMessages.appendChild(carousel);
        
        // Scroll suave al final
        setTimeout(() => {
            els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
        }, 150);
    }
};

// Polling: Intentar iniciar el chat cada 100ms hasta que los elementos aparezcan
let initAttempts = 0;
const pollInit = setInterval(() => {
    const el = document.getElementById('chat-button');
    if (el) {
        initChat();
        clearInterval(pollInit);
    }
    initAttempts++;
    if (initAttempts > 50) { // Tras 5 segundos nos rendimos
        clearInterval(pollInit);
    }
}, 100);

// También intentamos por si el DOM ya estaba listo
document.addEventListener('DOMContentLoaded', initChat);
