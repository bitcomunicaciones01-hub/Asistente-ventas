document.addEventListener('DOMContentLoaded', () => {
    const chatButton = document.getElementById('chat-button');
    const chatWindow = document.getElementById('chat-window');
    const closeChat = document.getElementById('close-chat');
    const sendBtn = document.getElementById('send-btn');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');

    // Toggle Chat Window
    chatButton.addEventListener('click', () => {
        chatWindow.classList.remove('hidden');
        chatButton.style.display = 'none';
        userInput.focus();
    });

    closeChat.addEventListener('click', () => {
        chatWindow.classList.add('hidden');
        chatButton.style.display = 'flex';
    });

    // Send Message
    const sendMessage = async () => {
        const text = userInput.value.trim();
        if (!text) return;

        // User Message UI
        appendMessage('user', text);
        userInput.value = '';

        // Bot Thinking indicator
        const typingId = appendMessage('bot', '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>', true);

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, context: 'tienda' })
            });

            const data = await response.json();
            
            // Remove typing indicator
            document.getElementById(typingId).remove();

            // Bot Message UI
            let botText = data.text;
            // Si hay productos, nos aseguramos de que el texto no ensucie la pantalla
            // y deje que la grilla horizontal sea la protagonista.
            if (data.products && data.products.length > 0) {
                botText = "¡Excelente! He encontrado estas opciones para ti:";
            }
            appendMessage('bot', botText);

            // Render Products if available
            if (data.products && data.products.length > 0) {
                renderProducts(data.products);
            }

        } catch (error) {
            console.error('Error:', error);
            document.getElementById(typingId).innerHTML = 'Lo siento, hubo un error conectando con el asistente.';
        }
    };

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
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
            // Usando el motor de Marked para que todos los links [link](url)
            // y fotos ![foto](url) se vuelvan clickeables automáticamente
            msgDiv.innerHTML = marked.parse(content);

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
        
        chatMessages.appendChild(msgDiv);
        
        // Scroll inmediato
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
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
        
        chatMessages.appendChild(carousel);
        
        // Scroll suave al final
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 150);
    }
});
