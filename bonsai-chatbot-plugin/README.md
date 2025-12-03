# Bonsai Chatbot WordPress Plugin

A WordPress plugin that integrates an Ollama-powered chatbot into your WooCommerce shop. Provides customer support, product information, and bonsai care advice through an AI assistant.

## Features

- 💬 **Floating Chat Widget** - Clean, modern chat interface in bottom-right corner
- 🤖 **AI-Powered Responses** - Uses Ollama LLM for intelligent conversations
- 📚 **RAG Support** - Retrieval-Augmented Generation for accurate product/care information
- 🔒 **HTTP Basic Auth** - Secure API communication
- ⚙️ **Admin Settings** - Easy configuration through WordPress admin panel
- 📱 **Responsive Design** - Works on desktop and mobile devices
- 🎨 **Custom Styling** - Beautiful gradient purple theme

## Installation

### Method 1: Manual Upload (Recommended)

1. **Upload Plugin Files**
   ```bash
   # On your local machine, create a zip file
   cd bonsai-chatbot-plugin
   zip -r bonsai-chatbot.zip .
   ```

2. **Install in WordPress**
   - Go to WordPress Admin → Plugins → Add New
   - Click "Upload Plugin"
   - Choose `bonsai-chatbot.zip`
   - Click "Install Now"
   - Click "Activate Plugin"

### Method 2: Direct Upload via SSH/kubectl

1. **Copy plugin to WordPress container**
   ```bash
   # Create zip on local machine
   cd /home/alex/repos/homelab-demo
   zip -r bonsai-chatbot.zip bonsai-chatbot-plugin/

   # Copy to WordPress pod
   kubectl cp bonsai-chatbot.zip wordpress/wordpress-<pod-name>:/tmp/

   # Extract in WordPress plugins directory
   kubectl exec -n wordpress deployment/wordpress -- unzip /tmp/bonsai-chatbot.zip -d /var/www/html/wp-content/plugins/

   # Set proper permissions
   kubectl exec -n wordpress deployment/wordpress -- chown -R www-data:www-data /var/www/html/wp-content/plugins/bonsai-chatbot-plugin
   ```

2. **Activate in WordPress**
   - Go to WordPress Admin → Plugins
   - Find "Bonsai Chatbot"
   - Click "Activate"

### Method 3: WP-CLI (Advanced)

```bash
# Copy plugin files to container
kubectl cp bonsai-chatbot-plugin wordpress/wordpress-<pod-name>:/var/www/html/wp-content/plugins/

# Activate via WP-CLI
kubectl exec -n wordpress deployment/wordpress -- wp plugin activate bonsai-chatbot --allow-root
```

## Configuration

1. **Access Settings**
   - Go to WordPress Admin → Settings → Bonsai Chatbot

2. **Configure API Connection**
   - **Chatbot API URL**: `https://chatbot.k8s-demo.de`
   - **API Username**: Your HTTP Basic Auth username (if required)
   - **API Password**: Your HTTP Basic Auth password (if required)
   - **Enable RAG**: ✅ Check to use knowledge base
   - **Welcome Message**: Customize the greeting message

3. **Save Settings**
   - Click "Save Changes"

4. **Test Chatbot**
   - Visit your shop homepage: https://wordpress.k8s-demo.de
   - Look for purple chat button in bottom-right corner
   - Click to open chat and test a message

## Usage

### For Customers

1. Click the purple chat button in bottom-right corner
2. Type a question about:
   - Bonsai care instructions
   - Product information
   - Shipping and delivery
   - Order status
   - General inquiries
3. Receive instant AI-powered responses

### Example Questions

- "What's the difference between a Juniper and a Ficus bonsai?"
- "How often should I water my bonsai?"
- "Do you ship to the United States?"
- "What tools do I need as a beginner?"
- "What's included in the starter kit?"

## API Integration

The plugin communicates with the Ollama chatbot API using:

- **Endpoint**: `POST /chat`
- **Authentication**: HTTP Basic Auth (optional)
- **Request Format**:
  ```json
  {
    "message": "User's question",
    "use_rag": true,
    "top_k": 5,
    "system_prompt": "You are a helpful assistant for a bonsai shop..."
  }
  ```
- **Response Format**:
  ```json
  {
    "response": "AI's answer",
    "model": "llama3.2:3b",
    "sources": ["Source 1", "Source 2"]
  }
  ```

## Troubleshooting

### Chat Widget Not Appearing

1. **Clear Cache**
   - Clear WordPress cache (if using cache plugin)
   - Clear browser cache (Ctrl+Shift+R)

2. **Check Plugin Activation**
   - Go to Plugins page
   - Ensure "Bonsai Chatbot" is activated

3. **Check JavaScript Console**
   - Open browser DevTools (F12)
   - Check Console tab for errors

### "Failed to connect to chatbot" Error

1. **Verify API URL**
   - Settings → Bonsai Chatbot
   - Ensure URL is `https://chatbot.k8s-demo.de`
   - No trailing slash

2. **Check API Credentials**
   - Verify username/password if API requires auth
   - Test API directly: `curl https://chatbot.k8s-demo.de/health`

3. **Check Network**
   - Ensure WordPress can reach chatbot API
   - Check for firewall/network restrictions

### Slow Responses

1. **Check API Performance**
   - Test API response time directly
   - Monitor Ollama container resources

2. **Optimize RAG**
   - Reduce `top_k` value in code
   - Disable RAG if knowledge base not needed

## File Structure

```
bonsai-chatbot-plugin/
├── bonsai-chatbot.php          # Main plugin file
├── assets/
│   ├── css/
│   │   └── chatbot.css         # Widget styles
│   └── js/
│       └── chatbot.js          # Widget JavaScript
└── README.md                   # This file
```

## Customization

### Change Colors

Edit `assets/css/chatbot.css`:

```css
/* Change gradient colors */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Change to different colors, e.g., green */
background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);
```

### Modify Welcome Message

Go to Settings → Bonsai Chatbot → Welcome Message

Or edit directly in code:
```php
// In bonsai-chatbot.php
$system_prompt = "You are a helpful assistant for a bonsai shop...";
```

### Adjust Chat Position

Edit `assets/css/chatbot.css`:

```css
#bonsai-chatbot-container {
    bottom: 20px;  /* Distance from bottom */
    right: 20px;   /* Distance from right */
}

/* For left side, use: */
/* left: 20px; */
```

## Development

### Testing Locally

1. Install on local WordPress:
   ```bash
   cd /path/to/wordpress/wp-content/plugins/
   ln -s /home/alex/repos/homelab-demo/bonsai-chatbot-plugin bonsai-chatbot
   ```

2. Activate plugin in WordPress admin

3. Configure settings to point to local or staging chatbot API

### Building for Production

```bash
# Create deployment zip
cd /home/alex/repos/homelab-demo
zip -r bonsai-chatbot-v1.0.0.zip bonsai-chatbot-plugin/ -x "*.git*" -x "*.DS_Store"
```

## Security

- ✅ Nonce verification for AJAX requests
- ✅ Input sanitization and validation
- ✅ XSS protection with escapeHtml()
- ✅ HTTP Basic Auth support
- ✅ WordPress capabilities checking
- ⚠️ Store API credentials securely
- ⚠️ Use HTTPS for all API communication

## Support

For issues or questions:
- Check WordPress error logs: `wp-content/debug.log`
- Check Ollama chatbot logs: `kubectl logs -n <namespace> deployment/chatbot`
- Review API documentation: https://chatbot.k8s-demo.de/docs

## License

GPL v2 or later

## Credits

Developed for Bonsai Garten demo shop integrating Ollama LLM chatbot with WooCommerce.

## Changelog

### Version 1.0.0 (2025-11-28)
- Initial release
- Floating chat widget
- RAG support
- HTTP Basic Auth
- Admin settings page
- Responsive design
