const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  isJidGroup,
  downloadMediaMessage,
  Browsers,
  fetchLatestBaileysVersion,
} = require("@whiskeysockets/baileys");

const pino = require("pino");
const qrcode = require("qrcode-terminal");
const fs = require("fs");
const path = require("path");
const { targetChats, sessionPath, receiverUrl } = require("./config");
const { sendMessages } = require("./sender");

// ============================================================================
// LOGGING SETUP
// ============================================================================

const logger = pino({ level: "silent" });

// ============================================================================
// CONSTANTS
// ============================================================================

const MEDIA_SIZE_LIMIT = 50 * 1024 * 1024; // 50 MB
const MAX_CONNECTION_ATTEMPTS = 3;
const CONNECTION_ATTEMPT_BACKOFF_MS = [1000, 3000, 5000]; // 1s, 3s, 5s

// ============================================================================
// DEDUPLICATION
// ============================================================================

const processedMessageIds = new Set();

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ============================================================================
// MESSAGE PROCESSING
// ============================================================================

async function processMessage(msg) {
  try {
    // Skip if already processed
    if (processedMessageIds.has(msg.key.id)) {
      return;
    }
    processedMessageIds.add(msg.key.id);

    // Extract basic message info
    const from = msg.key.remoteJid;
    const sender = msg.key.participant || msg.key.remoteJid;
    const timestamp = msg.messageTimestamp
      ? new Date(msg.messageTimestamp * 1000).toISOString()
      : new Date().toISOString();

    // Filter by targetChats (supports both individual JIDs and group JIDs)
    // Set WHATSAPP_TARGET_CHATS=[] in .env to accept all chats
    if (targetChats.length > 0 && !targetChats.includes(from)) return;

    const isGroup = isJidGroup(from);
    const chatName = from;

    // Extract text content
    let messageText = "";
    let hasMedia = false;
    let mediaData = null;
    let mediaMimeType = null;
    let mediaFilename = null;

    // Handle different message types
    if (msg.message?.conversation) {
      messageText = msg.message.conversation;
    } else if (msg.message?.extendedTextMessage?.text) {
      messageText = msg.message.extendedTextMessage.text;
    } else if (msg.message?.imageMessage) {
      const imageMsg = msg.message.imageMessage;
      messageText = imageMsg.caption || "[Image]";
      mediaMimeType = imageMsg.mimetype;
      hasMedia = true;
    } else if (msg.message?.audioMessage) {
      const audioMsg = msg.message.audioMessage;
      messageText = "[Voice Note]";
      mediaMimeType = audioMsg.mimetype;
      hasMedia = true;
    } else if (msg.message?.videoMessage) {
      const videoMsg = msg.message.videoMessage;
      messageText = videoMsg.caption || "[Video]";
      mediaMimeType = videoMsg.mimetype;
      hasMedia = true;
    } else if (msg.message?.documentMessage) {
      const docMsg = msg.message.documentMessage;
      messageText = docMsg.caption || `[Document: ${docMsg.fileName}]`;
      mediaMimeType = docMsg.mimetype;
      mediaFilename = docMsg.fileName;
      hasMedia = true;
    } else if (msg.message?.stickerMessage) {
      messageText = "[Sticker]";
      mediaMimeType = msg.message.stickerMessage.mimetype;
      hasMedia = true;
    } else {
      // Skip messages without text
      return;
    }

    // Skip empty text
    if (!messageText || messageText.trim() === "") {
      return;
    }

    // Download media if present
    if (hasMedia && msg.message) {
      try {
        const buffer = await downloadMediaMessage(msg, "buffer", {}, logger);

        if (buffer && buffer.length <= MEDIA_SIZE_LIMIT) {
          mediaData = buffer.toString("base64");
          console.log(
            `[WhatsApp] 🔍 Downloaded media (${(buffer.length / 1024).toFixed(2)} KB)`
          );
        } else if (buffer && buffer.length > MEDIA_SIZE_LIMIT) {
          console.warn(
            `[WhatsApp] ⚠ Media too large: ${(buffer.length / (1024 * 1024)).toFixed(2)} MB > 50 MB limit`
          );
          hasMedia = false;
        }
      } catch (mediaErr) {
        console.warn(`[WhatsApp] ⚠ Failed to download media: ${mediaErr.message}`);
        hasMedia = false;
      }
    }

    // Build normalized message
    const normalizedMessage = {
      chat_name: chatName,
      message_id: msg.key.id,
      timestamp: timestamp,
      sender: sender.split("@")[0] || sender,
      message: messageText,
      is_group: isGroup,
      has_media: hasMedia && mediaData ? true : false,
      ...(hasMedia && mediaData && {
        media_data: mediaData,
        media_mime_type: mediaMimeType,
        media_filename:
          mediaFilename || `whatsapp_${msg.key.id}${getExtFromMime(mediaMimeType)}`,
      }),
    };

    console.log(`[WhatsApp] ⬇️  Message: "${messageText.substring(0, 50)}" from ${sender}`);

    // Send to FastAPI
    await sendMessages([normalizedMessage]);

  } catch (err) {
    console.error(`[WhatsApp] ❌ Error processing message: ${err.message}`);
  }
}

function getExtFromMime(mimeType) {
  const mimeToExt = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "audio/ogg": ".ogg",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "video/mp4": ".mp4",
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
      ".docx",
  };
  return mimeToExt[mimeType] || ".bin";
}

// ============================================================================
// MAIN LOOP WITH RETRY
// ============================================================================

async function main() {
  let attempts = 0;

  while (attempts < MAX_CONNECTION_ATTEMPTS) {
    try {
      attempts++;
      console.log(
        `[WhatsApp] Opening socket and attempting connection (attempt ${attempts}/${MAX_CONNECTION_ATTEMPTS})...`
      );

      const sock = await initializeSocket();

      // Keep socket alive - wait for graceful shutdown signals
      await new Promise((resolve) => {
        process.on("SIGINT", resolve);
        process.on("SIGTERM", resolve);
      });

      console.log("[WhatsApp] Shutting down gracefully...");
      await sock.end();
      break;
    } catch (err) {
      console.error(`[WhatsApp] ❌ Connection failed: ${err.message}`);

      if (attempts < MAX_CONNECTION_ATTEMPTS) {
        const backoffMs =
          CONNECTION_ATTEMPT_BACKOFF_MS[attempts - 1] ||
          CONNECTION_ATTEMPT_BACKOFF_MS[
            CONNECTION_ATTEMPT_BACKOFF_MS.length - 1
          ];
        console.log(`[WhatsApp] Retrying in ${backoffMs / 1000}s...`);
        await sleep(backoffMs);
      } else {
        console.error(`[WhatsApp] ❌ Failed to connect after ${MAX_CONNECTION_ATTEMPTS} attempts`);
        process.exit(1);
      }
    }
  }
}

// ============================================================================
// START
// ============================================================================

console.log("[WhatsApp] " + "=".repeat(66));
console.log("[WhatsApp] EchoMind WhatsApp Service (Baileys)");
console.log("[WhatsApp] " + "=".repeat(66));
console.log(`[WhatsApp] ℹ Receiver URL: ${receiverUrl}`);
console.log(`[WhatsApp] ℹ Target Chats: ${targetChats.join(", ")}`);
console.log(`[WhatsApp] ℹ Session Path: ${sessionPath}`);
console.log(`[WhatsApp] ℹ Media Size Limit: 50 MB`);
console.log("[WhatsApp] One-time QR authentication per device");
console.log("[WhatsApp] Session persists across restarts");
console.log("[WhatsApp] " + "=".repeat(66));

main().catch((err) => {
  console.error(`[WhatsApp] ❌ Fatal error: ${err.message}`);
  process.exit(1);
});

// ============================================================================
// INITIALIZATION
// ============================================================================

async function initializeSocket() {
  console.log("[WhatsApp] Initializing Baileys WhatsApp client...");

  // Ensure session directory exists
  const sessionDir = path.resolve(sessionPath);
  if (!fs.existsSync(sessionDir)) {
    fs.mkdirSync(sessionDir, { recursive: true });
    console.log(`[WhatsApp] ℹ Created session directory: ${sessionDir}`);
  }

  // Load auth state (one-time QR per device)
  const { state, saveCreds } = await useMultiFileAuthState(sessionDir);
  console.log(`[WhatsApp] ℹ Using session directory: ${sessionDir}`);

  const { version, isLatest } = await fetchLatestBaileysVersion();
  console.log(`[WhatsApp] ℹ WA version: ${version.join(".")}, latest: ${isLatest}`);

  // Create socket with browser fingerprint and current WA version
  const sock = makeWASocket({
    auth: state,
    version,
    browser: Browsers.ubuntu("Chrome"),
    logger: logger,
  });

  // ========================================================================
  // EVENT HANDLERS & CONNECTION PROMISE
  // ========================================================================

  return new Promise((resolve, reject) => {
    // Save credentials on update
    sock.ev.on("creds.update", saveCreds);

    // Connection updates
    sock.ev.on("connection.update", async (update) => {
      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        qrcode.generate(qr, { small: true });
        console.log("[WhatsApp] Scan QR code above to authenticate");
      }

      if (connection === "close") {
        const shouldReconnect =
          lastDisconnect?.error?.output?.statusCode !==
          DisconnectReason.loggedOut;

        if (shouldReconnect) {
          const statusCode = lastDisconnect?.error?.output?.statusCode;
          console.warn(
            `[WhatsApp] ⚠ Connection closed: ${lastDisconnect?.error?.message || "unknown"} (code: ${statusCode})`
          );
          console.log(`[WhatsApp] ℹ Reconnecting in next attempt...`);
          reject(new Error("Connection closed, reconnect needed"));
        } else {
          console.error("[WhatsApp] ❌ Logged out from WhatsApp. Please rescan QR code.");
          reject(new Error("Logged out from WhatsApp"));
        }
      } else if (connection === "connecting") {
        console.log("[WhatsApp] ℹ Connecting to WhatsApp...");
      } else if (connection === "open") {
        console.log("[WhatsApp] ✓ Connected to WhatsApp");
        console.log("[WhatsApp] ℹ Listening for real-time messages...");

        // Resolve promise - socket is ready
        resolve(sock);
      }
    });

    // Real-time message listener (primary mechanism)
    sock.ev.on("messages.upsert", async ({ messages, type }) => {
      if (type === "notify") {
        for (const msg of messages) {
          // Skip outgoing messages
          if (msg.key.fromMe) {
            continue;
          }

          await processMessage(msg);
        }
      }
    });

  });
}