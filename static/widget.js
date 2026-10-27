/**
 * website-ai-chatbot — embeddable floating chat widget.
 *
 * Self-contained, no dependencies. Uses a Shadow DOM so the host page's CSS
 * and scripts cannot leak in, and nothing leaks out.
 *
 * Usage
 * -----
 *   <script src="https://your-host/widget.js"
 *           data-api-url="https://your-host"
 *           data-position="bottom-right"
 *           data-title="VaaniLink Assistant"
 *           defer></script>
 *
 * Options (all optional)
 *   data-api-url      Backend origin. Default: the origin of this script.
 *   data-position     bottom-right (default) | bottom-left
 *   data-title        Panel heading text.
 *   data-accent       Accent colour (CSS colour).
 *   data-placeholder   Input placeholder.
 *   data-welcome      First assistant message.
 *   data-history      Max stored messages (default 20).
 */
(function () {
  'use strict';

  var STYLE = '  var STYLE = \':host{all:initial}\' +\n        \':host{--cb-accent:#84cc16}\' +\n        \'.cb-root{position:fixed;z-index:2147483000;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;bottom:90px;right:24px;display:flex;flex-direction:column;align-items:flex-end;gap:12px}\' +\n        \'.cb-root[data-pos="bottom-left"]{right:auto;left:24px;align-items:flex-start}\' +\n        \'.cb-launcher{width:56px;height:56px;border-radius:50%;border:0;cursor:pointer;background:var(--cb-accent);color:#1a2e05;display:flex;align-items:center;justify-content:center;box-shadow:0 10px 25px rgba(0,0,0,.22);transition:transform .18s ease,box-shadow .18s ease}\' +\n        \'.cb-launcher:hover{transform:scale(1.06)}\' +\n        \'.cb-launcher:active{transform:scale(.96)}\' +\n        \'.cb-launcher:focus-visible{outline:3px solid #1a2e05;outline-offset:2px}\' +\n        \'.cb-badge{position:absolute;top:-2px;right:-2px;min-width:20px;height:20px;padding:0 5px;border-radius:10px;background:#dc2626;color:#fff;font-size:11px;font-weight:700;line-height:20px;text-align:center}\' +\n        \'.cb-panel{width:370px;max-width:calc(100vw - 32px);height:520px;max-height:calc(100vh - 120px);display:flex;flex-direction:column;border-radius:18px;overflow:hidden;background:rgba(255,255,255,.96);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border:1px solid rgba(132,204,22,.45);box-shadow:0 20px 60px rgba(0,0,0,.32);animation:cb-pop .18s ease}\' +\n        \'@keyframes cb-pop{from{opacity:0;transform:translateY(10px) scale(.98)}to{opacity:1;transform:none}}\' +\n        \'.cb-head{padding:14px 16px;background:linear-gradient(135deg,#f7fee7,#ecfccb);border-bottom:1px solid rgba(132,204,22,.35);display:flex;align-items:center;gap:10px}\' +\n        \'.cb-dot{width:9px;height:9px;border-radius:50%;background:#65a30d;box-shadow:0 0 0 3px rgba(132,204,22,.25);flex:none}\' +\n        \'.cb-dot[data-offline="true"]{background:#dc2626;box-shadow:0 0 0 3px rgba(220,38,38,.25)}\' +\n        \'.cb-title{font-size:14px;font-weight:700;color:#1a2e05;line-height:1.2}\' +\n        \'.cb-sub{font-size:11px;color:#4d7c0f;line-height:1.2}\' +\n        \'.cb-close{margin-left:auto;border:0;background:transparent;cursor:pointer;color:#4d7c0f;font-size:20px;line-height:1;padding:2px 6px;border-radius:8px}\' +\n        \'.cb-close:hover{background:rgba(132,204,22,.2);color:#1a2e05}\' +\n        \'.cb-body{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px;scroll-behavior:smooth;background:rgba(255,255,255,.5);border-top:1px solid rgba(132,204,22,.25)}\' +\n        \'.cb-markdown{padding:0;margin:0;line-height:1.55;font-size:14px;color:#1f2937}\' +\n        \'.cb-markdown h2{font-size:1.05rem;font-weight:700;color:#111827;margin:12px 0 6px;padding-bottom:4px;border-bottom:2px solid rgba(132,204,22,.3)}\' +\n        \'.cb-markdown h3{font-size:0.92rem;font-weight:600;color:#374151;margin:10px 0 4px;padding-bottom:3px;border-bottom:1px solid rgba(132,204,22,.2)}\' +\n        \'.cb-markdown p{margin:0 0 8px}\' +\n        \'.cb-markdown ul{list-style-type:disc;margin:6px 0 10px;padding-left:18px}\' +\n        \'.cb-markdown ol{list-style-type:decimal;margin:6px 0 10px;padding-left:22px}\' +\n        \'.cb-markdown li{margin:3px 0}\' +\n        \'.cb-markdown strong{font-weight:600}\' +\n        \'.cb-markdown em{font-style:italic}\' +\n        \'.cb-markdown a{color:#2563eb;text-decoration:underline;background:transparent}\' +\n        \'.cb-markdown a:hover{color:#1d4ed8}\' +\n        \'.cb-code{background:#0f172a;color:#e2e8f0;border-radius:10px;padding:10px 12px;overflow-x:auto;font-size:12.5px;line-height:1.5;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Courier New",monospace;white-space:pre-wrap;word-break:break-word;margin:6px 0 10px;position:relative}\' +\n        \'.cb-code::before{content:"├── ";position:absolute;left:2px;font-size:10px;color:#475569}\' +\n        \'.cb-code .cb-lang{font-size:10px;color:#94a3b8;font-weight:600;margin-right:6px}\' +\n        \'.cb-code code{background:transparent;padding:0;margin:0;color:#e2e8f0}\' +\n        \'.cb-src{margin-top:7px;padding-top:6px;border-top:1px solid rgba(132,204,22,.25);display:flex;flex-wrap:wrap;gap:4px}\' +\n        \'.cb-src{font-size:10.5px;line-height:1.25;padding:2px 7px;border-radius:8px;background:#f7fee7;border:1px solid rgba(132,204,22,.35);color:#4d7c0f;max-width:100%;word-break:break-word}\' +\n        \'.cb-src::before{content:"\\\\u270E  "}\' +\n        \'.cb-user{align-self:flex-end;background:var(--cb-accent);color:#1a2e05;border-bottom-right-radius:5px;padding:9px 13px}\' +\n        \'.cb-user p{margin:0 0 4px 0}\' +\n        \'.cb-user .cb-msg{padding:0;font-size:13.5px}\' +\n        \'.cb-bot{align-self:flex-start;background:rgba(247,254,231,.92);color:#1f2937;border:1px solid rgba(132,204,22,.3);border-bottom-left-radius:5px;padding:10px 13px}\' +\n        \'.cb-bot p{margin:0 0 6px 0;font-size:13.5px}\' +\n        \'.cb-bot .cb-msg{padding:0}\' +\n        \'.cb-bot .cb-code{margin:4px 0 8px 0;position:relative}\' +\n        \'.cb-bot .cb-code::before{content:"#  ";position:absolute;left:4px;font-size:10px;color:#94a3b8}\' +\n        \'.cb-bot .cb-h2{font-size:1.05rem;font-weight:700;color:#111827;margin:10px 0 6px;padding-bottom:3px;border-bottom:1px solid rgba(132,204,22,.2)}\' +\n        \'.cb-bot .cb-h3{font-size:0.92rem;font-weight:600;color:#374151;margin:8px 0 4px;padding-bottom:2px;border-bottom:1px solid rgba(132,204,22,.15)}\' +\n        \'.cb-bot .cb-ul{list-style-type:none;margin:4px 0 8px 0;padding-left:4px}\' +\n        \'.cb-bot .cb-ul li{margin:2px 0;padding-left:16px;background-image:url("data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%228%22 height=%228%22 viewBox=%220 0 8 8%22><circle cx=%224%22 cy=%224%22 r=%222%22 fill=%22%2384cc16%22/></svg>");background-repeat:no-repeat;background-position:left center;background-size:8px}\' +\n        \'.cb-bot .cb-ol{list-style-type:none;margin:4px 0 8px 0;padding-left:4px}\' +\n        \'.cb-bot .cb-ol li{margin:2px 0;padding-left:16px;background-image:url("data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%228%22 height=%228%22 viewBox=%220 0 8 8%22><path d=%22M4 0L8 8H0z%22 fill=%22%2384cc16%22/></svg>");background-repeat:no-repeat;background-position:left center;background-size:7px 7px}\' +\n        \'.cb-bot .cb-code{margin:4px 0 8px 0;position:relative}\' +\n        \'.cb-bot .cb-code::before{content:"//  ";position:absolute;left:4px;font-size:10px;color:#94a3b8}\' +\n        \'.cb-typing{display:flex;gap:4px;padding:12px 14px;align-self:flex-start;background:rgba(247,254,231,.9);border-radius:14px;border:1px solid rgba(132,204,22,.3)}\' +\n        \'.cb-typing i{width:6px;height:6px;border-radius:50%;background:#84cc16;animation:cb-blink 1.2s infinite both}\' +\n        \'.cb-typing i:nth-child(2){animation-delay:.15s}\' +\n        \'.cb-typing i:nth-child(3){animation-delay:.3s}\' +\n        \'@keyframes cb-blink{0%,80%,100%{opacity:.25;transform:none}40%{opacity:1;transform:translateY(-3px)}}\' +\n        \'.cb-foot{padding:10px;border-top:1px solid rgba(132,204,22,.3);background:rgba(255,255,255,.75);display:flex;gap:8px;align-items:flex-end}\' +\n        \'.cb-input{flex:1;resize:none;border:1px solid rgba(132,204,22,.4);border-radius:12px;padding:9px 11px;font-size:13.5px;font-family:inherit;line-height:1.4;max-height:110px;background:#fff;color:#1f2937}\' +\n        \'.cb-input:focus{outline:none;border-color:var(--cb-accent);box-shadow:0 0 0 3px rgba(132,204,22,.2)}\' +\n        \'.cb-input:disabled{opacity:.6;cursor:not-allowed}\' +\n        \'.cb-send{flex:none;width:40px;height:40px;border:0;border-radius:12px;background:var(--cb-accent);color:#1a2e05;cursor:pointer;display:flex;align-items:center;justify-content:center}\' +\n        \'.cb-send:hover{background:#6fae10}\' +\n        \'.cb-send:disabled{opacity:.5;cursor:not-allowed}\' +\n        \'.cb-send:focus-visible{outline:3px solid #1a2e05;outline-offset:2px}\' +\n        \'@media (max-width:480px){.cb-panel{width:calc(100vw - 24px);height:calc(100vh - 96px);max-height:none}.cb-root{bottom:80px;right:16px}.cb-root[data-pos="bottom-left"]{left:16px}}\' ;\n    ';

  // ---------------------------------------------------------------- config
  var current = typeof document !== 'undefined' ? document.currentScript : null;
  var ds = (current && current.dataset) || {};
  var scriptSrc = (current && current.src) || '';
  var defaultOrigin = '';
  try {
    defaultOrigin = scriptSrc ? new URL(scriptSrc, window.location.href).origin : window.location.origin;
  } catch (e) {
    defaultOrigin = window.location.origin;
  }

  var cfg = {
    apiUrl: (ds.apiUrl || defaultOrigin || '').replace(/\/+$/, ''),
    position: ds.position === 'bottom-left' ? 'bottom-left' : 'bottom-right',
    title: ds.title || 'Assistant',
    accent: ds.accent || '#84cc16',
    placeholder: ds.placeholder || 'Ask anything…',
    welcome: ds.welcome || 'Hi! How can I help you today?',
    maxHistory: parseInt(ds.history, 10) || 20,
  };
  if (!cfg.apiUrl) cfg.apiUrl = window.location.origin;

  var STORAGE_KEY = 'ai_chatbot_history_v1';

  // ---------------------------------------------------------------- helpers
  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function svgIcon(path, size) {
    var ns = 'http://www.w3.org/2000/svg';
    var s = document.createElementNS(ns, 'svg');
    s.setAttribute('viewBox', '0 0 24 24');
    s.setAttribute('width', size || '26');
    s.setAttribute('height', size || '26');
    s.setAttribute('fill', 'none');
    s.setAttribute('stroke', 'currentColor');
    s.setAttribute('stroke-width', '2');
    s.setAttribute('stroke-linecap', 'round');
    s.setAttribute('stroke-linejoin', 'round');
    path.forEach(function (d) {
      var p = document.createElementNS(ns, 'path');
      p.setAttribute('d', d);
      s.appendChild(p);
    });
    return s;
  }

  // ---------------------------------------------------------------- widget
  function init() {
    if (document.getElementById('ai-chatbot-widget-root')) return;

    var mount = el('div');
    mount.id = 'ai-chatbot-widget-root';
    var root = mount.attachShadow({ mode: 'open' });

    var style = el('style');
    style.textContent = STYLE;
    root.appendChild(style);

    var box = el('div', 'cb-root');
    box.setAttribute('data-pos', cfg.position);
    box.style.setProperty('--cb-accent', cfg.accent);
    root.appendChild(box);

    // launcher
    var launcher = el('button', 'cb-launcher');
    launcher.type = 'button';
    launcher.setAttribute('aria-label', 'Open chat');
    launcher.setAttribute('aria-expanded', 'false');
    var iconSlot = el('span', 'cb-icon-slot');
    iconSlot.style.display = 'inline-flex';
    iconSlot.style.alignItems = 'center';
    iconSlot.style.justifyContent = 'center';
    launcher.appendChild(iconSlot);
    var badge = el('span', 'cb-badge', '1');
    badge.style.display = 'none';
    launcher.appendChild(badge);
    box.appendChild(launcher);

    // panel
    var panel = el('div', 'cb-panel');
    panel.style.display = 'none';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', cfg.title);
    box.appendChild(panel);

    var head = el('div', 'cb-head');
    var dot = el('span', 'cb-dot');
    var titleWrap = el('div');
    var titleEl = el('div', 'cb-title', cfg.title);
    var subEl = el('div', 'cb-sub', "Don't paste secrets or customer data");
    titleWrap.appendChild(titleEl);
    titleWrap.appendChild(subEl);
    var closeBtn = el('button', 'cb-close', '×');
    closeBtn.type = 'button';
    closeBtn.setAttribute('aria-label', 'Close chat');
    head.appendChild(dot);
    head.appendChild(titleWrap);
    head.appendChild(closeBtn);
    panel.appendChild(head);

    var body = el('div', 'cb-body');
    body.setAttribute('role', 'log');
    body.setAttribute('aria-live', 'polite');
    panel.appendChild(body);

    var foot = el('div', 'cb-foot');
    var input = el('textarea', 'cb-input');
    input.rows = 1;
    input.placeholder = cfg.placeholder;
    input.setAttribute('aria-label', 'Message');
    var sendBtn = el('button', 'cb-send');
    sendBtn.type = 'button';
    sendBtn.setAttribute('aria-label', 'Send message');
    sendBtn.appendChild(svgIcon(ICON_SEND, 18));
    foot.appendChild(input);
    foot.appendChild(sendBtn);
    panel.appendChild(foot);

    document.body.appendChild(mount);

    // ------------------------------------------------------------ state
    var history = [];
    var open = false;
    var busy = false;

    function persist() {
      try {
        window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(-cfg.maxHistory)));
      } catch (e) { /* storage unavailable — non-fatal */ }
    }

    function restore() {
      try {
        var raw = window.sessionStorage.getItem(STORAGE_KEY);
        if (!raw) return;
        var parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) history = parsed.slice(-cfg.maxHistory);
      } catch (e) { /* ignore corrupt state */ }
      history.forEach(function (m) {
        appendBubble(m.role, m.content);
      });
    }

    function appendBubble(role, text, isError, sources) {
      var bubble = el('div', 'cb-msg ' + (role === 'user' ? 'cb-user' : 'cb-bot'));
      if (isError) bubble.setAttribute('data-error', 'true');

      // Parse markdown into HTML and render it properly.
      // Uses a safe, lightweight markdown parser that only handles what the
      // LLM produces: headings, bold, italic, lists, code blocks, links.
      var html = markdownToHtml(text);

      // Build a container with proper styling per element type.
      var container = el('div', 'cb-markdown');
      container.innerHTML = html;

      // Replace the raw text <p> with the parsed HTML container.
      bubble.appendChild(container);

      // Citation chips — built with textContent, never innerHTML.
      if (sources && sources.length) {
        var box = el('div', 'cb-sources');
        box.setAttribute('aria-label', 'Sources');
        sources.forEach(function (s) {
          var label = s.section ? (s.source + ' — ' + s.section) : s.source;
          box.appendChild(el('span', 'cb-src', label));
        });
        bubble.appendChild(box);
      }

      body.appendChild(bubble);
      body.scrollTop = body.scrollHeight;
      return bubble;
    }

    // ------------------------------------------------------------------
    // Markdown → HTML converter (lightweight, safe for LLM-generated text)
    // ------------------------------------------------------------------
    function markdownToHtml(text) {
      var html = text;

      // 1. Code blocks (```lang ... ```) — must be done first to avoid
      //    escaping interfering with backticks.
      html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, function (match, lang, code) {
        var langClass = lang ? ' lang-' + lang : '';
        return '<pre class="cb-code' + langClass + '"><code>' + escapeHtml(code.trim()) + '</code></pre>';
      });

      // 2. Headings (## ... through ##### ...)
      html = html.replace(/^### (.*)$/gm, '<h3>$1</h3>');
      html = html.replace(/^## (.*)$/gm, '<h2>$1</h2>');
      html = html.replace(/^# (.*)$/gm, '<h1>$1</h1>');

      // 3. Bold (**text**) and italic (*text*)
      html = html.replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>');
      html = html.replace(/\*([^*]+?)\*/g, '<em>$1</em>');

      // 4. Links ([text](url))
      html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

      // 5. Unordered lists (- or * item)
      html = html.replace(/^(\s*)[-*]\s+(.+)$/gm, function (match, indent, item) {
        var margin = indent ? 'margin-left: ' + (indent.length * 20) + 'px' : '0';
        return '<ul style="margin:0;' + margin + ';padding-left:14px;list-style-type:disc"><li>' + escapeHtml(item) + '</li></ul>';
      });

      // 6. Ordered lists (1. item)
      html = html.replace(/^(\s*)\d+\.\s+(.+)$/gm, function (match, indent, item) {
        var margin = indent ? 'margin-left: ' + (indent.length * 20) + 'px' : '0';
        return '<ol style="margin:0;' + margin + ';padding-left:14px;list-style-type:decimal"><li>' + escapeHtml(item) + '</li></ol>';
      });

      // 7. Paragraphs (wrap remaining text in <p>)
      html = html.replace(/(.+?)(?=\n\s*\n|\n*$)/gs, function (match) {
        if (match.startsWith('<h') || match.startsWith('<pre') || match.startsWith('<ol') || match.startsWith('<ul')) {
          return match;
        }
        var trimmed = match.replace(/^\s+/, '').replace(/\s+$/, '');
        if (trimmed) {
          return '<p>' + escapeHtml(trimmed) + '</p>';
        }
        return match;
      });

      return html;
    }

    // Escape HTML special characters to prevent XSS when rendering user/content.
    function escapeHtml(str) {
      return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    function showTyping() {
      var t = el('div', 'cb-typing');
      t.appendChild(el('i'));
      t.appendChild(el('i'));
      t.appendChild(el('i'));
      t.setAttribute('aria-label', 'Assistant is typing');
      body.appendChild(t);
      body.scrollTop = body.scrollHeight;
      return t;
    }

    function setBusy(next) {
      busy = next;
      sendBtn.disabled = next;
      input.disabled = next;
      launcher.setAttribute('aria-busy', String(next));
    }

    function setOffline(flag) {
      dot.setAttribute('data-offline', String(flag));
      subEl.textContent = flag ? 'Reconnecting…' : 'Typically replies instantly';
    }

    function addMessage(role, content) {
      history.push({ role: role, content: content });
      if (history.length > cfg.maxHistory) history = history.slice(-cfg.maxHistory);
      persist();
    }

    async function send() {
      var text = input.value.trim();
      if (!text || busy) return;

      appendBubble('user', text);
      addMessage('user', text);
      input.value = '';
      input.style.height = 'auto';
      setBusy(true);

      var typing = showTyping();
      try {
        var res = await fetch(cfg.apiUrl + '/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, history: history.slice(0, -1) }),
        });

        var data = null;
        try { data = await res.json(); } catch (e) { /* non-JSON body */ }

        if (!res.ok) {
          var msg = (data && data.error) || 'Something went wrong. Please try again.';
          typing.remove();
          appendBubble('assistant', msg, true);
          setOffline(true);
          return;
        }

        var reply = (data && data.reply) || '';
        typing.remove();
        if (!reply) {
          appendBubble('assistant', 'I got an empty response. Please try again.', true);
          return;
        }
        appendBubble('assistant', reply, false, data.sources);
        // feedback buttons
        var fb = el('div');
        fb.style.display = 'flex'; fb.style.gap = '6px'; fb.style.marginTop = '4px';
        var up = el('button', null, '👍'); var down = el('button', null, '👎');
        [up, down].forEach(function(b){ b.style.background='transparent'; b.style.border='1px solid #cbd5e1'; b.style.borderRadius='6px'; b.style.cursor='pointer'; b.style.padding='2px 6px'; });
        up.onclick = function(){ fetch(cfg.apiUrl+'/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({vote:'up',message:text})}); up.disabled=true; down.disabled=true; };
        down.onclick = function(){ fetch(cfg.apiUrl+'/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({vote:'down',message:text})}); up.disabled=true; down.disabled=true; };
        fb.appendChild(up); fb.appendChild(down);
        body.appendChild(fb);
        body.scrollTop = body.scrollHeight;
        addMessage('assistant', reply);
        setOffline(false);
      } catch (err) {
        typing.remove();
        appendBubble(
          'assistant',
          'Could not reach the assistant. Check your connection and try again.',
          true
        );
        setOffline(true);
      } finally {
        setBusy(false);
        if (open) input.focus();
      }
    }

    // ------------------------------------------------------------ wiring
    launcher.addEventListener('click', function () {
      open = !open;
      panel.style.display = open ? 'flex' : 'none';
      launcher.setAttribute('aria-expanded', String(open));
      launcher.querySelector('svg') && setLauncherIcon(open);
      if (open) {
        if (badge.style.display !== 'none') { badge.style.display = 'none'; badge.textContent = '0'; }
        if (!history.length) {
          appendBubble('assistant', cfg.welcome);
          addMessage('assistant', cfg.welcome);
        }
        body.scrollTop = body.scrollHeight;
        setTimeout(function () { input.focus(); }, 50);
      }
    });

    function setLauncherIcon(isOpen) {
      while (iconSlot.firstChild) iconSlot.removeChild(iconSlot.firstChild);
      iconSlot.appendChild(svgIcon(isOpen ? ICON_X : ICON_CHAT));
    }

    closeBtn.addEventListener('click', function () {
      open = false;
      panel.style.display = 'none';
      launcher.setAttribute('aria-expanded', 'false');
      setLauncherIcon(false);
      launcher.focus();
    });

    sendBtn.addEventListener('click', send);

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        send();
      } else if (e.key === 'Escape') {
        closeBtn.click();
      }
    });

    input.addEventListener('input', function () {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 110) + 'px';
    });

    // close the panel if the user clicks outside the widget (optional nicety)
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && open) closeBtn.click();
    });

    restore();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
// Deploy auto-rebuild
