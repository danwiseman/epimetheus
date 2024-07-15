/*
            
    Silence is golden.
    01001001 01000111 01101111 01110100 01001110 01101111 01110100 01101000 01101001 01101110 01100111 01110100 01101111 01001100 01101111 01110011 01100101
    
    Happy editing!

    
 * LexiStream - Easily Create a Chatbot Interface with OpenAI's GPT API
 *
 * Author: MeSilicon7
 * Version: 1.0.0-beta
 * Repository: https://github.com/MeSilicon7
 * License: No License
 *
 */

    class LexiStream {
        constructor(config) {
            this.config = config;
            this.box = document.querySelector(config.box);
            this.inputBox = document.querySelector(config.sendContent);
            this.inputSession = document.querySelector(config.sessionContent);
            this.startButton = document.querySelector(config.start);
            this.stopButton = document.querySelector(config.stop);
            this.customInputTag = config.customInputTag || 'div'; 
            this.customOutputTag = config.customOutputTag || 'lexi-mark'; 
            this.customErrorTag = config.customErrorTag || 'div'; 
            this.customLoadingTag = config.customLoadingTag || 'div'; 
            this.customLoadingMessage = config.customLoadingMessage || 'Processing...';
            this.eventSource = null;
            this.messageContainer = null;
            this.reportConnectionErrorMessage = config.reportConnectionErrorMessage || 'Failed to send message. Please try again later. Please check your internet connection.'; 
            this.streamingErrorMessage = config.streamingErrorMessage || 'Openai server is not responding. Please try again later.';  
            this.aiAvatarSource = config.aiAvatarSource || null;
            this.userAvatarSource = config.userAvatarSource || null;

            this.attachEventListeners();
        }
    
        attachEventListeners() {
            this.startButton.addEventListener('click', () => this.processInput());
            this.inputBox.addEventListener('keypress', e => {
                if (e.key === 'Enter') {
                    if (this.eventSource) {
                        e.preventDefault();
                    } else {
                        e.preventDefault();  
                        this.processInput();
                    }
                }
            });
            this.stopButton.addEventListener('click', () => this.stopStream());
        }
        
    
        processInput() {
            const message = this.inputBox.value.trim();
            const chat_session = this.inputSession.value.trim();
            if (message && chat_session) {
                this.sendMessage(message, chat_session);

                this.inputBox.value = '';
            }
        }
    
        startStream() {
            if (this.eventSource) {
                console.log('Stream is already active.');
                return;
            }
            console.log('streaming...')
        
            this.displayLoading(true);
        
            this.eventSource = new EventSource(this.config.listen + "?chat_session=" + this.inputSession.value.trim());
        
            this.eventSource.onmessage = event => {
                this.displayLoading(false);
                if (event.data.includes('finish_reason: stop')) {
                    this.stopStream();
                } else {
                    this.appendData(event.data);
                }
            };
        
            this.eventSource.onerror = () => {
                console.error('EventSource failed');
                this.displayError(this.streamingErrorMessage); 
                this.stopStream();
            };
        
            this.updateUI();
        }
    
        displayLoading(show) {

            if (!this.loadingElement) {
                this.loadingElement = document.createElement(this.customLoadingTag);
                this.loadingElement.classList.add('loading');
                this.loadingElement.innerHTML = this.customLoadingMessage;
                this.box.appendChild(this.loadingElement); 
            }
    
            // fix loading element not showing up after last message
            if (this.loadingElement) {
                this.loadingElement.remove();
                this.loadingElement = document.createElement(this.customLoadingTag);
                this.loadingElement.classList.add('loading');
                this.loadingElement.innerHTML = this.customLoadingMessage;
                this.box.appendChild(this.loadingElement);
            }
        
            this.loadingElement.style.display = show ? 'block' : 'none';
        }
        
        
    
    
        appendData(data) {
            if (!this.messageContainer) {

                this.messageContainer = document.createElement(this.customOutputTag);
                const rowElement = this.createChatElement(this.messageContainer, false, '')
                this.box.appendChild(rowElement);

            }
            this.messageContainer.textContent += data;
        }
        
        stopStream() {
            if (this.eventSource) {
                this.eventSource.close();
                this.eventSource = null;
                this.messageContainer = null;
            }
            this.updateUI();
            this.displayLoading(false); 
        }
    
        sendMessage(message, chat_session) {
            fetch(this.config.sendRequest, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, chat_session: chat_session })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('displaying now...' + message)
                    this.displayMessage({ text: message, user: true });
                    console.log('streaming...')
                    this.startStream();
                } else {
                    console.error('Message was not processed successfully:', data);
                }
            })
            .catch(error => {
                this.displayError(this.reportConnectionErrorMessage);
                console.error('Error sending message:', error);
            });
        }

        displayMessage({ text, user }) {
            const messageElement = document.createElement(this.customOutputTag);
            const rowElement = this.createChatElement(messageElement, user, text)
            console.log('created row')
            this.box.appendChild(rowElement);
        }
    
        displayError(text) {
            const messageElement = document.createElement(this.customErrorTag);
            messageElement.classList.add('error');
            messageElement.innerHTML = text;
            this.box.appendChild(messageElement);
        }
    
        animateText(text, element) {
            let i = 0;
            const speed = 10;
            const typeWriter = () => {
                if (i < text.length) {
                    element.textContent += text.charAt(i);
                    i++;
                    setTimeout(typeWriter, speed);
                }
            };
            typeWriter();
        }
    
        updateUI() {
            const isActive = !!this.eventSource;  
            this.startButton.disabled = isActive; 
            this.stopButton.disabled = !isActive;
        }

        createChatElement(messageElement, user, text) {
            // create row div
            const rowElement = document.createElement('div');
            rowElement.className = "row p-4";

            // create avatar and message column divs
            const colAvatar = document.createElement('div');
            colAvatar.className = "col-sm-2 col-md-2 align-self-center";
            const colMessage = document.createElement('div');
            colMessage.className = "col-sm-10 col-md-10";

            // create card elements for avatar and message
            const aiAvatarElement = document.createElement('img');
            aiAvatarElement.src = user ? this.userAvatarSource : this.aiAvatarSource;
            aiAvatarElement.className = user ? "user-avatar" : "ai-avatar rounded rounded-3 border";
            aiAvatarElement.alt = user ? "User" : "AI";

            const cardElementForMessage = document.createElement('div');
            cardElementForMessage.classList.add('card');

            const cardBodyForMessage = document.createElement('div');
            cardBodyForMessage.classList.add('card-body');

            // append avatar to column div, and card to body of message card
            colAvatar.appendChild(aiAvatarElement);
            cardElementForMessage.appendChild(cardBodyForMessage);

            // create the lexi-mark element for the message

            messageElement.classList.add(user ? 'user-message' : 'assistant-message');
            messageElement.textContent = text;  // or .innerHTML depending on your use case

            // append the lexi-mark to card body, and card to column div for messages
            cardBodyForMessage.appendChild(messageElement);
            colMessage.appendChild(cardElementForMessage);

            // finally, add columns (avatar and message) to row and add row to designated box
            rowElement.appendChild(colAvatar);
            rowElement.appendChild(colMessage);

            return rowElement;
        }


    }
    