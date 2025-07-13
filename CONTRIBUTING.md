# Contributing to DOMP

Thank you for your interest in contributing to the Decentralized Online Marketplace Protocol!

## Development Philosophy

DOMP follows these core principles:
- **Protocol-first design**: Specifications before implementations
- **Maximum decentralization**: No central authorities or gatekeepers
- **Maximum simplicity**: Start minimal, add complexity only when necessary
- **Implementation diversity**: Multiple independent implementations strengthen the protocol

## How to Contribute

### 1. Protocol Development (DIPs)

Protocol changes follow the DIP (DOMP Improvement Proposal) process:

1. **Draft**: Create a new DIP in `docs/protocol/dip-XX-title.md`
2. **Discussion**: Open GitHub issue for community feedback
3. **Revision**: Update based on feedback
4. **Implementation**: Create reference implementation
5. **Testing**: Add test vectors and validation
6. **Acceptance**: Community consensus through GitHub discussions

### 2. Implementation Development

- **Reference implementations** in `implementations/reference/`
- **Community implementations** in `implementations/community/`
- All implementations must pass the protocol test suite
- Implementations should be well-documented and tested

### 3. Tools and Examples

- **Developer tools** in `tools/`
- **Example applications** in `examples/`
- Focus on developer experience and protocol adoption

## DIP Process

### DIP Structure
```markdown
# DIP-XX: Title

## Summary
Brief description of the proposal

## Motivation
Why is this change needed?

## Specification
Detailed technical specification

## Rationale
Design decisions and trade-offs

## Test Vectors
Examples for validation

## Implementation
Reference implementation details
```

### DIP Categories
- **Core**: Changes to core protocol events
- **Networking**: Relay and transport improvements  
- **Applications**: Higher-level application patterns
- **Informational**: Guidelines and best practices

## Code Guidelines

### Protocol Specifications
- Use clear, unambiguous language
- Include complete examples
- Provide test vectors for validation
- Consider security implications

### Reference Implementations
- Follow language-specific best practices
- Include comprehensive tests
- Document public APIs
- Handle errors gracefully
- Use secure cryptographic libraries

### Documentation
- Keep README files up to date
- Include usage examples
- Document security considerations
- Explain design decisions

## Testing Requirements

All contributions must include:
- **Unit tests** for new functionality
- **Integration tests** for protocol compliance
- **Security tests** for attack vectors
- **Interoperability tests** across implementations

## Security

- Report security issues privately via email
- Include threat model analysis for new features
- Use established cryptographic primitives
- Avoid storing secrets in code or logs

## Community

- Be respectful and constructive
- Help newcomers understand the protocol
- Share knowledge and best practices
- Collaborate across implementations

## Getting Started

1. Read the [Protocol Overview](docs/protocol/dip-01-core-events.md)
2. Set up a development environment
3. Run the test suite: `make test`
4. Try the reference implementation
5. Join discussions in GitHub issues

For questions, open a GitHub issue or discussion.