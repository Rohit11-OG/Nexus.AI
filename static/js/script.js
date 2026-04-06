/**
 * NEXUS AIML Chatbot v4.0 — Frontend Script
 * Features: Sound effects, theme switcher, reactions, game UI, analytics, themed particles
 */

// ============ DOM ELEMENTS ============
const chatMessages = document.getElementById('chatMessages');
const chatContainer = document.getElementById('chatContainer');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const resetBtn = document.getElementById('resetBtn');
const charCount = document.getElementById('charCount');
const moodDisplay = document.getElementById('moodDisplay');
const patternCount = document.getElementById('patternCount');
const glitchOverlay = document.getElementById('glitchOverlay');
const quickBtns = document.querySelectorAll('.quick-btn');
const soundToggle = document.getElementById('soundToggle');
const reactionPicker = document.getElementById('reactionPicker');
const themeBtns = document.querySelectorAll('.theme-btn');

let isProcessing = false;
let messageCount = 0;
let currentMood = 'unknown';
let soundEnabled = true;
let currentTheme = 'cyberpunk';
let activeGameType = null;
let activeReactTarget = null;
let audioCtx = null;

// ============ AUDIO SYSTEM ============
function getAudioCtx() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioCtx;
}

function playSound(type) {
    if (!soundEnabled) return;
    try {
        const ctx = getAudioCtx();
        const masterGain = ctx.createGain();
        masterGain.connect(ctx.destination);
        masterGain.gain.value = 0.25;

        switch (type) {
            case 'keystroke': {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(masterGain);
                osc.type = 'square';
                osc.frequency.setValueAtTime(800 + Math.random() * 400, ctx.currentTime);
                gain.gain.setValueAtTime(0.3, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.04);
                osc.start(ctx.currentTime);
                osc.stop(ctx.currentTime + 0.04);
                break;
            }
            case 'send': {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(masterGain);
                osc.type = 'sine';
                osc.frequency.setValueAtTime(440, ctx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.1);
                gain.gain.setValueAtTime(0.5, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
                osc.start(ctx.currentTime);
                osc.stop(ctx.currentTime + 0.15);
                break;
            }
            case 'receive': {
                [0, 0.08, 0.15].forEach((delay, i) => {
                    const osc = ctx.createOscillator();
                    const gain = ctx.createGain();
                    osc.connect(gain); gain.connect(masterGain);
                    osc.type = 'sine';
                    const freqs = [523, 659, 784];
                    osc.frequency.value = freqs[i];
                    gain.gain.setValueAtTime(0, ctx.currentTime + delay);
                    gain.gain.linearRampToValueAtTime(0.4, ctx.currentTime + delay + 0.02);
                    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + delay + 0.12);
                    osc.start(ctx.currentTime + delay);
                    osc.stop(ctx.currentTime + delay + 0.12);
                });
                break;
            }
            case 'reaction': {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(masterGain);
                osc.type = 'sine';
                osc.frequency.setValueAtTime(1046, ctx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(1568, ctx.currentTime + 0.08);
                gain.gain.setValueAtTime(0.4, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2);
                osc.start(ctx.currentTime);
                osc.stop(ctx.currentTime + 0.2);
                break;
            }
            case 'theme': {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(masterGain);
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(200, ctx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(600, ctx.currentTime + 0.2);
                gain.gain.setValueAtTime(0.3, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
                osc.start(ctx.currentTime);
                osc.stop(ctx.currentTime + 0.25);
                break;
            }
            case 'error': {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(masterGain);
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(220, ctx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(110, ctx.currentTime + 0.3);
                gain.gain.setValueAtTime(0.4, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.35);
                osc.start(ctx.currentTime);
                osc.stop(ctx.currentTime + 0.35);
                break;
            }
        }
    } catch (e) {
        // Audio not supported — silently skip
    }
}

// ============ THEME SYSTEM ============
const themeOrder = ['cyberpunk', 'matrix', 'retro', 'light'];

function applyTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    currentTheme = theme;
    localStorage.setItem('nexus-theme', theme);

    // Update active dot
    themeBtns.forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-theme') === theme);
    });

    // Update particle colors from CSS vars
    updateParticleColors();
    playSound('theme');
    triggerGlitch();
}

function updateParticleColors() {
    const style = getComputedStyle(document.body);
    const p1 = style.getPropertyValue('--particle-1').trim();
    const p2 = style.getPropertyValue('--particle-2').trim();
    if (window._particleConfig) {
        window._particleConfig.color1 = p1;
        window._particleConfig.color2 = p2;
    }
}

themeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const theme = btn.getAttribute('data-theme');
        if (theme && theme !== currentTheme) {
            applyTheme(theme);
        }
    });
});

// ============ SOUND TOGGLE ============
if (soundToggle) {
    soundToggle.addEventListener('click', () => {
        soundEnabled = !soundEnabled;
        soundToggle.classList.toggle('muted', !soundEnabled);
        soundToggle.title = soundEnabled ? 'Sound ON' : 'Sound OFF';
        soundToggle.textContent = soundEnabled ? '🔊' : '🔇';
        if (soundEnabled) playSound('receive');
    });
}

// ============ INITIALIZATION ============
document.addEventListener('DOMContentLoaded', () => {
    // Load saved theme
    const savedTheme = localStorage.getItem('nexus-theme') || 'cyberpunk';
    applyTheme(savedTheme);

    initParticles();
    loadStats();
    messageInput.focus();
    triggerGlitch();

    // Close reaction picker on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.reaction-picker') && !e.target.closest('.react-trigger')) {
            hideReactionPicker();
        }
    });
});

// ============ EVENT LISTENERS ============
sendBtn.addEventListener('click', sendMessage);

messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    } else {
        playSound('keystroke');
    }
});

messageInput.addEventListener('input', () => {
    charCount.textContent = messageInput.value.length;
});

resetBtn.addEventListener('click', resetConversation);

quickBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const msg = btn.getAttribute('data-message');
        messageInput.value = msg;
        charCount.textContent = msg.length;
        sendMessage();
    });
});

// Reaction emoji buttons
if (reactionPicker) {
    reactionPicker.querySelectorAll('.reaction-emoji').forEach(emojiBtn => {
        emojiBtn.addEventListener('click', () => {
            const emoji = emojiBtn.textContent.trim();
            if (activeReactTarget) {
                addReactionToMessage(activeReactTarget, emoji);
                sendReactionToServer(emoji);
                playSound('reaction');
            }
            hideReactionPicker();
        });
    });
}

// ============ CHAT FUNCTIONS ============
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isProcessing) return;

    isProcessing = true;
    sendBtn.disabled = true;
    messageCount++;

    addMessage(message, 'user');
    messageInput.value = '';
    charCount.textContent = '0';
    playSound('send');

    const typingEl = showTyping();
    triggerGlitch();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await response.json();
        removeTyping(typingEl);
        await sleep(200);

        addMessage(data.response, 'bot', { llmUsed: data.llm_used, llmProvider: data.llm_provider });
        playSound('receive');

        if (data.mood && data.mood !== currentMood) {
            currentMood = data.mood;
            updateMood(data.mood);
        }

        // Update game state
        if (data.game_active) {
            activeGameType = data.game_type;
            showGameBadge(data.game_type);
        } else if (activeGameType && !data.game_active) {
            activeGameType = null;
            hideGameBadge();
        }

        triggerGlitch();

    } catch (error) {
        removeTyping(typingEl);
        addMessage('*static noises* CONNECTION ERROR! My circuits are temporarily scrambled. Try again!', 'bot');
        playSound('error');
    }

    isProcessing = false;
    sendBtn.disabled = false;
    messageInput.focus();
}

function addMessage(text, type, opts = {}) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}-message animate-in`;

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const formattedText = escapeHtml(text)
        .replace(/\n/g, '<br>')
        .replace(/\*([^*]+)\*/g, '<em style="color: var(--accent-2); font-style: italic;">$1</em>');

    if (type === 'bot') {
        const aiBadge = opts.llmUsed
            ? `<span class="ai-badge" title="Response generated by ${opts.llmProvider || 'AI'}">✨ AI</span>`
            : '';

        msgDiv.innerHTML = `
            <div class="message-avatar">
                <div class="avatar-bot${opts.llmUsed ? ' avatar-llm' : ''}">
                    <div class="avatar-eye left"></div>
                    <div class="avatar-eye right"></div>
                </div>
            </div>
            <div class="message-content">
                <div class="message-bubble">${formattedText}</div>
                <div class="message-meta">
                    <span class="message-time">${timeStr}</span>
                    ${aiBadge}
                    <button class="react-trigger" title="React" aria-label="Add reaction">+</button>
                </div>
                <div class="message-reactions"></div>
            </div>
        `;

        // Wire up react trigger
        const reactBtn = msgDiv.querySelector('.react-trigger');
        reactBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            showReactionPicker(msgDiv, reactBtn);
        });
    } else {
        msgDiv.innerHTML = `
            <div class="message-avatar">
                <div class="avatar-user">U</div>
            </div>
            <div class="message-content">
                <div class="message-bubble">${formattedText}</div>
                <span class="message-time">${timeStr}</span>
            </div>
        `;
    }

    chatMessages.appendChild(msgDiv);
    scrollToBottom();
}

function showTyping() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message animate-in';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="message-avatar">
            <div class="avatar-bot">
                <div class="avatar-eye left"></div>
                <div class="avatar-eye right"></div>
            </div>
        </div>
        <div class="message-content">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    scrollToBottom();
    return typingDiv;
}

function removeTyping(el) {
    if (el && el.parentNode) el.parentNode.removeChild(el);
}

async function resetConversation() {
    try {
        const response = await fetch('/api/reset', { method: 'POST' });
        const data = await response.json();

        const messages = chatMessages.querySelectorAll('.message');
        messages.forEach((msg, idx) => { if (idx > 0) msg.remove(); });

        addMessage(data.message, 'bot');
        currentMood = 'unknown';
        updateMood('unknown');
        messageCount = 0;
        activeGameType = null;
        hideGameBadge();
        triggerGlitch();
        playSound('theme');

    } catch (error) {
        addMessage('Reset failed! The chaos persists!', 'bot');
    }
}

// ============ REACTION SYSTEM ============
function showReactionPicker(msgEl, triggerBtn) {
    if (!reactionPicker) return;

    // If clicking same target, toggle off
    if (activeReactTarget === msgEl && reactionPicker.classList.contains('visible')) {
        hideReactionPicker();
        return;
    }

    activeReactTarget = msgEl;

    // Position near the trigger button
    const rect = triggerBtn.getBoundingClientRect();
    const containerRect = document.querySelector('.app-container').getBoundingClientRect();

    reactionPicker.style.position = 'fixed';
    reactionPicker.style.bottom = (window.innerHeight - rect.top + 8) + 'px';
    reactionPicker.style.left = Math.max(containerRect.left + 8, rect.left - 60) + 'px';

    reactionPicker.classList.add('visible');
}

function hideReactionPicker() {
    if (reactionPicker) reactionPicker.classList.remove('visible');
    activeReactTarget = null;
}

function addReactionToMessage(msgEl, emoji) {
    const reactionsDiv = msgEl.querySelector('.message-reactions');
    if (!reactionsDiv) return;

    // Check if emoji already exists
    const existing = reactionsDiv.querySelector(`[data-emoji="${emoji}"]`);
    if (existing) {
        const countEl = existing.querySelector('.r-count');
        countEl.textContent = parseInt(countEl.textContent) + 1;
        existing.style.transform = 'scale(1.3)';
        setTimeout(() => existing.style.transform = '', 200);
    } else {
        const badge = document.createElement('span');
        badge.className = 'msg-reaction';
        badge.setAttribute('data-emoji', emoji);
        badge.innerHTML = `${emoji} <span class="r-count">1</span>`;
        reactionsDiv.appendChild(badge);
    }
}

async function sendReactionToServer(emoji) {
    try {
        await fetch('/api/reaction', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ emoji })
        });
    } catch (e) {
        // Non-critical — reactions still show locally
    }
}

// ============ GAME STATE UI ============
function showGameBadge(gameType) {
    let badge = document.getElementById('gameBadge');
    if (!badge) {
        badge = document.createElement('div');
        badge.id = 'gameBadge';
        badge.className = 'game-badge';
        const inputArea = document.querySelector('.input-area') || document.querySelector('.chat-input');
        if (inputArea) inputArea.prepend(badge);
    }
    const labels = {
        hangman: '🎮 HANGMAN ACTIVE',
        trivia: '🎯 TRIVIA ACTIVE',
        twenty_questions: '❓ 20 QUESTIONS ACTIVE'
    };
    badge.textContent = labels[gameType] || `🎮 GAME: ${gameType}`;
    badge.style.display = 'block';
}

function hideGameBadge() {
    const badge = document.getElementById('gameBadge');
    if (badge) badge.style.display = 'none';
}

// ============ UI HELPERS ============
function scrollToBottom() {
    requestAnimationFrame(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateMood(mood) {
    if (!moodDisplay) return;
    moodDisplay.textContent = mood.toUpperCase();

    const moodColors = {
        happy:    '#00ff88',
        sad:      '#6366f1',
        angry:    '#ef4444',
        excited:  '#ffd600',
        tired:    '#8888aa',
        bored:    '#ff6b35',
        scared:   '#a855f7',
        lonely:   '#6366f1',
        confused: '#ffd600',
        savage:   '#ff6b35',
        unknown:  'var(--accent-1)'
    };

    const color = moodColors[mood] || moodColors.unknown;
    moodDisplay.style.color = color;
    moodDisplay.style.textShadow = `0 0 8px ${color}80`;
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        if (patternCount) patternCount.textContent = data.patterns;
    } catch (e) {
        if (patternCount) patternCount.textContent = '???';
    }
}

function triggerGlitch() {
    if (!glitchOverlay) return;
    glitchOverlay.classList.add('active');
    setTimeout(() => glitchOverlay.classList.remove('active'), 150);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ============ PARTICLE SYSTEM (theme-aware) ============
function initParticles() {
    const canvas = document.getElementById('particles');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const particles = [];

    // Shared config object so updateParticleColors() can mutate it live
    const style = getComputedStyle(document.body);
    window._particleConfig = {
        color1: style.getPropertyValue('--particle-1').trim() || '0,240,255',
        color2: style.getPropertyValue('--particle-2').trim() || '168,85,247'
    };

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);

    class Particle {
        constructor() { this.reset(); }

        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 0.5;
            this.speedX = (Math.random() - 0.5) * 0.5;
            this.speedY = (Math.random() - 0.5) * 0.5;
            this.opacity = Math.random() * 0.5 + 0.1;
            this.useColor2 = Math.random() > 0.5;
            this.pulse = Math.random() * Math.PI * 2;
            this.pulseSpeed = Math.random() * 0.02 + 0.01;
        }

        getColor() {
            return this.useColor2
                ? window._particleConfig.color2
                : window._particleConfig.color1;
        }

        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            this.pulse += this.pulseSpeed;
            this.opacity = Math.sin(this.pulse) * 0.25 + 0.25;

            if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
            if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
        }

        draw() {
            const c = this.getColor();
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${c}, ${this.opacity})`;
            ctx.fill();

            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size * 3, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${c}, ${this.opacity * 0.15})`;
            ctx.fill();
        }
    }

    const count = Math.min(80, Math.floor(window.innerWidth * window.innerHeight / 15000));
    for (let i = 0; i < count; i++) particles.push(new Particle());

    function drawConnections() {
        const c1 = window._particleConfig.color1;
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 150) {
                    const opacity = (1 - dist / 150) * 0.12;
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(${c1}, ${opacity})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => { p.update(); p.draw(); });
        drawConnections();
        requestAnimationFrame(animate);
    }

    animate();
}

// ============ EASTER EGGS ============
let konamiSequence = [];
const konamiCode = [38, 38, 40, 40, 37, 39, 37, 39, 66, 65];

document.addEventListener('keydown', (e) => {
    konamiSequence.push(e.keyCode);
    if (konamiSequence.length > konamiCode.length) konamiSequence.shift();
    if (JSON.stringify(konamiSequence) === JSON.stringify(konamiCode)) {
        messageInput.value = 'UP UP DOWN DOWN LEFT RIGHT LEFT RIGHT B A';
        sendMessage();
        konamiSequence = [];
    }
});

// Triple-click title cycles themes
let clickCount = 0;
let clickTimer = null;
const titleEl = document.querySelector('.title');
if (titleEl) {
    titleEl.addEventListener('click', () => {
        clickCount++;
        clearTimeout(clickTimer);
        clickTimer = setTimeout(() => { clickCount = 0; }, 500);
        if (clickCount >= 3) {
            const idx = themeOrder.indexOf(currentTheme);
            applyTheme(themeOrder[(idx + 1) % themeOrder.length]);
            triggerMatrixFlash();
            clickCount = 0;
        }
    });
}

function triggerMatrixFlash() {
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed; inset: 0; z-index: 9999; pointer-events: none;
        background: rgba(0,0,0,0.85); display: flex; align-items: center;
        justify-content: center; font-family: var(--font-main); font-size: 22px;
        color: var(--accent-1); text-shadow: 0 0 20px var(--accent-1);
        animation: fadeIn 0.2s ease;
    `;
    overlay.textContent = `[ THEME: ${currentTheme.toUpperCase()} ]`;
    document.body.appendChild(overlay);
    setTimeout(() => {
        overlay.style.transition = 'opacity 0.8s';
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 800);
    }, 1200);
}
