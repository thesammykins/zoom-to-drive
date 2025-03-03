# Release Process

This document outlines the steps for building and releasing new versions of the Zoom to Drive Recording Manager.

## Prerequisites

- macOS 10.13 or higher
- Python 3.8 or higher
- Git
- GitHub account with repository access

## Build Process

### Local Development Build

1. Clone the repository:
```bash
git clone https://github.com/thesammykins/zoom-to-drive.git
cd zoom-to-drive
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the build script:
```bash
./build.sh
```

The built application will be available in:
- `dist/Zoom to Drive.app` - The application bundle
- `dist/Zoom to Drive.app.zip` - The release package

### GitHub Actions Build

The application is automatically built and released when a new tag is pushed:

1. Create and push a new tag:
```bash
git tag v2.0.0  # Replace with appropriate version
git push origin v2.0.0
```

2. The GitHub Action will:
   - Build the application
   - Create a GitHub release
   - Upload the app and checksum
   - Run tests and linting

## Version Management

### Version Format
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Example: v2.0.0, v2.0.1, v2.1.0

### Version Bumping

1. Update version in `zoom_manager.spec`:
```python
app = BUNDLE(
    exe,
    name='Zoom to Drive.app',
    icon='zoom_manager/config/icon.icns',
    bundle_identifier='com.zoomdrive.app',
    info_plist={
        'CFBundleShortVersionString': '2.0.0',  # Update this
        'CFBundleVersion': '2.0.0',             # And this
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.13.0',
    }
)
```

2. Create and push tag:
```bash
git tag v2.0.0  # Match the version in spec file
git push origin v2.0.0
```

## Testing

Before creating a release:

1. Run tests locally:
```bash
pytest tests/
```

2. Run linting:
```bash
flake8 zoom_manager/src
black --check zoom_manager/src
```

3. Test the built application:
   - Build using `./build.sh`
   - Install from `dist/Zoom to Drive.app`
   - Test all features
   - Verify credential encryption
   - Check progress bars
   - Test error handling

## Release Checklist

- [ ] Update version in `zoom_manager.spec`
- [ ] Run tests and linting
- [ ] Test the built application
- [ ] Create and push version tag
- [ ] Verify GitHub Action build
- [ ] Check release assets:
  - [ ] Application zip file
  - [ ] SHA256 checksum
  - [ ] Release notes
- [ ] Test the release package

## Troubleshooting

### Build Issues

1. Icon Creation Fails
```bash
# Manually create icon
python zoom_manager/src/create_icon.py
```

2. PyInstaller Build Fails
```bash
# Clean build directory
rm -rf build dist
# Rebuild
pyinstaller zoom_manager.spec
```

3. Missing Dependencies
```bash
# Update requirements
pip install -r requirements.txt
```

### Release Issues

1. GitHub Action Fails
- Check the Actions tab for error logs
- Verify tag format (v*)
- Ensure all tests pass

2. Release Creation Fails
- Verify GitHub token permissions
- Check release name format
- Ensure assets are properly zipped

## Security Considerations

1. Credential Storage
- Verify encryption key storage
- Test credential loading
- Check secure file handling

2. Release Signing
- Verify code signing
- Check bundle identifier
- Validate entitlements

## Maintenance

### Regular Tasks

1. Dependency Updates
```bash
# Update requirements
pip install --upgrade -r requirements.txt
# Update requirements.txt
pip freeze > requirements.txt
```

2. Icon Updates
```bash
# Regenerate icon
python zoom_manager/src/create_icon.py
```

3. Documentation Updates
- Update RELEASE.md for new processes
- Update README.md for user-facing changes
- Update inline code documentation 