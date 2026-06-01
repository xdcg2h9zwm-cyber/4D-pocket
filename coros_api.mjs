/**
 * Coros API 桥接脚本 — 供 Python Bot 通过 subprocess 调用
 * 用法: node coros_api.mjs <command> [args...]
 * 支持中国区 (teamcnapi.coros.com) 和国际区 (teamapi.coros.com)
 */

import { CorosApi, isDirectory, createDirectory } from "@nyt87/crs-connect";
import { existsSync, readFileSync, writeFileSync, mkdirSync, createWriteStream } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";
import ky from "ky";

const __dirname = dirname(fileURLToPath(import.meta.url));
const TOKEN_DIR = join(__dirname, ".coros_token");
const CREDS_FILE = join(__dirname, "coros_creds.json");

const CN_API_URL = "https://teamcnapi.coros.com";
const GLOBAL_API_URL = "https://teamapi.coros.com";

// ── Helpers ──────────────────────────────────────────────────────

function loadToken(coros) {
  try {
    if (isDirectory(TOKEN_DIR)) {
      coros.loadTokenByFile(TOKEN_DIR);
      return true;
    }
  } catch (_) { /* ignore */ }
  return false;
}

function saveToken(coros) {
  if (!existsSync(TOKEN_DIR)) createDirectory(TOKEN_DIR);
  coros.exportTokenToFile(TOKEN_DIR);
}

function loadCreds() {
  try {
    if (existsSync(CREDS_FILE)) {
      return JSON.parse(readFileSync(CREDS_FILE, "utf-8"));
    }
  } catch (_) { /* ignore */ }
  return null;
}

function saveCreds(email, password, region) {
  writeFileSync(CREDS_FILE, JSON.stringify({ email, password, region }), "utf-8");
}

function output(data) {
  process.stdout.write(JSON.stringify(data));
}

function die(msg) {
  output({ ok: false, error: msg });
  process.exit(1);
}

// ── Commands ─────────────────────────────────────────────────────

async function cmd_login(args) {
  const email = args[0] || loadCreds()?.email;
  const password = args[1] || loadCreds()?.password;
  if (!email || !password) die("缺少账号或密码，用法: login <email> <password>");

  // 先尝试中国区 API（手机号默认走中国区）
  let region = 0;
  let coros = new CorosApi({ email, password });
  coros.config({ apiUrl: CN_API_URL });

  let userInfo;
  try {
    userInfo = await coros.login(email, password);
    region = userInfo.userProfile?.region || userInfo.regionId || 2;
  } catch (e) {
    // 中国区失败，回退到国际区
    coros = new CorosApi({ email, password });
    try {
      userInfo = await coros.login(email, password);
      region = userInfo.userProfile?.region || 0;
    } catch (e2) {
      die(`登录失败: ${e2.message}`);
    }
  }

  saveCreds(email, password, region);
  saveToken(coros);
  output({ ok: true, user: { region, nickname: userInfo.nickname || email } });
}

async function cmd_activities(args) {
  let page = 1, size = 10;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--page" && args[i + 1]) page = parseInt(args[++i]);
    else if (args[i] === "--size" && args[i + 1]) size = parseInt(args[++i]);
  }

  const coros = await getClient();
  try {
    const data = await coros.getActivitiesList({ page, size });
    output({ ok: true, ...data });
  } catch (e) {
    die(`获取活动列表失败: ${e.message}`);
  }
}

async function cmd_detail(args) {
  const activityId = args[0];
  if (!activityId) die("缺少 activityId");

  let sportType;
  const stIdx = args.indexOf("--sportType");
  if (stIdx >= 0 && args[stIdx + 1]) sportType = args[stIdx + 1];

  const coros = await getClient();
  try {
    const data = await coros.getActivityDetails(activityId, sportType);
    output({ ok: true, data });
  } catch (e) {
    die(`获取活动详情失败: ${e.message}`);
  }
}

async function cmd_download(args) {
  const activityId = args[0];
  if (!activityId) die("缺少 activityId");

  let fileType = "fit", outputDir = __dirname;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--type" && args[i + 1]) fileType = args[++i];
    else if (args[i] === "--output" && args[i + 1]) outputDir = args[++i];
  }

  const coros = await getClient();
  try {
    const fileUrl = await coros.getActivityDownloadFile({ activityId, fileType });
    const filename = fileUrl.split("/").pop() || `activity_${activityId}.${fileType}`;
    const filePath = join(outputDir, filename);

    // 确保输出目录存在
    if (!existsSync(outputDir)) mkdirSync(outputDir, { recursive: true });

    // 手动下载（库的 downloadFile 不等待流完成）
    const resp = await ky.get(fileUrl);
    if (resp.ok && resp.body) {
      await pipeline(Readable.fromWeb(resp.body), createWriteStream(filePath));
    } else {
      die("下载响应无效");
    }

    output({ ok: true, filePath, filename });
  } catch (e) {
    die(`下载失败: ${e.message}`);
  }
}

async function cmd_user() {
  const coros = await getClient();
  try {
    const account = await coros.getAccount();
    output({ ok: true, account });
  } catch (e) {
    die(`获取用户信息失败: ${e.message}`);
  }
}

// ── Client factory ───────────────────────────────────────────────

async function getClient() {
  const creds = loadCreds();
  if (!creds) die("未登录，请先执行: login <email> <password>");

  const isCN = creds.region === 2;
  const apiUrl = isCN ? CN_API_URL : GLOBAL_API_URL;

  // 尝试加载已缓存的 token
  const coros = new CorosApi({ email: creds.email, password: creds.password });
  coros.config({ apiUrl });

  if (loadToken(coros)) {
    // Token 加载成功，验证是否有效
    try {
      await coros.getAccount();
      return coros;
    } catch (_) { /* token 过期，重新登录 */ }
  }

  // Token 无效或不存在，重新登录
  try {
    await coros.login(creds.email, creds.password);
    saveToken(coros);
    return coros;
  } catch (e) {
    die(`登录失败: ${e.message}`);
  }
}

// ── Main ─────────────────────────────────────────────────────────

const COMMANDS = { login: cmd_login, activities: cmd_activities, detail: cmd_detail, download: cmd_download, user: cmd_user };

async function main() {
  const args = process.argv.slice(2);
  const cmd = args.shift();

  if (!cmd || !COMMANDS[cmd]) {
    die(`用法: node coros_api.mjs <${Object.keys(COMMANDS).join("|")}> [args...]`);
  }

  await COMMANDS[cmd](args);
}

main().catch((e) => {
  output({ ok: false, error: e.message });
  process.exit(1);
});
