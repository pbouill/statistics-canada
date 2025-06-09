## Overview
A Python project template with automated versioning and build utilities.
see: https://www12.statcan.gc.ca/census-recensement/2021/ref/dict/fig/index-eng.cfm?ID=f1_1

## Installation

### From PyPI
```bash
pip install template-project
```

### From source
```bash
git clone https://github.com/pbouill/template.git
cd template
pip install -e .
```

## Features
- Automated version generation based on timestamps
- Git commit hash tracking in builds
- Configurable package dependencies

## Usage

```python
import template

# Your code examples here
```

## Development

### Requirements
- Python 3.10 or later

### Setup development environment
```bash
pip install -e ".[all]"
```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
This project is licensed under the GPL-3.0 License - see the LICENSE file for details.