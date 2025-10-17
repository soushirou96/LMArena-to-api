# Authentication Fix for LMArena Userscript

## Issue
The userscript was failing to properly handle authentication with the LMArena website, which resulted in API calls returning 404 errors. This occurred because the LMArena platform requires an authentication cookie (`arena-auth-prod-v1`) to be present before API requests can be made.

## Root Cause
- LMArena requires users to have a valid session cookie (`arena-auth-prod-v1`) for API authentication
- The previous version of the userscript did not check for or initialize this authentication cookie
- Without this cookie, API requests to `/api/stream/retry-evaluation-session-message/...` endpoints would fail

## Solution
Added comprehensive authentication checking and initialization to the userscript (v2.5 → v2.6):

### Changes Made

1. **Cookie Detection Function** (`checkAuthCookie`)
   - Checks if the `arena-auth-prod-v1` cookie exists
   - Returns boolean indicating authentication status

2. **Authentication Initialization** (`ensureAuthentication`)
   - Automatically checks for authentication cookie on startup
   - If missing, attempts to initialize session by fetching the main page
   - Provides clear console messages about authentication status
   - Returns success/failure status

3. **Proactive Authentication Check**
   - Authentication is verified when WebSocket connection is established
   - Before each API request, authentication status is checked
   - If authentication fails, requests are rejected with clear error messages

4. **Enhanced Error Messages**
   - Users are informed when authentication is missing
   - Clear instructions provided for manual session establishment if needed

### User Experience
- **Automatic**: In most cases, authentication is handled automatically
- **Transparent**: Console logs provide visibility into the authentication process
- **Graceful Fallback**: If automatic authentication fails, users receive clear guidance

### Testing Notes
After updating the userscript:
1. Open the browser console to see authentication status logs
2. The script will report: "✅ 检测到认证 cookie，认证已完成。" if successful
3. If authentication fails, follow the console instructions to refresh or manually initiate a conversation

## Technical Details

### Authentication Cookie
- **Name**: `arena-auth-prod-v1`
- **Purpose**: Identifies the user's session with LMArena
- **Scope**: lmarena.ai domain
- **Created**: Automatically when visiting the LMArena website or initiating a conversation

### Authentication Flow
```
1. Userscript loads
2. WebSocket connects to local server
3. ensureAuthentication() is called
4. Check for arena-auth-prod-v1 cookie
5. If missing: Fetch homepage to trigger session creation
6. Wait for cookie to be set
7. Verify cookie presence
8. Mark as authenticated (or report failure)
```

### API Request Flow
```
1. Backend sends request via WebSocket
2. executeFetchAndStreamBack() receives request
3. Check isAuthenticated flag
4. If false: Call ensureAuthentication()
5. If authentication fails: Return error to backend
6. If authenticated: Proceed with API call
```

## Migration Notes
- This is a backward-compatible change
- No configuration changes required
- Existing sessions will continue to work
- Version bumped from 2.5 to 2.6

## Related Files
- `TampermonkeyScript/LMArenaApiBridge.js` - Main userscript with authentication logic
