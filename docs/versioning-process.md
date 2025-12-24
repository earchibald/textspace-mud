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
   # Current: 2.0.26 → New Feature: 2.1.0
   ```

3. **Commit and Tag**
   ```bash
   git add .
   git commit -m "feat: admin/user bot visibility differentiation v2.1.0"
   git tag v2.1.0
   git push origin main --tags
   ```

4. **Deploy and Test**
   - Verify deployment
   - Test new functionality
   - Monitor for issues

### Current Change Analysis
- **Bot visibility differentiation**: New feature
- **Admin vs user views**: Backward compatible
- **No breaking changes**: Existing functionality preserved
- **Version bump**: 2.0.26 → 2.1.0 (MINOR)
