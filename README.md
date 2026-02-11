# HarmonEyes Theia SDK

Python SDK for real-time eye tracking analysis, cognitive load prediction, and sleepiness detection.

## Installation

### Direct from GitHub

```bash
# Install directly with pip
pip install git+https://github.com/harmoneyes/HarmonEyesTheia.git

# Or add to requirements.txt
git+https://github.com/harmoneyes/HarmonEyesTheia.git

# Or add to pyproject.toml
[project]
dependencies = [
    "harmoneyes-theia @ git+https://github.com/harmoneyes/HarmonEyesTheia.git"
]
```

### Install from Local Clone

```bash
# Clone the repository
git clone https://github.com/harmoneyes/HarmonEyesTheia.git
cd HarmonEyesTheia

# Install the package
pip install .
```


## Requirements
- Python 3.12 only
- No additional dependencies (all compiled into the binary)
- **License Key**: A valid license key is required to use the SDK.

### Using pyenv for Python 3.12

```bash
# Install pyenv
brew install pyenv
# Install Python 3.12
pyenv install 3.12
# Set local Python version
pyenv local 3.12

python3 --version
#> Python 3.12.X
```

## License & Usage

This software is proprietary and requires a valid license key to operate. The compiled binaries are publicly distributed but will not function without proper licensing credentials.

- **Copyright**: © RightEye LLC / HarmonEyes
- **License Type**: Proprietary / Commercial
- **Obtaining a License**: contact sales@harmoneyes.com

## Support

For issues, questions, or feature requests, please contact support@harmoneyes.com or create an issue on GitHub.
