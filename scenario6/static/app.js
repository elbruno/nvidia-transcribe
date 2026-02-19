/**
 * PersonaPlex Voice Conversation — Client Application
 *
 * Handles:
 *  - Theme switching (system / light / dark)
 *  - Server config loading (voices, personas)
 *  - Moshi WebSocket proxy connection for full-duplex audio
 *    (uses /proxy/moshi so WSS same-origin avoids mixed-content block)
 *  - Auto-connect on load; handshake-gated mic enable
 *  - Microphone capture via MediaRecorder → Opus chunks
 *  - Scheduled AudioContext playback queue for gapless output
 *  - Real-time server log streaming
 */
(function () {
    'use strict';

    /* ==================================================================
       DOM handles
       ================================================================== */
    var $convo      = document.getElementById('convoScroll');
    var $hero       = document.getElementById('heroCard');
    var $mic        = document.getElementById('micBtn');
    var $conn       = document.getElementById('connPill');
    var $bk         = document.getElementById('bkPill');
    var $logFeed    = document.getElementById('logFeed');
    var $logBar     = document.getElementById('logBar');
    var $caret      = document.getElementById('caret');
    var $logNum     = document.getElementById('logNum');
    var $logWipe    = document.getElementById('logWipe');
    var $wipeChat   = document.getElementById('wipeChatBtn');
    var $link       = document.getElementById('linkBtn');
    var $backendHint = document.getElementById('backendHint');
    var $voicePick  = document.getElementById('voicePick');
    var $persona    = document.getElementById('personaField');
    var $chipRow    = document.getElementById('chipRow');
    var $portHint   = document.getElementById('portHint');

    var logSock     = null;
    var moshiSock   = null;
    var recorder    = null;
    var micStream   = null;
    var streamActive = false;
    var handshakeOk  = false;   // true after server sends \x00 "ready" byte
    var reconnTimer  = null;
    var logCounter  = 0;
    var logFolded   = false;
    var cfg         = {};

    // Audio playback — scheduled queue so chunks play gaplessly
    var audioCtx    = null;
    var nextPlayAt  = 0;
    var textBuf     = '';
    var textTimer   = null;

    /* ==================================================================
       Theme
       ================================================================== */
    function pickTheme(name) {
        document.documentElement.setAttribute('data-theme', name);
        try { localStorage.setItem('pp-theme', name); } catch (_) { /* noop */ }
        document.querySelectorAll('.t-pick').forEach(function (b) {
            b.classList.toggle('active', b.getAttribute('data-t') === name);
        });
    }
    document.querySelectorAll('.t-pick').forEach(function (b) {
        b.addEventListener('click', function () { pickTheme(b.getAttribute('data-t')); });
    });
    pickTheme(localStorage.getItem('pp-theme') || 'system');

    /* ==================================================================
       Config loader
       ================================================================== */
    function fetchConfig() {
        fetch('/api/config').then(function (r) { return r.json(); }).then(function (c) {
            cfg = c;
            var host = c.moshi_host || location.hostname || 'localhost';
            var port = c.moshi_port || 8998;
            var scheme = c.moshi_ws_scheme || 'wss';
            var wsUrl = c.moshi_ws_url || (scheme + '://' + host + ':' + port);
            if ($backendHint) $backendHint.textContent = wsUrl;

            // voices
            $voicePick.innerHTML = '';
            if (c.voices) {
                Object.keys(c.voices).forEach(function (grp) {
                    var og = document.createElement('optgroup');
                    og.label = grp;
                    c.voices[grp].forEach(function (v) {
                        var o = document.createElement('option');
                        o.value = v; o.textContent = v;
                        if (v === c.default_voice) o.selected = true;
                        og.appendChild(o);
                    });
                    $voicePick.appendChild(og);
                });
            }

            // presets
            $chipRow.innerHTML = '';
            if (c.persona_presets) {
                Object.keys(c.persona_presets).forEach(function (k) {
                    var btn = document.createElement('button');
                    btn.className = 'chip';
                    btn.textContent = k;
                    btn.addEventListener('click', function () {
                        $persona.value = c.persona_presets[k];
                        clog('Persona → ' + k);
                    });
                    $chipRow.appendChild(btn);
                });
            }
            $persona.value = c.default_persona || '';

            var statusText = c.moshi_backend_status || (c.moshi_backend_running === true ? 'Running' : c.moshi_backend_running === false ? 'Stopped' : 'External');
            var statusClass = c.moshi_backend_running === true ? 'ok' : c.moshi_backend_running === false ? 'disc' : 'wait';
            $bk.textContent = statusText;
            $bk.className   = 'conn-pill ' + statusClass;
            clog('Config loaded — connecting…');
            // Auto-connect once config is ready
            openMoshi();
        }).catch(function (e) { clog('Config error: ' + e.message); });
    }
    fetchConfig();

    /* ==================================================================
       Moshi WebSocket (direct connection to backend)
       ================================================================== */
    $link.addEventListener('click', function () {
        if (moshiSock && moshiSock.readyState === WebSocket.OPEN) {
            moshiSock.close();
            if (reconnTimer) { clearTimeout(reconnTimer); reconnTimer = null; }
            return;
        }
        openMoshi();
    });

    function buildMoshiUrl() {
        var voice = ($voicePick && $voicePick.value) ? $voicePick.value : (cfg.default_voice || 'NATF2');
        var voicePrompt = normalizeVoice(voice);
        var persona = ($persona && $persona.value) ? $persona.value : '';
        // Connect directly to the moshi backend (both services run HTTP/WS)
        var wsUrl = cfg.moshi_ws_url;
        if (!wsUrl) {
            var scheme = (cfg.moshi_ws_scheme === 'wss') ? 'wss' : 'ws';
            var host = cfg.moshi_host || location.hostname || 'localhost';
            var port = cfg.moshi_port || 8998;
            wsUrl = scheme + '://' + host + ':' + port + '/api/chat';
        }
        // Ensure ws/wss scheme
        wsUrl = wsUrl.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:');
        return (
            wsUrl
            + '?voice_prompt=' + encodeURIComponent(voicePrompt)
            + '&text_prompt='  + encodeURIComponent(persona)
        );
    }

    function openMoshi() {
        if (moshiSock && moshiSock.readyState !== WebSocket.CLOSED) return;
        handshakeOk = false;
        var url = buildMoshiUrl();
        clog('Connecting → ' + url.split('?')[0]);
        setConnState('connecting');
        $link.textContent = 'Connecting…';

        try { moshiSock = new WebSocket(url); } catch (e) {
            clog('WS error: ' + e.message);
            setConnState('error');
            $link.textContent = 'Reconnect';
            return;
        }
        moshiSock.binaryType = 'arraybuffer';

        moshiSock.onopen = function () {
            // Connected to proxy — now waiting for moshi \x00 handshake
            setConnState('warming');
            $link.textContent = 'Disconnect';
            clog('Proxy open — waiting for model handshake…');
            pushBubble('s', '⏳ Loading model — please wait…');
        };

        moshiSock.onclose = function (ev) {
            setConnState('disc');
            if (streamActive) capStop();
            $link.textContent = 'Reconnect';
            handshakeOk = false;
            clog('Disconnected (code ' + ev.code + ')');
            // Auto-reconnect after 4 s unless user manually closed (code 1000)
            if (ev.code !== 1000 && ev.code !== 1001) {
                reconnTimer = setTimeout(openMoshi, 4000);
                clog('Will reconnect in 4 s…');
            }
        };

        moshiSock.onerror = function () {
            setConnState('error');
            clog('WS error — check backend');
            pushBubble('s', '⚠️ Connection error. Retrying…');
        };

        moshiSock.onmessage = function (ev) {
            if (!(ev.data instanceof ArrayBuffer)) {
                try {
                    var d = JSON.parse(ev.data);
                    if (d.text) accumText(d.text);
                } catch (_) {}
                return;
            }
            var data = new Uint8Array(ev.data);
            if (!data.length) return;
            var kind    = data[0];
            var payload = data.slice(1);

            if (kind === 0) {
                // Server handshake — model is ready
                handshakeOk = true;
                setConnState('ready');
                $mic.classList.remove('off');
                clog('Handshake received — model ready');
                pushBubble('s', '🟢 Ready — click Start to begin');
                resetAudio();
                return;
            }
            if (kind === 1) {
                // Opus audio from moshi
                schedulePlay(payload.buffer);
                return;
            }
            if (kind === 2) {
                // Text token fragment
                var tok = new TextDecoder('utf-8').decode(payload);
                if (tok) accumText(tok);
            }
        };
    }

    function setConnState(state) {
        var label = { connecting: 'Connecting', warming: 'Warming up…', ready: 'Live',
                      disc: 'Disconnected', error: 'Error' }[state] || state;
        var cls   = { connecting: 'wait', warming: 'warm', ready: 'ok',
                      disc: 'disc', error: 'disc' }[state] || 'disc';
        $conn.textContent = label;
        $conn.className   = 'conn-pill ' + cls;
        if (state !== 'ready') { $mic.classList.add('off'); }
    }

    /* ==================================================================
       Audio playback — AudioContext scheduled queue for gapless output
       ================================================================== */
    function resetAudio() {
        audioCtx   = new (window.AudioContext || window.webkitAudioContext)();
        nextPlayAt = audioCtx.currentTime;
    }

    function schedulePlay(buf) {
        if (!audioCtx) return;
        audioCtx.decodeAudioData(buf.slice(0), function (decoded) {
            var src = audioCtx.createBufferSource();
            src.buffer = decoded;
            src.connect(audioCtx.destination);
            var now = audioCtx.currentTime;
            if (nextPlayAt < now) nextPlayAt = now;
            src.start(nextPlayAt);
            nextPlayAt += decoded.duration;
        }, function () {
            // decodeAudioData failed — chunk may be an intermediate Opus frame; ignore silently
        });
    }

    /* ==================================================================
       Text token accumulator — fragments arrive word-by-word; batch them
       ================================================================== */
    function accumText(tok) {
        textBuf += tok;
        if (textTimer) clearTimeout(textTimer);
        textTimer = setTimeout(function () {
            if (textBuf.trim()) { pushBubble('a', '🧠 ' + textBuf.trim()); }
            textBuf = '';
            textTimer = null;
        }, 600);
    }

    /* ==================================================================
       Microphone capture — MediaRecorder → Opus chunks → WS
       ================================================================== */
    function capStart() {
        if (!handshakeOk) { clog('Model not ready yet'); return; }
        if (!moshiSock || moshiSock.readyState !== WebSocket.OPEN) { clog('Not connected'); return; }
        if (streamActive) return;

        navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
            micStream = stream;
            var opts = pickRecorderOptions();
            try {
                recorder = opts ? new MediaRecorder(stream, opts) : new MediaRecorder(stream);
            } catch (e) {
                clog('Recorder error: ' + e.message);
                stream.getTracks().forEach(function (t) { t.stop(); });
                return;
            }

            recorder.ondataavailable = function (ev) {
                if (!ev.data || ev.data.size === 0) return;
                ev.data.arrayBuffer().then(function (buf) {
                    if (!moshiSock || moshiSock.readyState !== WebSocket.OPEN) return;
                    var payload = new Uint8Array(buf);
                    var framed = new Uint8Array(payload.length + 1);
                    framed[0] = 1;
                    framed.set(payload, 1);
                    moshiSock.send(framed);
                }).catch(function (e) { clog('Chunk error: ' + e.message); });
            };

            recorder.onstop = function () {
                if (micStream) {
                    micStream.getTracks().forEach(function (t) { t.stop(); });
                    micStream = null;
                }
            };

            recorder.start(100);   // 100 ms chunks for low latency
            streamActive = true;
            $mic.classList.add('rec');
            $mic.innerHTML = 'Stop';
            $conn.textContent = 'Live'; $conn.className = 'conn-pill ok';
            clog('Streaming audio');
        }).catch(function (e) { clog('Mic error: ' + e.message); });
    }

    function capStop() {
        if (!streamActive) return;
        streamActive = false;
        if (recorder && recorder.state !== 'inactive') { recorder.stop(); }
        if (micStream) {
            micStream.getTracks().forEach(function (t) { t.stop(); });
            micStream = null;
        }
        $mic.classList.remove('rec');
        $mic.innerHTML = 'Start';
        if (handshakeOk && moshiSock && moshiSock.readyState === WebSocket.OPEN) {
            setConnState('ready');
        }
        clog('Streaming stopped');
    }

    function normalizeVoice(voice) {
        if (!voice) return 'NATF2.pt';
        if (voice.indexOf('.') === -1) return voice + '.pt';
        return voice;
    }

    function pickRecorderOptions() {
        if (typeof MediaRecorder === 'undefined') return null;
        var types = [
            'audio/ogg;codecs=opus',
            'audio/webm;codecs=opus'
        ];
        for (var i = 0; i < types.length; i++) {
            if (MediaRecorder.isTypeSupported(types[i])) return { mimeType: types[i] };
        }
        return null;
    }

    /* ==================================================================
       Chat bubbles
       ================================================================== */
    function pushBubble(kind, text) {
        if ($hero) $hero.style.display = 'none';
        var el = document.createElement('div');
        el.className = 'bubble ' + kind;
        if (kind !== 's') {
            var tag = document.createElement('div');
            tag.className = 'tag';
            tag.textContent = kind === 'u' ? 'You' : 'PersonaPlex';
            el.appendChild(tag);
        }
        var sp = document.createElement('span');
        sp.textContent = text;
        el.appendChild(sp);
        $convo.appendChild(el);
        $convo.scrollTop = $convo.scrollHeight;
    }

    $wipeChat.addEventListener('click', function () {
        $convo.innerHTML = '';
        var h = document.createElement('div');
        h.className = 'welcome-hero'; h.id = 'heroCard';
        var emoji = document.createElement('div'); emoji.className = 'hero-emoji'; emoji.textContent = '🗣️';
        var heading = document.createElement('h2'); heading.textContent = 'Ready to Talk';
        var para = document.createElement('p'); para.textContent = 'Click Start to begin a live conversation.';
        h.appendChild(emoji); h.appendChild(heading); h.appendChild(para);
        $convo.appendChild(h);
        $hero = h;
        clog('Chat cleared');
    });

    /* ==================================================================
       Mic button bindings
       ================================================================== */
    $mic.addEventListener('click', function (e) {
        e.preventDefault();
        if (streamActive) { capStop(); } else { capStart(); }
    });

    /* ==================================================================
       Log panel
       ================================================================== */
    $logBar.addEventListener('click', function (e) {
        if (e.target === $logWipe) return;
        logFolded = !logFolded;
        $logFeed.classList.toggle('shut', logFolded);
        $caret.textContent = logFolded ? '▼' : '▲';
    });
    $logWipe.addEventListener('click', function (e) {
        e.stopPropagation();
        $logFeed.innerHTML = '';
        logCounter = 0;
        $logNum.style.display = 'none';
    });

    function openLogSocket() {
        var proto = location.protocol === 'https:' ? 'wss' : 'ws';
        logSock = new WebSocket(proto + '://' + location.host + '/ws/logs');
        logSock.onmessage = function (ev) {
            var d = JSON.parse(ev.data);
            addLogLine(d.timestamp, d.level, d.message, d.detail || '');
        };
        logSock.onclose = function () { setTimeout(openLogSocket, 3000); };
        logSock.onerror = function () { logSock.close(); };
    }

    function addLogLine(ts, lv, msg, detail) {
        var wrap = document.createElement('div');
        var row  = document.createElement('div'); row.className = 'l-row';

        var t = document.createElement('span'); t.className = 'l-ts'; t.textContent = ts;
        var l = document.createElement('span'); l.className = 'l-lv ' + lv; l.textContent = lv;
        var m = document.createElement('span'); m.className = 'l-mg'; m.textContent = msg;
        row.appendChild(t); row.appendChild(l); row.appendChild(m);

        if (detail) {
            var tog = document.createElement('span'); tog.className = 'l-dt-toggle'; tog.textContent = '▶ details';
            row.appendChild(tog);
            var dd = document.createElement('div'); dd.className = 'l-dt'; dd.textContent = detail;
            tog.addEventListener('click', function () {
                var open = dd.classList.toggle('show');
                tog.textContent = open ? '▼ details' : '▶ details';
            });
            wrap.appendChild(row); wrap.appendChild(dd);
        } else { wrap.appendChild(row); }

        $logFeed.appendChild(wrap);
        $logFeed.scrollTop = $logFeed.scrollHeight;
        logCounter++;
        $logNum.textContent = logCounter;
        $logNum.style.display = 'inline';
        while ($logFeed.children.length > 200) $logFeed.removeChild($logFeed.firstChild);
    }

    function clog(msg) {
        var d = new Date();
        var ts = d.toLocaleTimeString('en-GB', { hour12: false });
        addLogLine(ts, 'INFO', msg, '');
    }

    openLogSocket();
})();
