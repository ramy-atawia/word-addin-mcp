# Novitai MCP - Word Add-in

AI-powered Word Add-in with MCP (Model Context Protocol) integration for enhanced document processing and research capabilities.

## Features

- **MCP Tool Integration**: Connect to your MCP server to access AI-powered tools
- **Document Processing**: Analyze and process Word document content using AI
- **Web Research**: Search the web and fetch content directly into your documents
- **Text Analysis**: Process and enhance text using advanced AI capabilities
- **Seamless Integration**: Works directly within Microsoft Word

## Prerequisites

- Microsoft Word (desktop or online)
- Node.js 16+ and npm
- MCP server running on `http://localhost:8000` (or configure custom URL)

## Installation & Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Start Development Server

```bash
npm run dev-server
```

This will start the web server on `https://localhost:3000`

### 3. Sideload the Add-in in Word

```bash
npm start
```

This will:
- Generate development certificates
- Start the Office Add-in debugging process
- Open Word with the add-in sideloaded

### 4. Use the Add-in

1. Open Word
2. Go to the **Home** tab
3. Click **Open Novitai MCP** button
4. The task pane will open with the MCP Tool Manager

## Available MCP Tools

The add-in integrates with your MCP server to provide access to:

- **Web Content Fetcher**: Extract and summarize content from web pages
- **Text Processor**: AI-powered text analysis and processing
- **Web Search**: Search the web for information
- **Document Analyzer**: Analyze Word document content
- **Custom Tools**: Any additional tools registered with your MCP server

## Configuration

### MCP Server URL

By default, the add-in connects to `http://localhost:8000`. To change this:

1. Go to the **Settings** tab in the add-in
2. Update the server URL as needed
3. Test the connection

### Environment Variables

Create a `.env` file in the project root:

```env
NODE_ENV=development
MCP_SERVER_URL=http://localhost:8000
```

## Development

### Project Structure

```
src/
├── taskpane/           # Main task pane components
│   ├── components/     # React components
│   ├── services/       # MCP service integration
│   ├── taskpane.html   # HTML entry point
│   └── index.tsx       # React entry point
├── commands/           # Office command functions
└── assets/             # Icons and images
```

### Key Files

- `manifest.xml` - Office Add-in manifest
- `src/taskpane/components/MCPToolManager.tsx` - Main UI component
- `src/taskpane/services/mcpService.ts` - MCP server communication
- `src/taskpane/taskpane.ts` - Word.js integration functions

### Building for Production

```bash
npm run build
```

### Linting and Code Quality

```bash
npm run lint          # Check for issues
npm run lint:fix      # Fix auto-fixable issues
npm run prettier      # Format code
```

## Troubleshooting

### Add-in Not Loading

1. Check that the development server is running on port 3000
2. Verify certificates are properly generated
3. Check Word's trust center settings

### MCP Connection Issues

1. Ensure your MCP server is running on the configured URL
2. Check network connectivity and firewall settings
3. Verify the MCP server endpoints are accessible

### Build Errors

1. Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
2. Check TypeScript compilation: `npx tsc --noEmit`
3. Verify all dependencies are properly installed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the MCP server logs
- Open an issue on GitHub

## Related Projects

- [Word Add-in MCP Backend](https://github.com/ramy-atawia/word-addin-mcp) - The MCP server this add-in connects to
- [Microsoft Office Add-ins Documentation](https://docs.microsoft.com/office/dev/add-ins/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
