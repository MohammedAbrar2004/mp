require("dotenv").config({path:"../../.env"});

const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
  downloadMediaMessage,
  Browsers,
} = require("@whiskeysockets/baileys");
const pino = require("pino");
const qrcode = require("qrcode-terminal");
const axios = require("axios");
const path = require("path");
const fs = require("fs");

const RECEIVER_URL = process.env.RECEIVER_URL || "http://127.0.0.1:8000/whatsapp/webhook";
const SESSION_PATH = process.env.SESSION_PATH || "./session";
const MEDIA_SIZE_LIMIT = 50 * 1024 * 1024; // 50 MB
const TARGET_CHATS = (process.env.TARGET_CHATS || "")
  .split(",")
  .map((jid) => jid.trim())
  .filter(Boolean);

const logger = pino({ level: "silent" });
const seen = new Set(); // in-process dedup

// ────────────────────────────────────────────────────────────────────────────
// Message processing
// ────────────────────────────────────────────────────────────────────────────

async function processMessage(msg) {
  const chatId = msg.key.remoteJid;
  //console.log("PROCESSING:", chatId);
  if (TARGET_CHATS.length > 0 && !TARGET_CHATS.includes(chatId))
    {
      //console.log("SKIPPED BY FILTER:", chatId);
      return;
    }
  if (seen.has(msg.key.id)) return;
  seen.add(msg.key.id);

  const body = msg.message;
  if (!body) return;

  let hasMedia = false;
  let documentMessage = null;
  let caption = "";

  console.log("Incoming message from:", msg.key.remoteJid);
  // Modern WA: document sent with caption arrives as documentWithCaptionMessage.
  if (body.documentWithCaptionMessage) {
    const inner = body.documentWithCaptionMessage.message || {};
    documentMessage = inner.documentMessage || null;
    caption = documentMessage?.caption || "";
    // const inner = body.documentWithCaptionMessage.message || {};
    // documentMessage = inner.documentMessage || null;
    // caption = inner.caption || documentMessage?.caption || "";
    hasMedia = true;
  } else if (body.documentMessage) {
    // Legacy / no-caption document (caption may be inline in the field).
    documentMessage = body.documentMessage;
    caption = documentMessage.caption || "";
    hasMedia = true;
  } else if (body.extendedTextMessage?.contextInfo?.quotedMessage?.documentMessage) {
    // Reply-to-document: the quoted document is the attachment, the reply text is the caption.
    documentMessage = body.extendedTextMessage.contextInfo.quotedMessage.documentMessage;
    caption = body.extendedTextMessage.text || "";
    hasMedia = true;
  } else if (body.conversation || body.extendedTextMessage) {
    hasMedia = false;
  } else if (body.audioMessage) {
    hasMedia = true;
  } else {
    // sticker, image, reaction, poll, etc. — not supported
    return;
  }

  // For documents: normalise so Python always sees documentMessage at top level.
  // This avoids touching the Python connector for either case.
  const payloadMessage = documentMessage
    ? { documentMessage: { ...documentMessage, caption: caption || undefined } }
    : msg.message;

  const payload = {
    key: msg.key,
    message: payloadMessage,
    messageTimestamp: msg.messageTimestamp,
    participant: msg.participant || msg.key.participant || null,
  };

  if (caption) payload.caption = caption;

  if (hasMedia) {
    try {
      const buffer = await downloadMediaMessage(msg, "buffer", {}, logger);
      if (!buffer || buffer.length === 0) {
        console.warn(`[WA] Empty media buffer — skipping media for ${msg.key.id}`);
      } else if (buffer.length > MEDIA_SIZE_LIMIT) {
        console.warn(`[WA] Media too large (${(buffer.length / 1024 / 1024).toFixed(1)} MB) — skipping media`);
      } else {
        payload._file_bytes_b64 = buffer.toString("base64");
      }
    } catch (err) {
      console.warn(`[WA] Media download failed: ${err.message}`);
    }
  }

  try {
    console.log("SENDING TO BACKEND:", RECEIVER_URL);
    await axios.post(RECEIVER_URL, payload, { timeout: 10000 });
    console.log(`[WA] Forwarded ${msg.key.id}`);
  } catch (err) {
    console.error(`[WA] Forward failed: ${err.message}`);
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Baileys connection (auto-reconnects on transient failures)
// ────────────────────────────────────────────────────────────────────────────

async function connect() {
  const sessionDir = path.resolve(SESSION_PATH);
  if (!fs.existsSync(sessionDir)) fs.mkdirSync(sessionDir, { recursive: true });

  const { state, saveCreds } = await useMultiFileAuthState(sessionDir);
  const { version } = await fetchLatestBaileysVersion();

  const sock = makeWASocket({
    auth: state,
    version,
    browser: Browsers.ubuntu("Chrome"),
    logger,
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", ({ connection, lastDisconnect, qr }) => {
    if (qr) {
      qrcode.generate(qr, { small: true });
      console.log("[WA] Scan the QR code above to authenticate");
    }
    if (connection === "open") {
      console.log("[WA] Connected — listening for messages");
    }
    if (connection === "close") {
      const code = lastDisconnect?.error?.output?.statusCode;
      const loggedOut = code === DisconnectReason.loggedOut;
      if (loggedOut) {
        console.error("[WA] Logged out. Delete ./session and restart to re-authenticate.");
      } else {
        console.log(`[WA] Connection closed (code ${code}) — reconnecting...`);
        connect();
      }
    }
  });

  sock.ev.on("messages.upsert", async ({ messages, type }) => {
    
    if (type !== "notify") return; 
    // if (!msg.message) return;
    // if (msg.key.fromMe) return;// skip history sync
    for (const msg of messages) {
      console.log("MSG:", {
      id: msg.key.id,
      chat: msg.key.remoteJid
    });
      if (!msg.key.fromMe) await processMessage(msg);
    }
  });
}

// ────────────────────────────────────────────────────────────────────────────
// Start
// ────────────────────────────────────────────────────────────────────────────

console.log(`[WA] EchoMind WhatsApp service starting`);
console.log(`[WA] Receiver:      ${RECEIVER_URL}`);
console.log(`[WA] Session:       ${path.resolve(SESSION_PATH)}`);
console.log(`[WA] Target chats:  ${TARGET_CHATS.length > 0 ? TARGET_CHATS.join(", ") : "(all chats)"}`);

connect().catch((err) => {
  console.error(`[WA] Fatal: ${err.message}`);
  process.exit(1);
});
