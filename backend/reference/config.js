require("dotenv").config({ path: "../../.env" });

module.exports = {
  targetChats: JSON.parse(process.env.WHATSAPP_TARGET_CHATS || "[]"),
  pollIntervalMinutes: parseInt(process.env.WHATSAPP_POLL_INTERVAL_MINUTES || "15", 10),
  sessionPath: process.env.WHATSAPP_SESSION_PATH || "./session",
  receiverUrl: `http://${process.env.RECEIVER_HOST || "127.0.0.1"}:${process.env.RECEIVER_PORT || "8000"}`,
};
