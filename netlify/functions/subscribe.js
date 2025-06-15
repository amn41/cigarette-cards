const { Resend } = require("resend");

// Initialize Resend with API key from environment variable
const resend = new Resend(process.env.RESEND_API_KEY);

exports.handler = async function (event, context) {
  // Set CORS headers
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  };

  // Handle preflight requests
  if (event.httpMethod === "OPTIONS") {
    return {
      statusCode: 200,
      headers,
      body: "",
    };
  }

  // Make sure this is a POST request
  if (event.httpMethod !== "POST") {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: "Method not allowed" }),
    };
  }

  try {
    // Parse JSON body (since we're only sending JSON now)
    const body = JSON.parse(event.body);
    const email = body.email;

    // Validate email (basic validation)
    if (!email || !email.includes("@")) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: "Please provide a valid email address" }),
      };
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

    // Return success response (JSON instead of redirect)
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        message: "Subscription successful! Check your email for confirmation.",
      }),
    };
  } catch (error) {
    console.error("Function error:", error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ error: `Server error: ${error.message}` }),
    };
  }
};
