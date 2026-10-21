const { Resend } = require("resend");

// Initialize Resend with API key from environment variable
const resend = new Resend(process.env.RESEND_API_KEY);

// The signup form is served from the site itself, so cross-origin requests are
// never needed. Anything sent from another origin is rejected.
const ALLOWED_ORIGINS = ["https://cigarettecard.club"];

function respond(statusCode, body) {
  return { statusCode, body: JSON.stringify(body) };
}

// Ask Cloudflare whether the Turnstile token from the form is genuine.
async function passesBotCheck(token, ip) {
  const params = { secret: process.env.TURNSTILE_SECRET_KEY, response: token };
  if (ip) params.remoteip = ip;
  const response = await fetch(
    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
    { method: "POST", body: new URLSearchParams(params) },
  );
  const result = await response.json();
  return result.success === true;
}

exports.handler = async function (event, context) {
  // Make sure this is a POST request
  if (event.httpMethod !== "POST") {
    return respond(405, { error: "Method not allowed" });
  }

  if (!ALLOWED_ORIGINS.includes(event.headers.origin)) {
    return respond(403, { error: "Forbidden" });
  }

  const success = respond(200, {
    success: true,
    message: "Subscription successful! Check your email for confirmation.",
  });

  try {
    // Parse JSON body (since we're only sending JSON now)
    const body = JSON.parse(event.body);
    const email = body.email;

    // The "website" field is hidden from people, so only bots fill it in.
    // Pretend it worked so they don't learn to skip it.
    if (body.website) {
      return success;
    }

    // Validate email (basic validation)
    if (!email || !email.includes("@")) {
      return respond(400, { error: "Please provide a valid email address" });
    }

    if (!process.env.TURNSTILE_SECRET_KEY) {
      console.error("TURNSTILE_SECRET_KEY is not set; refusing signups");
      return respond(500, { error: "Signups are temporarily unavailable" });
    }
    const ip = event.headers["x-nf-client-connection-ip"];
    if (!body.turnstileToken || !(await passesBotCheck(body.turnstileToken, ip))) {
      return respond(403, { error: "The bot check failed" });
    }

    // Send confirmation email
    const confirmationResponse = await resend.emails.send({
      from: process.env.FROM_EMAIL || "cards@cigarettecard.club",
      to: email,
      subject: "Welcome to Cigarette Card Club!",
      html: `
        <html>
        <head>
          <title>Welcome to the Cigarette Card Club!</title>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
            h1 { color: #7c3c21; }
            .footer { font-size: 14px; margin-top: 40px; color: #777; text-align: center; }
          </style>
        </head>
        <body>
          <h1>Welcome to the Cigarette Card Club!</h1>
          <p>Thank you for subscribing to our daily cigarette card emails!</p>
          <p>Starting tomorrow, you'll receive a beautiful vintage cigarette card in your inbox every day.</p>
          <p>Cigarette cards were collectible cards included in cigarette packages between the 1870s and 1940s, covering various subjects from sports and nature to science and history.</p>
          <p>We hope these little pieces of history bring a smile to your day!</p>
          <div class="footer">
            <p>© cigarettecard.club - To unsubscribe, simply reply to any of our emails.</p>
          </div>
        </body>
        </html>
      `,
    });

    // Add email to Resend audience if configured
    try {
      if (process.env.RESEND_AUDIENCE_ID) {
        await resend.contacts.create({
          email: email,
          first_name: "",
          last_name: "",
          audience_id: process.env.RESEND_AUDIENCE_ID,
          unsubscribed: false,
        });
      }
    } catch (contactError) {
      console.error("Error adding contact to Resend:", contactError);
      // Continue - don't fail the whole function if this part doesn't work
    }

    return success;
  } catch (error) {
    console.error("Function error:", error);
    return respond(500, { error: `Server error: ${error.message}` });
  }
};
