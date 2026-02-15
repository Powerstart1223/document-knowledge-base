# Migration Guide: v1.0 → v2.0

This guide helps you upgrade from the single-user v1.0 to the multi-user v2.0 with authentication.

## Overview of Changes

### Breaking Changes
- **Authentication Required:** All users must now log in to access the application
- **Per-User Data:** Document collections are now isolated per user
- **New Dependencies:** Added `bcrypt` for password hashing

### New Features
- Multi-user support with user registration and login
- Admin panel for user management
- Modern, professional UI with improved styling
- Per-user data isolation for security
- Role-based access control

## Migration Steps

### Option 1: Fresh Start (Recommended for Most Users)

This is the simplest approach if you don't have critical data in v1.0.

1. **Backup existing data** (optional):
   ```bash
   # Backup your old ChromaDB
   cp -r chroma_db chroma_db_v1_backup

   # Backup uploaded files
   cp -r uploads uploads_v1_backup
   ```

2. **Update code:**
   ```bash
   git pull origin main
   # Or download the new code
   ```

3. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   streamlit run streamlit_app.py
   ```

5. **First login:**
   - Email: `admin@lawfirm.com`
   - Password: `Admin123!`
   - **Change password immediately!**

6. **Re-upload your documents:**
   - Upload documents via the sidebar
   - They will be stored in your user-specific collection

### Option 2: Migrate Existing Data

If you have important documents in your v1.0 ChromaDB collection, you can migrate them to a specific user.

1. **Complete steps 1-3 from Option 1** (backup, update, install dependencies)

2. **Run the app once to create the user database:**
   ```bash
   streamlit run streamlit_app.py
   ```
   - Login with default admin credentials
   - Logout

3. **Create migration script:**

   Create a file `migrate_data.py`:

   ```python
   """
   Migrate v1.0 data to v2.0 user-specific collection.
   """
   import chromadb
   from auth import get_user_collection_name

   # Configuration
   ADMIN_USER_ID = 1  # Default admin user ID
   OLD_COLLECTION = "documents"

   def migrate():
       client = chromadb.PersistentClient(path="./chroma_db")

       # Get old collection
       try:
           old_coll = client.get_collection(OLD_COLLECTION)
       except Exception:
           print(f"No collection named '{OLD_COLLECTION}' found. Nothing to migrate.")
           return

       # Get new user-specific collection
       new_collection_name = get_user_collection_name(ADMIN_USER_ID)

       # Create new collection (if doesn't exist)
       from chromadb.utils import embedding_functions
       ef = embedding_functions.SentenceTransformerEmbeddingFunction(
           model_name="all-MiniLM-L6-v2"
       )
       new_coll = client.get_or_create_collection(
           name=new_collection_name,
           embedding_function=ef
       )

       # Get all data from old collection
       print(f"Migrating data from '{OLD_COLLECTION}' to '{new_collection_name}'...")
       all_data = old_coll.get(include=["documents", "metadatas", "embeddings"])

       if not all_data["ids"]:
           print("No data to migrate.")
           return

       # Update metadatas to include user_id
       metadatas = []
       for meta in all_data["metadatas"]:
           meta["user_id"] = ADMIN_USER_ID
           metadatas.append(meta)

       # Add to new collection
       new_coll.add(
           ids=all_data["ids"],
           documents=all_data["documents"],
           metadatas=metadatas,
           embeddings=all_data["embeddings"]
       )

       print(f"✅ Migrated {len(all_data['ids'])} chunks to user {ADMIN_USER_ID}'s collection")
       print(f"Old collection '{OLD_COLLECTION}' is still available if you need to rollback")

   if __name__ == "__main__":
       migrate()
   ```

4. **Run migration:**
   ```bash
   python migrate_data.py
   ```

5. **Verify migration:**
   - Login to the app
   - Check Database Stats in sidebar
   - Your documents should appear

6. **Optional - Clean up old collection:**
   ```python
   # Only do this if migration was successful!
   import chromadb
   client = chromadb.PersistentClient(path="./chroma_db")
   client.delete_collection("documents")
   ```

## Configuration Changes

### Environment Variables

No changes to environment variables. The same `.env` configuration works in v2.0.

### Streamlit Cloud Secrets

No changes needed. Same secrets configuration as v1.0.

## Features Comparison

| Feature | v1.0 | v2.0 |
|---------|------|------|
| User Authentication | ❌ No | ✅ Yes (login/registration) |
| Multi-User Support | ❌ Single user | ✅ Multiple users |
| Data Isolation | ❌ Shared data | ✅ Per-user collections |
| Admin Panel | ❌ No | ✅ User management |
| Modern UI | ⚠️ Basic | ✅ Professional theme |
| Role-Based Access | ❌ No | ✅ Admin/User roles |
| Password Security | N/A | ✅ Bcrypt hashing |
| Document Generation | ✅ Yes | ✅ Yes (same) |
| Chat Q&A | ✅ Yes | ✅ Yes (same) |
| External Integrations | ✅ Yes | ✅ Yes (same) |

## Troubleshooting

### Issue: "Module 'bcrypt' not found"
**Solution:**
```bash
pip install --upgrade -r requirements.txt
```

### Issue: "Cannot login with default credentials"
**Solution:**
1. Stop the app
2. Delete `users.db` file
3. Restart the app (will recreate default admin)

### Issue: "My old documents are gone"
**Solution:**
- Documents are now stored per-user
- Follow "Option 2: Migrate Existing Data" above
- Or re-upload your documents

### Issue: "Users reset after Streamlit Cloud restart"
**Expected on Free Tier:**
- SQLite database is ephemeral on Streamlit Cloud free tier
- Database resets when app restarts/sleeps
- For persistence: upgrade to paid tier or use external database

### Issue: "Can't access admin panel"
**Solution:**
- Only users with `admin` role can access admin panel
- Login with default admin account
- Check your role in Profile settings

## Rollback to v1.0

If you need to rollback:

1. **Checkout v1.0 code:**
   ```bash
   git checkout v1.0-tag
   # Or restore your backup of v1.0 files
   ```

2. **Restore old dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Restore data** (if you backed it up):
   ```bash
   rm -rf chroma_db
   cp -r chroma_db_v1_backup chroma_db
   ```

4. **Run v1.0:**
   ```bash
   streamlit run streamlit_app.py
   ```

## Getting Help

If you encounter issues during migration:

1. Check this migration guide thoroughly
2. Review DEPLOYMENT.md for deployment-specific issues
3. Check application logs for error messages
4. Verify all dependencies are installed: `pip list`
5. Try the "Fresh Start" option if data migration fails

## Recommended: Test in Development First

Before deploying v2.0 to production:

1. Test locally with the new version
2. Verify authentication works
3. Test document upload and generation
4. Create test user accounts
5. Verify admin panel functionality
6. Only then deploy to Streamlit Cloud or production

## Next Steps After Migration

1. **Change default admin password**
2. **Create user accounts** for your team
3. **Configure integrations** (SEC EDGAR) in Settings
4. **Upload style examples** to train the document generator
5. **Test all features** with real documents
6. **Review security settings** in admin panel

---

**Migration Support:** This is a major version upgrade. Take your time and test thoroughly before deploying to production.
