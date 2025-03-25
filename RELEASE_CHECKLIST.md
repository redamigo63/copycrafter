# Release Checklist

Follow this checklist when releasing a new version of CopyCrafter.

## Pre-release

1. [ ] Update version in `pubspec.yaml`
2. [ ] Update CHANGELOG.md with the changes in this version
3. [ ] Test the app on all supported platforms (macOS, Windows)
4. [ ] Fix any bugs found during testing
5. [ ] Commit all changes
6. [ ] Create and push a version tag (e.g., `v1.0.1`)

```bash
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1
```

## Release

### Automated Release via GitHub Actions

When you push a tag that starts with 'v', GitHub Actions will automatically:

1. [ ] Build the app for macOS and Windows
2. [ ] Create installers/packages for each platform
3. [ ] Create a draft GitHub release with the installers attached

### Manual Release

If you need to build manually:

1. [ ] Run the build script: `./scripts/build_all.sh`
2. [ ] Upload the built packages to the GitHub release

## Post-release

1. [ ] Review the draft GitHub release
2. [ ] Add release notes from CHANGELOG.md
3. [ ] Publish the GitHub release
4. [ ] Announce the new version to users
5. [ ] Update documentation website (if applicable)
6. [ ] Start planning the next version

## Code Signing (Future Enhancement)

### macOS

To sign the macOS application for distribution:

1. [ ] Obtain an Apple Developer certificate
2. [ ] Sign the application:
   ```bash
   codesign --force --options runtime --sign "Developer ID Application: Your Name (TEAM_ID)" \
     build/macos/Build/Products/Release/CopyCrafter.app
   ```
3. [ ] Verify the signature:
   ```bash
   codesign --verify --deep --strict build/macos/Build/Products/Release/CopyCrafter.app
   ```
4. [ ] Notarize the application (for distribution outside the App Store)

### Windows

For Windows applications:

1. [ ] Obtain a code signing certificate from a trusted CA
2. [ ] Sign the application using signtool:
   ```bash
   signtool sign /a /tr http://timestamp.digicert.com /td sha256 /fd sha256 \
     build\windows\runner\Release\CopyCrafter.exe
   ```
``` 