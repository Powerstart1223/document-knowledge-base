# Testing Guide - UX Improvements Update

## Quick Start Testing

### 1. First-Time User Experience

**Test the complete onboarding flow:**

```bash
# Start fresh (optional - to simulate first-time user)
# Delete users.db and chroma_db/ if you want to test from scratch

# Run the app
streamlit run streamlit_app.py
```

**Expected Flow:**
1. See clean login page (no "v2.0" anywhere)
2. Log in with demo credentials (in expandable section):
   - Email: `admin@lawfirm.com`
   - Password: `Admin123!`
3. **First-run wizard appears automatically** (if no LLM configured)
4. Choose OpenAI or Ollama
5. Enter API key or configure Ollama
6. Click "Save & Continue"
7. Main app appears with helpful empty states

---

## Detailed Test Scenarios

### Scenario 1: OpenAI Setup (New User)

**Steps:**
1. Clear browser cache or use incognito
2. Log in with admin credentials
3. Onboarding wizard appears
4. Select "OpenAI (Recommended for cloud)"
5. Enter a test API key starting with "sk-"
6. Verify green checkmark appears: "✅ API key format looks valid!"
7. Click "Save & Continue"
8. App loads with main interface

**Verify:**
- ✅ Onboarding wizard is welcoming and clear
- ✅ API key validation works in real-time
- ✅ Settings are saved correctly
- ✅ Wizard doesn't appear again this session

---

### Scenario 2: Ollama Setup (New User)

**Prerequisites:** Ollama installed and running

**Steps:**
1. Log in
2. Onboarding wizard appears
3. Select "Ollama (Local only)"
4. If Ollama running: See "✅ Ollama detected and running!"
5. Click "Use Ollama"
6. App loads

**Verify:**
- ✅ Ollama detection works
- ✅ Clear instructions if Ollama not running
- ✅ Links to ollama.com are present

---

### Scenario 3: Skip Onboarding

**Steps:**
1. Log in
2. Onboarding wizard appears
3. Click "Skip for Now"
4. Main app loads
5. See error banner about LLM not configured

**Verify:**
- ✅ Skip button works
- ✅ Error message is clear and helpful
- ✅ Instructions tell user how to fix it

---

### Scenario 4: Chat with Empty Database

**Steps:**
1. Log in (with LLM configured)
2. Go to "💬 Chat Q&A" tab
3. No documents uploaded yet

**Verify:**
- ✅ See large 📚 icon
- ✅ "No Documents Yet" heading
- ✅ 3-step visual guide (Upload → Process → Ask)
- ✅ Clean, not confusing

---

### Scenario 5: Document Generation (No LLM)

**Steps:**
1. Log in without configuring LLM
2. Skip onboarding
3. Go to "📝 Generate Document" tab

**Verify:**
- ✅ Red error card appears
- ✅ Step-by-step fix instructions
- ✅ Links to Settings tab
- ✅ Alternative options mentioned

---

### Scenario 6: Settings - LLM Configuration

**Steps:**
1. Log in
2. Go to Settings → 🤖 LLM Provider tab

**Verify:**
- ✅ Clear section headers
- ✅ Radio buttons show "🏠 Ollama (Free, runs locally)" and "☁️ OpenAI (Cloud-based, paid API)"
- ✅ Help text is helpful, not technical
- ✅ Validation feedback works
- ✅ Save button works and shows success message

---

### Scenario 7: Settings - Integrations

**Steps:**
1. Go to Settings → 🔌 Integrations tab

**Verify:**
- ✅ Only SEC EDGAR shown (no Westlaw/LexisNexis)
- ✅ Clear explanation of what SEC EDGAR does
- ✅ Help text for User-Agent field
- ✅ Clean, uncluttered layout

---

### Scenario 8: Mobile Experience

**Steps:**
1. Open app on mobile device or use Chrome DevTools mobile emulation
2. Test login, chat, and document generation

**Verify:**
- ✅ Login page fits on screen
- ✅ Buttons are touch-friendly
- ✅ Input fields don't cause zoom on iOS
- ✅ Text is readable
- ✅ Navigation works
- ✅ No horizontal scrolling

---

### Scenario 9: Error Messages (Ollama Not Running)

**Steps:**
1. Configure app to use Ollama
2. Stop Ollama service
3. Try to use chat or document generation

**Verify:**
- ✅ Clear error: "⚠️ Ollama Not Running"
- ✅ Step-by-step fix instructions:
  - Install link
  - Terminal commands
  - Refresh instruction
- ✅ Alternative: "Switch to OpenAI"

---

### Scenario 10: Error Messages (OpenAI Key Missing)

**Steps:**
1. Configure app to use OpenAI
2. Don't enter API key (or enter invalid key)
3. Try to use chat or document generation

**Verify:**
- ✅ Clear error: "⚠️ OpenAI API Key Required"
- ✅ Step-by-step fix instructions:
  - Link to OpenAI Platform
  - Where to enter key
  - How to save it
- ✅ Alternative: "Install Ollama"

---

## Visual Checks

### Overall Interface
- [ ] No "v2.0" visible anywhere
- [ ] No developer jargon ("LLM" → "AI Provider", etc.)
- [ ] Icons used consistently (🤖, 📄, 💬, 📝, ⚙️)
- [ ] Color scheme is professional (navy + gold)
- [ ] Spacing and padding looks good
- [ ] Cards and containers have proper shadows
- [ ] Buttons are prominent and clear

### Typography
- [ ] Headers are clear hierarchy
- [ ] Body text is readable
- [ ] Help text is subtle but accessible
- [ ] Code snippets use monospace font
- [ ] Links are underlined or colored

### Animations
- [ ] Fade-in animations smooth
- [ ] Hover effects work
- [ ] No jarring transitions
- [ ] Spinners appear during loading

---

## Functional Tests

### Document Upload
- [ ] Upload PDF file
- [ ] Upload DOCX file
- [ ] Upload TXT file
- [ ] Select document category
- [ ] Click "Process Documents"
- [ ] See progress indicator
- [ ] See success message

### Chat Q&A
- [ ] Type question
- [ ] Press Enter
- [ ] See spinner
- [ ] Get answer with sources
- [ ] Sources are clickable/visible
- [ ] Chat history persists
- [ ] Clear chat button works

### Document Generation
- [ ] Select document type
- [ ] Fill in form fields
- [ ] Checkbox for SEC EDGAR works
- [ ] Click "Generate Document"
- [ ] See spinner (may take 30-60 sec)
- [ ] Preview appears
- [ ] Download button works
- [ ] Downloaded .docx opens correctly

### Settings
- [ ] LLM settings save correctly
- [ ] Provider switch works
- [ ] Model selection works
- [ ] API key saves
- [ ] SEC EDGAR settings save

### Authentication
- [ ] Login works
- [ ] Registration works
- [ ] Password validation works
- [ ] Logout works
- [ ] Session persists on refresh

### Admin Panel
- [ ] Admin can see all users
- [ ] Toggle active/inactive works
- [ ] Change role works
- [ ] Can't modify own account

---

## Performance Checks

- [ ] App loads in <3 seconds
- [ ] Chat response in <10 seconds (with small docs)
- [ ] Document generation in <60 seconds
- [ ] No memory leaks after extended use
- [ ] File uploads process reasonably fast

---

## Browser Compatibility

Test in:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile Safari (iOS)
- [ ] Mobile Chrome (Android)

---

## Accessibility

- [ ] Keyboard navigation works
- [ ] Tab order makes sense
- [ ] Forms have proper labels
- [ ] Error messages are clear
- [ ] Color contrast is sufficient
- [ ] Screen reader friendly (test with NVDA/JAWS if possible)

---

## Regression Tests

Make sure we didn't break anything:

- [ ] Existing users can still log in
- [ ] Existing documents still accessible
- [ ] ChromaDB collections still work
- [ ] Admin functions still work
- [ ] All original features still functional

---

## Known Limitations (Expected Behavior)

These are NOT bugs:

1. **Ollama requires local installation** - Can't run on Streamlit Cloud
2. **OpenAI requires API key** - Users must provide their own
3. **First model download slow** - ChromaDB downloads sentence-transformers (2-3 min first time)
4. **LLM generation takes time** - 30-60 seconds normal for document generation
5. **Data is ephemeral on free Streamlit Cloud** - Use paid tier for persistence

---

## Success Criteria

✅ **All tests pass**
✅ **No console errors**
✅ **UX feels intuitive**
✅ **New users can get started easily**
✅ **Error messages are helpful**
✅ **Mobile experience is good**
✅ **No "v2.0" or technical jargon visible to users**

---

## Rollback Plan

If issues are found:

```bash
# Restore from git (if using version control)
git checkout HEAD~1 streamlit_app.py auth_ui.py styles.py

# Or manually:
# 1. Restore backup of modified files
# 2. Restart Streamlit
```

---

## Support Resources

If you encounter issues:

1. Check browser console for JavaScript errors
2. Check terminal for Python errors
3. Verify all dependencies installed: `pip install -r requirements.txt`
4. Clear Streamlit cache: `streamlit cache clear`
5. Check Ollama is running: `curl http://localhost:11434/api/tags`
6. Verify OpenAI key: Check it starts with `sk-`

---

## Feedback Collection

After testing, note:

- **What works well:** ________________
- **What's confusing:** ________________
- **What's missing:** ________________
- **Mobile experience:** ________________
- **Overall impression:** ________________
