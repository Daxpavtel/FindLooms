const { spawn } = require('child_process');
const fs = require('fs');

const BASE_URL = 'http://127.0.0.1:5000';
const VIEWPORTS = [320, 375, 414, 768, 1024, 1280, 1440, 1920];

async function loginUser(email, password) {
  const getRes = await fetch(`${BASE_URL}/auth/login`);
  const getHtml = await getRes.text();
  const getCookie = getRes.headers.get('set-cookie');
  const initialCookie = getCookie ? getCookie.split(';')[0] : '';
  const m = getHtml.match(/name="csrf_token"[^>]*value="([^"]+)"/) || getHtml.match(/value="([^"]+)"[^>]*name="csrf_token"/);
  const body = new URLSearchParams();
  body.append('csrf_token', m[1]);
  body.append('email', email);
  body.append('password', password);
  const postRes = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'Cookie': initialCookie },
    body: body.toString(),
    redirect: 'manual'
  });
  const postCookie = postRes.headers.get('set-cookie');
  return postCookie.match(/session=([^;]+)/)[1];
}

async function audit() {
  const userCookie = await loginUser('aarav.patel@campus.edu', 'UserPass123!');
  const staffCookie = await loginUser('priya.sharma@campus.edu', 'StaffPass123!');
  const adminCookie = await loginUser('admin@campus.edu', 'AdminPass123!');

  const pages = [
    { name: 'Landing Page', path: '/', role: 'public' },
    { name: 'Sign In', path: '/auth/login', role: 'public' },
    { name: 'Register', path: '/auth/register', role: 'public' },
    { name: 'User Dashboard', path: '/auth/dashboard', role: 'user' },
    { name: 'Staff Dashboard', path: '/auth/dashboard', role: 'staff' },
    { name: 'User Profile', path: '/auth/profile', role: 'user' },
    { name: 'Lost Catalog', path: '/lost', role: 'public' },
    { name: 'Report Lost Item', path: '/lost/new', role: 'user' },
    { name: 'Lost Item Detail', path: '/lost/6ac68a8ebec95d0f694c2241', role: 'user' },
    { name: 'Possible Matches', path: '/lost/6ac68a8ebec95d0f694c2241/matches', role: 'user' },
    { name: 'Found Catalog', path: '/found', role: 'public' },
    { name: 'Register Found Item', path: '/found/new', role: 'staff' },
    { name: 'Found Item Detail', path: '/found/6ac68a8ebec95d0f694c2242', role: 'user' },
    { name: 'File Claim', path: '/claims/new?found_id=6ac68a8ebec95d0f694c2242', role: 'user' },
    { name: 'My Claims', path: '/claims/my', role: 'user' },
    { name: 'Claim Detail', path: '/claims/6ac68a8ebec95d0f694c2251', role: 'user' },
    { name: 'Claims Queue', path: '/claims/queue', role: 'staff' },
    { name: 'Claim Review', path: '/claims/6ac68a8ebec95d0f694c2251/review', role: 'staff' },
    { name: 'Claim Handover', path: '/claims/6ac68a8ebec95d0f694c2251/handover', role: 'staff' },
    { name: 'Kanban Board', path: '/kanban', role: 'staff' },
    { name: 'Map View', path: '/views/map', role: 'staff' },
    { name: 'Calendar View', path: '/views/calendar', role: 'staff' },
    { name: 'Day Schedule', path: '/views/day/2026-10-05', role: 'staff' },
    { name: 'Reports & Analytics', path: '/reports', role: 'staff' },
    { name: 'Admin Categories', path: '/admin/categories', role: 'admin' },
    { name: 'Admin Locations', path: '/admin/locations', role: 'admin' },
    { name: 'Admin Users', path: '/admin/users', role: 'admin' },
    { name: 'Admin Settings', path: '/admin/settings', role: 'admin' },
    { name: 'Admin Archive', path: '/admin/archive', role: 'admin' },
    { name: 'Admin Audit Log', path: '/admin/audit', role: 'admin' },
    { name: 'Error 403', path: '/403', role: 'public' },
    { name: 'Error 404', path: '/404', role: 'public' },
    { name: 'Error 500', path: '/500', role: 'public' },
  ];

  const chromeProc = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
    '--headless=new',
    '--disable-gpu',
    '--remote-debugging-port=9223',
    '--user-data-dir=C:\\temp\\chrome_audit_eval_after'
  ]);
  await new Promise(r => setTimeout(r, 1500));

  const findings = [];

  try {
    const versionRes = await fetch('http://127.0.0.1:9223/json/version');
    const versionData = await versionRes.json();
    const ws = new WebSocket(versionData.webSocketDebuggerUrl);
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

    let id = 1;
    function send(method, params = {}) {
      return new Promise((resolve, reject) => {
        const msgId = id++;
        const handler = (evt) => {
          const msg = JSON.parse(evt.data);
          if (msg.id === msgId) {
            ws.removeEventListener('message', handler);
            if (msg.error) reject(msg.error);
            else resolve(msg.result);
          }
        };
        ws.addEventListener('message', handler);
        ws.send(JSON.stringify({ id: msgId, method, params }));
      });
    }

    const target = await send('Target.createTarget', { url: 'about:blank' });
    const pageWs = new WebSocket(`ws://127.0.0.1:9223/devtools/page/${target.targetId}`);
    await new Promise(r => pageWs.onopen = r);

    let pageId = 1;
    function pageSend(method, params = {}) {
      return new Promise((resolve, reject) => {
        const msgId = pageId++;
        const handler = (evt) => {
          const msg = JSON.parse(evt.data);
          if (msg.id === msgId) {
            pageWs.removeEventListener('message', handler);
            if (msg.error) reject(msg.error);
            else resolve(msg.result);
          }
        };
        pageWs.addEventListener('message', handler);
        pageWs.send(JSON.stringify({ id: msgId, method, params }));
      });
    }

    await pageSend('Page.enable');
    await pageSend('Network.enable');

    for (const p of pages) {
      await pageSend('Network.clearBrowserCookies');
      let sessionVal = null;
      if (p.role === 'user') sessionVal = userCookie;
      else if (p.role === 'staff') sessionVal = staffCookie;
      else if (p.role === 'admin') sessionVal = adminCookie;

      if (sessionVal) {
        await pageSend('Network.setCookie', {
          name: 'session', value: sessionVal, domain: '127.0.0.1', path: '/', httpOnly: true
        });
      }

      const pageReport = { name: p.name, path: p.path, role: p.role, viewports: {} };

      for (const w of VIEWPORTS) {
        await pageSend('Emulation.setDeviceMetricsOverride', {
          width: w,
          height: 800,
          deviceScaleFactor: 1,
          mobile: w < 768
        });

        await pageSend('Page.navigate', { url: `${BASE_URL}${p.path}` });
        await new Promise(r => setTimeout(r, 400));

        const res = await pageSend('Runtime.evaluate', {
          expression: `(() => {
            const docEl = document.documentElement;
            const scrollWidth = docEl.scrollWidth;
            const clientWidth = docEl.clientWidth;
            const hasHScroll = scrollWidth > clientWidth;
            
            // Find overflowing elements
            const overflowing = [];
            document.querySelectorAll('*').forEach(el => {
              const r = el.getBoundingClientRect();
              if (r.right > clientWidth + 2) {
                overflowing.push({
                  tag: el.tagName.toLowerCase(),
                  class: el.className,
                  id: el.id,
                  right: Math.round(r.right),
                  width: Math.round(r.width)
                });
              }
            });

            // Tap targets below 40px
            const tinyTargets = [];
            document.querySelectorAll('button, a, input, select').forEach(el => {
              const r = el.getBoundingClientRect();
              if (r.width > 0 && r.height > 0 && (r.height < 40 || r.width < 40)) {
                tinyTargets.push({
                  text: (el.innerText || el.value || el.placeholder || el.className).trim().slice(0, 30),
                  height: Math.round(r.height),
                  width: Math.round(r.width)
                });
              }
            });

            // Tables check
            const tables = Array.from(document.querySelectorAll('table')).map(t => {
              const parent = t.parentElement;
              return {
                tableWidth: t.scrollWidth,
                parentOverflow: window.getComputedStyle(parent).overflowX,
                isWrapped: window.getComputedStyle(parent).overflowX === 'auto'
              };
            });

            // Navbar check
            const nav = document.querySelector('header');
            const navHeight = nav ? Math.round(nav.getBoundingClientRect().height) : 0;

            return {
              scrollWidth,
              clientWidth,
              hasHScroll,
              overflowingCount: overflowing.length,
              sampleOverflow: overflowing.slice(0, 3),
              tinyTargetsCount: tinyTargets.length,
              tables,
              navHeight
            };
          })()`,
          returnByValue: true
        });

        pageReport.viewports[w] = res.result ? res.result.value : null;
      }

      findings.push(pageReport);
      console.log(`Audited: ${p.name}`);
    }

    fs.writeFileSync('L:\\project\\FindLooms\\audit_after_data.json', JSON.stringify(findings, null, 2));
    console.log('Saved audit_after_data.json');

    await pageSend('Page.close').catch(() => {});
    pageWs.close();
    ws.close();
  } finally {
    chromeProc.kill();
  }
}

audit().catch(console.error);
