# Publishing CopyCrafter

This document provides a complete guide to publishing CopyCrafter to GitHub and making it available for users.

## 1. GitHub Repository

### Initial Setup (if not already done)

1. Create a new repository on GitHub
2. Push your code to GitHub:
   ```bash
   git remote add origin https://github.com/nesimtunc/copycrafter.git
   git push -u origin main
   ```

### Repository Configuration

1. Add appropriate topics to your repository (e.g., flutter, macos, desktop-app, file-management)
2. Set up a description and website link if you have one
3. Enable GitHub Issues for user feedback
4. Add a license file if not already present

## 2. Building and Releasing

### Automatic Builds via GitHub Actions

When you push a tag starting with 'v', GitHub Actions will automatically:
1. Build the app for macOS and Windows
2. Create installers
3. Create a draft GitHub Release with the binaries attached

To trigger this process:
```bash
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0
```

### Manual Building

To build manually:
1. Run the build script:
   ```bash
   ./scripts/build_all.sh
   ```
2. This will create releases in the `releases/` directory
3. Upload these manually to a GitHub Release

## 3. Code Signing for Distribution

### macOS

For proper distribution on macOS:
1. Obtain an Apple Developer certificate (Apple Developer Program membership required)
2. Sign the app:
   ```bash
   codesign --force --options runtime --sign "Developer ID Application: Your Name (TEAM_ID)" \
     build/macos/Build/Products/Release/CopyCrafter.app
   ```
3. Notarize the app:
   ```bash
   xcrun altool --notarize-app --primary-bundle-id "com.yourdomain.copycrafter" \
     --username "your@email.com" --password "@keychain:AC_PASSWORD" \
     --file path/to/CopyCrafter.dmg
   ```
4. Check notarization status:
   ```bash
   xcrun altool --notarization-info [RequestUUID] -u "your@email.com" -p "@keychain:AC_PASSWORD"
   ```
5. Staple the notarization ticket:
   ```bash
   xcrun stapler staple "path/to/CopyCrafter.dmg"
   ```

### Windows

For Windows distribution:
1. Obtain a code signing certificate from a trusted CA
2. Sign the executable:
   ```bash
   signtool sign /a /tr http://timestamp.digicert.com /td sha256 /fd sha256 \
     build\windows\runner\Release\CopyCrafter.exe
   ```

## 4. Updating Existing Installations

Currently, CopyCrafter doesn't include auto-update functionality. Users will need to:
1. Download the new version manually
2. Replace their existing installation 

Consider adding an auto-update mechanism in future versions.

## 5. Marketing and Distribution

1. Update your README.md with screenshots and clear installation instructions
2. Create a landing page or website for the app (optional)
3. Share on relevant platforms:
   - Flutter community
   - Reddit (r/Flutter, r/MacOS, r/WindowsApps)
   - Twitter/X
   - Developer forums
   
## 6. Legal Considerations

1. Include a clear privacy policy if your app collects any user data
2. Ensure you have the right to use all included libraries and assets
3. Consider trademark registration if planning commercial use

## 7. Post-Release

1. Monitor GitHub Issues for bug reports
2. Create a roadmap for future development
3. Engage with users for feedback
4. Plan regular updates to add features and fix bugs 