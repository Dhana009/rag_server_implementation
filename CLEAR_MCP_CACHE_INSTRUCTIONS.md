# Clear MCP Cache and Re-add Server - Instructions

## Step 1: Clean Python Cache (Already Done)
✅ Python cache files have been cleaned up.

## Step 2: Clear Cursor MCP Cache

### Option A: Via Cursor Settings UI
1. Open Cursor Settings:
   - Press `Ctrl+,` (Windows/Linux) or `Cmd+,` (Mac)
   - Or: File → Preferences → Settings

2. Search for "MCP" or "Model Context Protocol"

3. Find your `rag-server` configuration:
   - Look for an entry with name like "rag-server" or "RAG Server"
   - Or check the MCP Servers section

4. Remove the server:
   - Click the trash/delete icon next to the server
   - Or remove it from the JSON configuration

5. Re-add the server:
   - Click "Add Server" or "+"
   - Use these settings:
     ```json
     {
       "name": "rag-server",
       "command": "python",
       "args": ["D:\\planning\\rag_server_implementation\\rag-server\\server.py"]
     }
     ```
   - Or use the full path to your Python executable if needed

6. Restart Cursor or reload:
   - Close and reopen Cursor
   - Or use Command Palette (`Ctrl+Shift+P`) → "MCP: Reload Servers"

### Option B: Via Settings JSON (Advanced)
1. Open Cursor Settings JSON:
   - Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
   - Type "Preferences: Open User Settings (JSON)"
   - Press Enter

2. Find the MCP configuration section:
   ```json
   {
     "mcp": {
       "servers": {
         "rag-server": {
           // ... configuration here
         }
       }
     }
   }
   ```

3. Remove the `rag-server` entry completely

4. Re-add it:
   ```json
   {
     "mcp": {
       "servers": {
         "rag-server": {
           "command": "python",
           "args": [
             "D:\\planning\\rag_server_implementation\\rag-server\\server.py"
           ],
           "env": {}
         }
       }
     }
   }
   ```

5. Save the file and restart Cursor

## Step 3: Verify Server Path

Your server path should be:
```
D:\planning\rag_server_implementation\rag-server\server.py
```

Make sure Python is in your PATH, or use the full path to Python:
```
C:\Python313\python.exe
```

## Step 4: Test the Server

After re-adding, test by:

1. **Check MCP Status:**
   - Open Command Palette (`Ctrl+Shift+P`)
   - Type "MCP: Show Server Status"
   - Look for "rag-server" in the list

2. **Test Tools:**
   - Try using `get_manifest` tool
   - Check if all 6 QUADRANTDB tools are listed:
     - `add_vector`
     - `get_vector`
     - `update_vector`
     - `delete_vector`
     - `search_similar`
     - `search_by_metadata`

3. **Run Verification Script:**
   ```bash
   cd rag-server
   python verify_server_tools.py
   ```

## Troubleshooting

### Server Not Starting
- Check Python path is correct
- Verify `server.py` exists at the specified path
- Check for errors in Cursor's MCP output panel

### Tools Not Appearing
- Make sure you removed the old server completely
- Restart Cursor after re-adding
- Check server logs in Cursor's MCP panel

### Import Errors
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check that `config.py` and other modules are accessible

## Quick Test Command

After re-adding, you can test the server directly:
```bash
cd rag-server
python server.py
```

The server should start and wait for MCP protocol messages (it won't output anything until connected).


