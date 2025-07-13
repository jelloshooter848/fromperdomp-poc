# Contributing to DOMP

Welcome to the DOMP (Decentralized Online Marketplace Protocol) project! We're excited that you want to contribute to building the future of decentralized commerce.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Contributing Guidelines](#contributing-guidelines)
- [DOMP Improvement Proposals (DIPs)](#domp-improvement-proposals-dips)
- [Code Style and Standards](#code-style-and-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

### Our Pledge

We are committed to making participation in the DOMP project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- The use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Project maintainers are responsible for clarifying standards of acceptable behavior and are expected to take appropriate and fair corrective action in response to any instances of unacceptable behavior.

## Getting Started

### Prerequisites

Before contributing, ensure you have:

1. **Development Environment**
   - Python 3.8+ or Node.js 16+
   - Git version control
   - Code editor (VS Code, PyCharm, etc.)

2. **Domain Knowledge**
   - Basic understanding of Bitcoin and Lightning Network
   - Familiarity with Nostr protocol concepts
   - Understanding of decentralized systems

3. **DOMP Knowledge**
   - Read the [Protocol Overview](docs/protocol/dip-01-core-events.md)
   - Review the [Developer Guide](docs/DEVELOPER_GUIDE.md)
   - Try the [Reference Implementation](implementations/reference/python/)

### Setup Development Environment

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/fromperdomp-poc.git
cd fromperdomp-poc

# 3. Add upstream remote
git remote add upstream https://github.com/original-org/fromperdomp-poc.git

# 4. Setup Python environment
cd implementations/reference/python
python3 -m venv domp-env
source domp-env/bin/activate
pip install -r requirements.txt

# 5. Install development tools
pip install pytest black flake8 pre-commit

# 6. Setup pre-commit hooks
pre-commit install

# 7. Verify setup
python3 -c "from domp.crypto import KeyPair; print('✅ Setup complete')"
```

## Development Process

### Development Philosophy

DOMP follows these core principles:
- **Protocol-first design**: Specifications before implementations
- **Maximum decentralization**: No central authorities or gatekeepers
- **Maximum simplicity**: Start minimal, add complexity only when necessary
- **Implementation diversity**: Multiple independent implementations strengthen the protocol

### Branching Strategy

We use a simplified Git flow:

```
main branch (stable)
├── develop branch (integration)
├── feature/feature-name (new features)
├── fix/issue-description (bug fixes)
├── docs/documentation-update (documentation)
└── dip/dip-number-title (protocol improvements)
```

### Workflow

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation as needed
   - Commit changes with clear messages

3. **Test Your Changes**
   ```bash
   # Run tests
   pytest
   
   # Check code style
   black --check .
   flake8
   
   # Run integration tests
   python3 test_integration.py
   ```

4. **Submit Pull Request**
   - Push branch to your fork
   - Open pull request against `develop` branch
   - Include clear description of changes
   - Reference any related issues

### Commit Message Format

Use clear, descriptive commit messages:

```
type(scope): short description

Longer description if needed.

- Bullet points for multiple changes
- Reference issues with #123
- Include breaking changes

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process, dependency updates

## Contributing Guidelines

### Types of Contributions

#### 🐛 Bug Reports

**Before submitting:**
- Check existing issues to avoid duplicates
- Test with the latest version
- Gather relevant information

**Include in your report:**
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs or error messages

#### 💡 Feature Requests

**Before submitting:**
- Check if feature already exists or is planned
- Consider if it fits DOMP's goals
- Think about implementation complexity

**Include in your request:**
- Clear description of the feature
- Use cases and benefits
- Possible implementation approach
- Any relevant examples

#### 🔧 Code Contributions

**Good first contributions:**
- Documentation improvements
- Test coverage expansion
- Bug fixes with clear reproduction steps
- Performance optimizations
- Code style improvements

**Larger contributions:**
- New protocol features (require DIP)
- New client implementations
- Integration with external services
- Security enhancements

## DOMP Improvement Proposals (DIPs)

For significant protocol changes, we use DOMP Improvement Proposals (DIPs) - similar to Bitcoin's BIPs or Nostr's NIPs.

### When to Write a DIP

**Requires DIP:**
- New event types
- Protocol modifications
- Cryptographic changes
- Network behavior changes
- Breaking changes

**Doesn't require DIP:**
- Bug fixes
- Implementation improvements
- Documentation updates
- Client-side features

### DIP Process

1. **Draft DIP**
   ```markdown
   # DIP-XX: Title
   
   ## Abstract
   Brief description of the proposal.
   
   ## Motivation
   Why is this needed?
   
   ## Specification
   Detailed technical specification.
   
   ## Rationale
   Design decisions and alternatives.
   
   ## Backwards Compatibility
   Impact on existing implementations.
   
   ## Test Vectors
   Examples and test cases.
   
   ## Implementation
   Reference implementation.
   ```

2. **Community Discussion**
   - Open GitHub issue for discussion
   - Present in community meetings
   - Gather feedback and iterate

3. **Implementation**
   - Create reference implementation
   - Write comprehensive tests
   - Update documentation

4. **Acceptance**
   - Community consensus
   - Technical review
   - Integration into main branch

### DIP Categories

- **Core**: Protocol fundamentals
- **Network**: Relay and networking
- **Crypto**: Cryptographic standards  
- **Application**: Client features
- **Process**: Development processes

## Code Style and Standards

### Python Standards

We follow PEP 8 with some modifications:

```python
# Line length: 88 characters (Black default)
# Use double quotes for strings
# Use type hints

from typing import List, Dict, Optional
import json

class ProductListing:
    """Create marketplace product listings."""
    
    def __init__(
        self,
        product_name: str,
        price_satoshis: int,
        description: Optional[str] = None
    ) -> None:
        self.product_name = product_name
        self.price_satoshis = price_satoshis
        self.description = description or ""
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for serialization."""
        return {
            "product_name": self.product_name,
            "price_satoshis": self.price_satoshis,
            "description": self.description
        }
```

### Security Standards

#### Input Validation
```python
def validate_price(price_sats: int) -> bool:
    """Validate price is within acceptable range."""
    MIN_PRICE = 1000  # 1000 sats minimum
    MAX_PRICE = 2_100_000_000_000_000  # 21M BTC in sats
    
    return MIN_PRICE <= price_sats <= MAX_PRICE
```

#### Cryptographic Standards
```python
# Always use secure random generation
import secrets

def generate_private_key() -> bytes:
    """Generate cryptographically secure private key."""
    return secrets.randbits(256).to_bytes(32, 'big')
```

## Testing Requirements

### Test Categories

All contributions must include appropriate tests:

#### Unit Tests
```python
def test_create_listing():
    """Test creating a valid product listing."""
    listing = ProductListing(
        product_name="Test Item",
        description="A test item",
        price_satoshis=1_000_000,
        category="test"
    )
    
    assert listing.product_name == "Test Item"
    assert listing.price_satoshis == 1_000_000
```

#### Integration Tests
```python
async def test_full_marketplace_flow():
    """Test complete marketplace transaction flow."""
    # Implementation of end-to-end test
    pass
```

#### Security Tests
```python
def test_signature_verification():
    """Test that invalid signatures are rejected."""
    # Test signature validation
    pass
```

### Test Coverage

Maintain high test coverage:
- >90% coverage on core modules
- >80% coverage overall

## Documentation

### Documentation Requirements

All contributions should include relevant documentation:

#### Code Documentation
- Docstrings for all public functions and classes
- Type hints throughout codebase
- Comments for complex logic

#### User Documentation
- API documentation
- Tutorial updates
- Example code

#### Protocol Documentation
- DIP specifications
- Architecture documentation
- Security analysis

## Community

### Communication Channels

#### GitHub
- **Issues**: Bug reports, feature requests
- **Discussions**: General questions, ideas
- **Pull Requests**: Code contributions

#### Getting Help

1. Check existing documentation
2. Search GitHub issues
3. Ask in GitHub discussions
4. Join community meetings

### Recognition

We recognize contributions through:
- Contributor credits in releases
- GitHub recognition on profiles
- Community acknowledgment in meetings

### Code of Conduct Enforcement

1. **Warning**: First violation
2. **Temporary ban**: Repeated violations
3. **Permanent ban**: Severe or continued violations

Appeals can be made to project maintainers.

---

## Getting Started Checklist

Ready to contribute? Follow this checklist:

- [ ] Read this contributing guide
- [ ] Set up development environment
- [ ] Run existing tests successfully
- [ ] Make a small test change
- [ ] Open your first pull request
- [ ] Join community discussions
- [ ] Explore the codebase
- [ ] Find an issue to work on

**Thank you for contributing to DOMP!** 🚀

Together, we're building the future of decentralized commerce. Every contribution, no matter how small, helps make DOMP better for everyone.

---

*For questions about contributing, please open a GitHub discussion or contact the maintainers.*