const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'http://127.0.0.1:5000';
const VIEWPORTS = [
  { name: '375px', width: 375, height: 812, mobile: true },
  { name: '768px', width: 768, height: 1024, mobile: false },
  { name: '1440px', width: 1440, height: 900, mobile: false },
];

async function loginUser(email, password) {
  const getRes = await fetch(`${BASE_URL}/auth/login`);
  const getHtml = await getRes.text();
  const getCookie = getRes.headers.get('set-cookie');
  let initialCookie = '';
  if (getCookie) {
    initialCookie = getCookie.split(';')[0];
  }

  const m = getHtml.match(/name="csrf_token"[^>]*value="([^"]+)"/) ||
            getHtml.match(/value="([^"]+)"[^>]*name="csrf_token"/);
  if (!m) throw new Error('No CSRF token found in login page');
  const csrfToken = m[1];

  const body = new URLSearchParams();
  body.append('csrf_token', csrfToken);
  body.append('email', email);
  body.append('password', password);

  const postRes = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Cookie': initialCookie
    },
    body: body.toString(),
    redirect: 'manual'
  });

  const postCookie = postRes.headers.get('set-cookie');
  if (!postCookie) throw new Error(`Login failed for ${email}`);
  const sessionMatch = postCookie.match(/session=([^;]+)/);
  if (!sessionMatch) throw new Error(`No session cookie in response for ${email}`);
  return sessionMatch[1];
}

async function main() {
  const mode = process.argv[2] || 'before';
  const outDir = path.join('L:', 'project', 'FindLooms', 'screenshots', mode);
  fs.mkdirSync(outDir, { recursive: true });

  console.log(`=== Starting screenshot capture for: ${mode} ===`);

  // Obtain session cookies
  console.log('Obtaining auth session cookies...');
  const userCookie = await loginUser('aarav.patel@campus.edu', 'UserPass123!');
  const staffCookie = await loginUser('priya.sharma@campus.edu', 'StaffPass123!');
  const adminCookie = await loginUser('admin@campus.edu', 'AdminPass123!');
  console.log('Sessions acquired successfully.');

  const pages = [
    { name: '01_landing', path: '/', role: 'public' },
    { name: '02_login', path: '/auth/login', role: 'public' },
    { name: '03_register', path: '/auth/register', role: 'public' },
    { name: '04_user_dashboard', path: '/auth/dashboard', role: 'user' },
    { name: '05_staff_dashboard', path: '/auth/dashboard', role: 'staff' },
    { name: '06_profile', path: '/auth/profile', role: 'user' },
    { name: '07_lost_catalog', path: '/lost', role: 'public' },
    { name: '08_lost_create', path: '/lost/new', role: 'user' },
    { name: '09_lost_detail', path: '/lost/6ac68a8ebec95d0f694c2241', role: 'user' },
    { name: '10_lost_matches', path: '/lost/6ac68a8ebec95d0f694c2241/matches', role: 'user' },
    { name: '11_found_catalog', path: '/found', role: 'public' },
    { name: '12_found_create', path: '/found/new', role: 'staff' },
    { name: '13_found_detail', path: '/found/6ac68a8ebec95d0f694c2242', role: 'user' },
    { name: '14_claim_create', path: '/claims/new?found_id=6ac68a8ebec95d0f694c2242', role: 'user' },
    { name: '15_my_claims', path: '/claims/my', role: 'user' },
    { name: '16_claim_detail', path: '/claims/6ac68a8ebec95d0f694c2251', role: 'user' },
    { name: '17_claims_queue', path: '/claims/queue', role: 'staff' },
    { name: '18_claim_review', path: '/claims/6ac68a8ebec95d0f694c2251/review', role: 'staff' },
    { name: '19_claim_handover', path: '/claims/6ac68a8ebec95d0f694c2251/handover', role: 'staff' },
    { name: '20_kanban_board', path: '/kanban', role: 'staff' },
    { name: '21_map_view', path: '/views/map', role: 'staff' },
    { name: '22_calendar_view', path: '/views/calendar', role: 'staff' },
    { name: '23_day_schedule', path: '/views/day/2026-10-05', role: 'staff' },
    { name: '24_reports_analytics', path: '/reports', role: 'staff' },
    { name: '25_admin_categories', path: '/admin/categories', role: 'admin' },
    { name: '26_admin_locations', path: '/admin/locations', role: 'admin' },
    { name: '27_admin_users', path: '/admin/users', role: 'admin' },
    { name: '28_admin_settings', path: '/admin/settings', role: 'admin' },
    { name: '29_admin_archive', path: '/admin/archive', role: 'admin' },
    { name: '30_admin_audit', path: '/admin/audit', role: 'admin' },
    { name: '31_error_403', path: '/403', role: 'public' },
    { name: '32_error_404', path: '/404', role: 'public' },
    { name: '33_error_500', path: '/500', role: 'public' }
  ];

  const chromePath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const chromeProc = spawn(chromePath, [
    '--headless=new',
    '--disable-gpu',
    '--remote-debugging-port=9222',
    '--user-data-dir=C:\\temp\\chrome_audit_profile'
  ]);

  await new Promise(r => setTimeout(r, 1500));

  try {
    const versionRes = await fetch('http://127.0.0.1:9222/json/version');
    const versionData = await versionRes.json();
    console.log('Connected to Chrome:', versionData.Browser);

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

    for (const vp of VIEWPORTS) {
      console.log(`\n--- Capturing viewport: ${vp.name} (${vp.width}x${vp.height}) ---`);

      // Create a tab
      const target = await send('Target.createTarget', { url: 'about:blank' });
      const pageWs = new WebSocket(`ws://127.0.0.1:9222/devtools/page/${target.targetId}`);
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

      await pageSend('Emulation.setDeviceMetricsOverride', {
        width: vp.width,
        height: vp.height,
        deviceScaleFactor: 1,
        mobile: vp.mobile
      });

      for (const p of pages) {
        // Clear cookies and set role cookie
        await pageSend('Network.clearBrowserCookies');

        let sessionVal = null;
        if (p.role === 'user') sessionVal = userCookie;
        else if (p.role === 'staff') sessionVal = staffCookie;
        else if (p.role === 'admin') sessionVal = adminCookie;

        if (sessionVal) {
          await pageSend('Network.setCookie', {
            name: 'session',
            value: sessionVal,
            domain: '127.0.0.1',
            path: '/',
            httpOnly: true
          });
        }

        const fullUrl = `${BASE_URL}${p.path}`;
        await pageSend('Page.navigate', { url: fullUrl });
        await new Promise(r => setTimeout(r, 600));

        // Evaluate scroll overflow to detect horizontal scrolling!
        const evalRes = await pageSend('Runtime.evaluate', {
          expression: `({
            scrollWidth: document.documentElement.scrollWidth,
            clientWidth: document.documentElement.clientWidth,
            hasHScroll: document.documentElement.scrollWidth > document.documentElement.clientWidth
          })`,
          returnByValue: true
        });

        if (evalRes && evalRes.result && evalRes.result.value) {
          const val = evalRes.result.value;
          if (val.hasHScroll) {
            console.warn(`[OVERFLOW WARNING] Page ${p.name} at ${vp.name}: scrollWidth=${val.scrollWidth} > clientWidth=${val.clientWidth}`);
          }
        }

        const screenshot = await pageSend('Page.captureScreenshot', {
          format: 'png',
          captureBeyondViewport: false
        });

        const filePath = path.join(outDir, `${p.name}_${vp.name}.png`);
        fs.writeFileSync(filePath, Buffer.from(screenshot.data, 'base64'));
        process.stdout.write(`.` );
      }

      await pageSend('Page.close').catch(() => {});
      pageWs.close();
    }

    ws.close();
    console.log(`\n=== Capture completed for all pages at 375px, 768px, and 1440px! ===`);
  } finally {
    chromeProc.kill();
  }
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
