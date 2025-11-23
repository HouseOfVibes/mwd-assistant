# Website Contact Form Setup Guide

This guide explains how to connect your Astro website's contact form to the MWD Assistant using secure HMAC-SHA256 authentication.

## Overview

```
Website Form → Vercel API (signs request) → MWD Assistant (verifies & processes)
```

---

## Step 1: Generate a Shared Secret

Run this command to generate a secure secret:

```bash
openssl rand -hex 32
```

Save this value - you'll use it in both places.

---

## Step 2: Configure MWD Assistant

Add these environment variables to your MWD Assistant (Railway):

```env
CONTACT_WEBHOOK_SECRET=your_generated_secret_here
SLACK_NOTIFICATION_CHANNEL=your_slack_channel_id
```

---

## Step 3: Create the API Route on Your Website

Create a new file at `api/contact.js` in your Astro project:

```javascript
// api/contact.js
import crypto from 'crypto';

export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const formData = req.body;

    // Configuration
    const ASSISTANT_URL = process.env.MWD_ASSISTANT_URL;
    const WEBHOOK_SECRET = process.env.CONTACT_WEBHOOK_SECRET;

    // Validate configuration
    if (!WEBHOOK_SECRET) {
      console.error('CONTACT_WEBHOOK_SECRET not configured');
      return res.status(500).json({ error: 'Server configuration error' });
    }

    if (!ASSISTANT_URL) {
      console.error('MWD_ASSISTANT_URL not configured');
      return res.status(500).json({ error: 'Server configuration error' });
    }

    // Prepare the payload
    const payload = JSON.stringify(formData);

    // Generate HMAC-SHA256 signature
    const signature = crypto
      .createHmac('sha256', WEBHOOK_SECRET)
      .update(payload)
      .digest('hex');

    // Send to MWD Assistant
    const response = await fetch(`${ASSISTANT_URL}/api/contact`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': signature,
      },
      body: payload,
    });

    const result = await response.json();

    if (!response.ok) {
      console.error('MWD Assistant error:', result);
      return res.status(response.status).json({
        success: false,
        error: result.error || 'Failed to process form'
      });
    }

    // Return success response
    return res.status(200).json({
      success: true,
      message: 'Thank you! Your form has been submitted successfully.',
      deliverables_count: result.deliverables_count,
    });

  } catch (error) {
    console.error('Contact form error:', error);
    return res.status(500).json({
      success: false,
      error: 'Failed to process form. Please try again.'
    });
  }
}
```

---

## Step 4: Configure Vercel Environment Variables

In your Vercel project dashboard, go to Settings → Environment Variables and add:

| Variable | Value |
|----------|-------|
| `CONTACT_WEBHOOK_SECRET` | Your generated secret (same as MWD Assistant) |
| `MWD_ASSISTANT_URL` | `https://your-mwd-assistant.railway.app` |

---

## Step 5: Create Your Contact Form

Here's an example contact form component:

### HTML Form Example

```html
<form id="contact-form" class="contact-form">
  <div class="form-group">
    <label for="company_name">Company Name *</label>
    <input type="text" id="company_name" name="company_name" required />
  </div>

  <div class="form-group">
    <label for="contact_name">Your Name *</label>
    <input type="text" id="contact_name" name="contact_name" required />
  </div>

  <div class="form-group">
    <label for="contact_email">Email *</label>
    <input type="email" id="contact_email" name="contact_email" required />
  </div>

  <div class="form-group">
    <label for="phone">Phone</label>
    <input type="tel" id="phone" name="phone" />
  </div>

  <div class="form-group">
    <label for="industry">Industry</label>
    <input type="text" id="industry" name="industry" placeholder="e.g., Technology, Healthcare, Retail" />
  </div>

  <div class="form-group">
    <label for="target_audience">Target Audience</label>
    <input type="text" id="target_audience" name="target_audience" placeholder="Who are your ideal customers?" />
  </div>

  <div class="form-group">
    <label>Services Needed</label>
    <div class="checkbox-group">
      <label><input type="checkbox" name="services" value="branding" /> Branding</label>
      <label><input type="checkbox" name="services" value="website" /> Website Design</label>
      <label><input type="checkbox" name="services" value="social_media" /> Social Media</label>
      <label><input type="checkbox" name="services" value="copywriting" /> Copywriting</label>
    </div>
  </div>

  <div class="form-group">
    <label for="budget">Budget Range</label>
    <select id="budget" name="budget">
      <option value="">Select a range</option>
      <option value="under_5k">Under $5,000</option>
      <option value="5k_10k">$5,000 - $10,000</option>
      <option value="10k_25k">$10,000 - $25,000</option>
      <option value="25k_plus">$25,000+</option>
    </select>
  </div>

  <div class="form-group">
    <label for="timeline">Timeline</label>
    <select id="timeline" name="timeline">
      <option value="">Select timeline</option>
      <option value="asap">ASAP</option>
      <option value="1_month">Within 1 month</option>
      <option value="2_3_months">2-3 months</option>
      <option value="flexible">Flexible</option>
    </select>
  </div>

  <div class="form-group">
    <label for="message">Tell us about your project</label>
    <textarea id="message" name="message" rows="4" placeholder="What are your goals? Any specific requirements?"></textarea>
  </div>

  <button type="submit" id="submit-btn">Submit</button>
  <div id="form-status"></div>
</form>
```

### JavaScript Form Handler

```javascript
<script>
document.getElementById('contact-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const submitBtn = document.getElementById('submit-btn');
  const statusDiv = document.getElementById('form-status');

  // Disable button and show loading state
  submitBtn.disabled = true;
  submitBtn.textContent = 'Submitting...';
  statusDiv.textContent = '';
  statusDiv.className = '';

  try {
    // Collect form data
    const formData = new FormData(e.target);
    const data = {};

    // Process form fields
    formData.forEach((value, key) => {
      if (key === 'services') {
        // Handle multiple checkboxes
        if (!data.key_services) {
          data.key_services = [];
        }
        data.key_services.push(value);
      } else {
        data[key] = value;
      }
    });

    // Send to API
    const response = await fetch('/api/contact', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (result.success) {
      statusDiv.textContent = result.message || 'Thank you! We will be in touch soon.';
      statusDiv.className = 'success';
      e.target.reset();
    } else {
      statusDiv.textContent = result.error || 'Something went wrong. Please try again.';
      statusDiv.className = 'error';
    }
  } catch (error) {
    console.error('Form submission error:', error);
    statusDiv.textContent = 'Network error. Please check your connection and try again.';
    statusDiv.className = 'error';
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Submit';
  }
});
</script>
```

### Basic CSS Styles

```css
<style>
.contact-form {
  max-width: 600px;
  margin: 0 auto;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
}

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: normal;
}

button[type="submit"] {
  background: #000;
  color: #fff;
  padding: 1rem 2rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  width: 100%;
}

button[type="submit"]:disabled {
  background: #666;
  cursor: not-allowed;
}

#form-status {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 4px;
  text-align: center;
}

#form-status.success {
  background: #d4edda;
  color: #155724;
}

#form-status.error {
  background: #f8d7da;
  color: #721c24;
}
</style>
```

---

## Expected Payload Structure

The MWD Assistant expects this JSON structure:

```json
{
  "company_name": "Acme Corp",
  "contact_name": "John Doe",
  "contact_email": "john@acme.com",
  "phone": "555-123-4567",
  "industry": "Technology",
  "target_audience": "Small business owners",
  "key_services": ["branding", "website"],
  "brand_values": ["innovative", "trustworthy"],
  "project_goals": ["increase brand awareness", "generate leads"],
  "budget": "10k_25k",
  "timeline": "2_3_months",
  "message": "We need a complete rebrand..."
}
```

---

## What Happens When Form is Submitted

1. User submits form on your website
2. Your Vercel API signs the request with HMAC-SHA256
3. MWD Assistant receives and verifies the signature
4. MWD Assistant generates 4 AI deliverables:
   - **Branding Strategy** - Brand positioning, colors, typography
   - **Website Plan** - Sitemap, page structure, UX recommendations
   - **Social Media Strategy** - Platform recommendations, content pillars
   - **Copywriting** - Taglines, about copy, value propositions
5. You get notified on Slack with the new lead details
6. Deliverables are returned in the API response

---

## Testing

1. Deploy your website with the new API route
2. Fill out and submit the form
3. Check your Slack channel for the notification
4. Check Vercel logs if there are any errors

---

## Troubleshooting

### "Invalid signature" error
- Make sure `CONTACT_WEBHOOK_SECRET` matches in both Vercel and MWD Assistant
- Check that the secret has no extra spaces or newlines

### "Server configuration error"
- Verify all environment variables are set in Vercel
- Redeploy after adding environment variables

### Form submits but no Slack notification
- Check `SLACK_NOTIFICATION_CHANNEL` is set correctly
- Verify Slack bot has permission to post to that channel

---

## Security Notes

- The HMAC signature ensures only your website can submit to the assistant
- Secrets are never exposed to the browser
- All communication happens server-to-server
- Use HTTPS in production

---

## Support

If you have issues, check:
1. Vercel function logs
2. MWD Assistant logs (Railway)
3. Network tab in browser dev tools
