/**
 * PersonaPlex Voice Conversation — Client Application
 *
 * Handles:
 *  - Theme switching (system / light / dark)
 *  - Server config loading (voices, personas)
 *  - Moshi WebSocket connection for full-duplex audio
 *  - Microphone capture via Web Audio API
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
    var $bkRestart  = document.getElementById('bkRestart');
    var $voicePick  = document.getElementById('voicePick');
    var $persona    = document.getElementById('personaField');
    var $chipRow    = document.getElementById('chipRow');
    var $portHint   = document.getElementById('portHint');

    var logSock     = null;
    var moshiSock   = null;
    var recorder    = null;
    var logCounter  = 0;
    var logFolded   = false;
    var cfg         = {};

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
            if ($portHint) $portHint.textContent = c.moshi_port || '8998';

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

            $bk.textContent = c.moshi_backend_running ? 'Running' : 'Stopped';
            $bk.className   = 'conn-pill ' + (c.moshi_backend_running ? 'ok' : 'disc');
            clog('Config loaded');
        }).catch(function (e) { clog('Config error: ' + e.message); });
    }
    fetchConfig();

    /* ==================================================================
       Backend restart
       ================================================================== */
    $bkRestart.addEventListener('click', function () {
        clog('Restarting backend…');
        $bk.textContent = 'Restarting'; $bk.className = 'conn-pill wait';
        fetch('/api/restart-backend', { method: 'POST' })
            .then(function () { clog('Restart requested'); setTimeout(fetchConfig, 5000); })
            .catch(function (e) { clog('Restart failed: ' + e.message); });
    });

    /* ==================================================================
       Moshi WebSocket
       ================================================================== */
    $link.addEventListener('click', function () {
        if (moshiSock && moshiSock.readyState === WebSocket.OPEN) { moshiSock.close(); return; }
        openMoshi();
    });

    function openMoshi() {
        var port = cfg.moshi_port || 8998;
        var url  = 'wss://localhost:' + port;
        clog('Connecting → ' + url);
        $conn.textContent = 'Connecting'; $conn.className = 'conn-pill wait';
        $link.textContent = 'Connecting…';

        try { moshiSock = new WebSocket(url); } catch (e) {
            clog('WS error: ' + e.message);
            $conn.textContent = 'Failed'; $conn.className = 'conn-pill disc';
            $link.textContent = 'Connect'; return;
        }
        moshiSock.binaryType = 'arraybuffer';

        moshiSock.onopen = function () {
            $conn.textContent = 'Connected'; $conn.className = 'conn-pill ok';
            $mic.classList.remove('off'); $link.textContent = 'Disconnect';
            clog('Moshi connected');
            pushBubble('s', '🟢 Connected — start speaking!');
        };
        moshiSock.onclose = function () {
            $conn.textContent = 'Disconnected'; $conn.className = 'conn-pill disc';
            $mic.classList.add('off'); $link.textContent = 'Connect';
            clog('Moshi disconnected');
        };
        moshiSock.onerror = function () {
            clog('WS error — backend running?');
            $conn.textContent = 'Error'; $conn.className = 'conn-pill disc';
            $link.textContent = 'Connect';
            pushBubble('s', '⚠️ Cannot reach moshi backend. Accept the self-signed cert by visiting https://localhost:' + (cfg.moshi_port || 8998) + ' first.');
        };
        moshiSock.onmessage = function (ev) {
            if (ev.data instanceof ArrayBuffer) {
                playBuffer(ev.data);
            } else {
                try {
                    var d = JSON.parse(ev.data);
                    if (d.text) pushBubble('a', '🧠 ' + d.text);
                } catch (_) { pushBubble('a', '🔊 ' + ev.data); }
            }
        };
    }

    /* ==================================================================
       Audio playback
       ================================================================== */
    function playBuffer(buf) {
        try {
            var blob = new Blob([buf], { type: 'audio/ogg' });
            var player = new Audio(URL.createObjectURL(blob));
            player.play().catch(function (e) { clog('Play error: ' + e.message); });
        } catch (e) { clog('Decode error: ' + e.message); }
    }

    /* ==================================================================
       Microphone capture (Web Audio ScriptProcessor → 16 kHz mono PCM)
       ================================================================== */
    function capStart() {
        if (!moshiSock || moshiSock.readyState !== WebSocket.OPEN) { clog('Not connected'); return; }
        if (recorder && recorder.active) return;

        navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
            var ctx  = new AudioContext({ sampleRate: 16000 });
            var src  = ctx.createMediaStreamSource(stream);
            var proc = ctx.createScriptProcessor(4096, 1, 1);
            var chunks = [];

            proc.onaudioprocess = function (e) { chunks.push(new Float32Array(e.inputBuffer.getChannelData(0))); };
            src.connect(proc); proc.connect(ctx.destination);

            recorder = {
                active: true,
                done: function () {
                    proc.disconnect(); src.disconnect();
                    stream.getTracks().forEach(function (t) { t.stop(); });

                    // merge captured float32 chunks
                    var total = 0;
                    chunks.forEach(function (c) { total += c.length; });
                    var pcm = new Float32Array(total);
                    var off = 0;
                    chunks.forEach(function (c) { pcm.set(c, off); off += c.length; });

                    var wav = buildWav(pcm, 16000);
                    pushBubble('u', '🎤 [audio ' + (wav.size / 1024).toFixed(1) + ' KB]');
                    clog('Sending ' + (wav.size / 1024).toFixed(1) + ' KB');
                    if (moshiSock && moshiSock.readyState === WebSocket.OPEN) moshiSock.send(wav);
                    ctx.close();
                }
            };

            $mic.classList.add('rec');
            $mic.innerHTML = '🔴<br>Recording';
            $conn.textContent = 'Recording'; $conn.className = 'conn-pill wait';
        }).catch(function (e) { clog('Mic error: ' + e.message); });
    }

    function capStop() {
        if (recorder && recorder.active) { recorder.active = false; recorder.done(); }
        $mic.classList.remove('rec');
        $mic.innerHTML = 'Hold to<br>Talk';
        if (moshiSock && moshiSock.readyState === WebSocket.OPEN) {
            $conn.textContent = 'Connected'; $conn.className = 'conn-pill ok';
        }
    }

    /* ==================================================================
       WAV builder — packs Float32 PCM into a 16-bit LE RIFF/WAVE blob
       ================================================================== */
    function buildWav(samples, sr) {
        var nSamples = samples.length;
        var payloadBytes = nSamples * 2;
        var headerSize = 44;
        var ab = new ArrayBuffer(headerSize + payloadBytes);
        var v  = new DataView(ab);

        // -- RIFF chunk descriptor --
        setASCII(v, 0, 'RIFF');
        v.setUint32(4, headerSize - 8 + payloadBytes, true);
        setASCII(v, 8, 'WAVE');

        // -- fmt  sub-chunk --
        setASCII(v, 12, 'fmt ');
        v.setUint32(16, 16, true);          // sub-chunk size (PCM)
        v.setUint16(20, 1, true);           // audio format: PCM
        v.setUint16(22, 1, true);           // mono
        v.setUint32(24, sr, true);          // sample rate
        v.setUint32(28, sr * 2, true);      // byte rate
        v.setUint16(32, 2, true);           // block align
        v.setUint16(34, 16, true);          // bits per sample

        // -- data sub-chunk --
        setASCII(v, 36, 'data');
        v.setUint32(40, payloadBytes, true);

        // -- write PCM samples (float → int16) --
        for (var i = 0; i < nSamples; i++) {
            var f = samples[i];
            if (f > 1) f = 1; else if (f < -1) f = -1;
            v.setInt16(headerSize + i * 2, (f * 32767) | 0, true);
        }

        return new Blob([ab], { type: 'audio/wav' });
    }

    function setASCII(dv, pos, s) {
        for (var i = 0; i < s.length; i++) dv.setUint8(pos + i, s.charCodeAt(i));
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
        var para = document.createElement('p'); para.textContent = 'Hold the mic button to start.';
        h.appendChild(emoji); h.appendChild(heading); h.appendChild(para);
        $convo.appendChild(h);
        clog('Chat cleared');
    });

    /* ==================================================================
       Mic button bindings
       ================================================================== */
    $mic.addEventListener('mousedown',  function (e) { e.preventDefault(); capStart(); });
    $mic.addEventListener('mouseup',    function (e) { e.preventDefault(); capStop(); });
    $mic.addEventListener('mouseleave', function ()  { if ($mic.classList.contains('rec')) capStop(); });
    $mic.addEventListener('touchstart', function (e) { e.preventDefault(); capStart(); });
    $mic.addEventListener('touchend',   function (e) { e.preventDefault(); capStop(); });

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
