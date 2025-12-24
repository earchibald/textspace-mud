# TextSpace Semantic Versioning Process

## Version Format: MAJOR.MINOR.PATCH

### Version Increment Rules

**MAJOR** (X.0.0) - Breaking changes:
- API changes that break existing clients
- Database schema changes requiring migration
- Fundamental architecture changes
- Removal of deprecated features

**MINOR** (X.Y.0) - New features (backward compatible):
- New commands or functionality
- New configuration options
- Performance improvements
- UI/UX enhancements

**PATCH** (X.Y.Z) - Bug fixes (backward compatible):
- Bug fixes
- Security patches
- Documentation updates
- Code refactoring without behavior changes

### Release Process

1. **Determine Version Type**
   - Review changes since last release
   - Apply semver rules above

2. **Update Version**
   ```bash
   # Update VERSION in server_web_only.py
   # Current: 2.2.0 → New Feature: 2.3.0
   ```

3. **Commit and Tag**
   ```bash
   git add .
   git commit -m "feat: tab completion v2.3.0"
   git tag v2.3.0
   git push origin main --tags
   ```

4. **Deploy to Railway**
   ```bash
   railway up
   ```

5. **Validate Deployment (60 Second Wait)**
   ```bash
   sleep 60  # Wait for Railway to cycle versions
   ```
   - Check server_status() for new version number
   - Test new functionality
   - If deployment fails, check GitHub CI results
   - Monitor server logs for issues

**Note**: See `_bmad/_config/deployment-process.md` for comprehensive deployment documentation including troubleshooting and Railway-specific behaviors.

### Current Change Analysis
- **Generalized command parser**: New feature
- **Improved argument validation**: Backward compatible
- **No breaking changes**: Existing functionality preserved
- **Version bump**: 2.1.0 → 2.2.0 (MINOR)
