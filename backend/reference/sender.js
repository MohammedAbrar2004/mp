const axios = require("axios");
const { receiverUrl } = require("./config");

/**
 * POST a batch of messages to the Python receiver.
 * @param {Array} messages - Array of message objects
 * @returns {Promise<void>}
 */
async function sendMessages(messages) {
  if (!messages || messages.length === 0) {
    return;
  }

  try {
    const response = await axios.post(
      `${receiverUrl}/ingest/whatsapp`,
      { messages },
      {
        headers: { "Content-Type": "application/json" },
        timeout: 10000,
      }
    );

    console.log(`[Sender] Posted ${messages.length} messages → ${response.status}`);
  } catch (err) {
    if (err.response) {
      console.error(
        `[Sender] Receiver error: ${err.response.status} — ${JSON.stringify(err.response.data)}`
      );
    } else {
      console.error(`[Sender] Failed to reach receiver: ${err.message}`);
    }
  }
}

module.exports = { sendMessages };
