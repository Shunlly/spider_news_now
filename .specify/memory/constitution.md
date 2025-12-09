<!--
SYNC IMPACT REPORT
==================
Version Change: Initial → 1.0.0
Rationale: Initial constitution creation establishing core principles for code quality,
           testing, extensibility, maintainability, consistency, and performance.

Modified Principles:
- NEW: I. Code Quality Standards
- NEW: II. Testing Discipline (NON-NEGOTIABLE)
- NEW: III. Extensibility First
- NEW: IV. Maintainability Requirements
- NEW: V. Consistency & Performance

Added Sections:
- Core Principles (5 principles)
- Quality Gates
- Development Standards
- Governance

Removed Sections: None (initial creation)

Templates Status:
- ✅ .specify/templates/plan-template.md - Updated Constitution Check with explicit gates,
     updated single project structure to match Development Standards
- ✅ .specify/templates/tasks-template.md - Task organization supports principles
- ✅ .specify/templates/spec-template.md - Requirements structure compatible
- ⚠ Future: Update command templates to reference specific constitution principles

Follow-up TODOs: None
-->

# Spider News Now Constitution

## Core Principles

### I. Code Quality Standards

All code MUST meet the following non-negotiable quality requirements:

- **Type Safety**: Explicit type annotations required for all function signatures,
  class attributes, and return values. No `Any` types without documented justification.
- **Error Handling**: Explicit error handling for all external calls (network, file I/O,
  database). No silent failures. Use structured exceptions with meaningful messages.
- **Documentation**: Every public module, class, and function MUST have docstrings
  explaining purpose, parameters, return values, and raised exceptions.
- **Code Reviews**: All changes require review against this constitution before merge.
- **Linting & Formatting**: Automated checks MUST pass (no warnings tolerated).
  Use consistent formatting tools across the project.

**Rationale**: Code quality directly impacts system reliability, onboarding speed, and
long-term maintenance costs. Preventable bugs from unclear code or missing types are
unacceptable in production systems.

### II. Testing Discipline (NON-NEGOTIABLE)

Testing is mandatory for all features following these rules:

- **Test-First Development**: Write failing tests before implementation. Tests define
  the contract and expected behavior. No feature is complete without tests.
- **Coverage Requirements**: Minimum 80% code coverage for business logic. 100%
  coverage required for critical paths (data persistence, API contracts, scrapers).
- **Test Categories**: MUST include:
  - **Unit Tests**: Isolated component testing with mocked dependencies
  - **Integration Tests**: Contract testing for scrapers, API endpoints, database access
  - **Contract Tests**: Verify scraper output format matches expected schema
- **Test Organization**: Tests mirror source structure. Each module `src/foo/bar.py`
  has corresponding `tests/unit/foo/test_bar.py` and integration tests as needed.
- **Red-Green-Refactor**: Strictly enforce TDD cycle - failing test → passing test →
  refactor for quality.

**Rationale**: Scrapers are fragile by nature (external HTML changes). Testing is the
only way to catch breakage early. API contracts must be tested to prevent downstream
failures. Test discipline is non-negotiable for system reliability.

### III. Extensibility First

The system MUST support growth without architectural rewrites:

- **Plugin Architecture**: New scrapers MUST integrate without modifying core code.
  All scrapers follow a standard interface/base class pattern.
- **Configuration Over Code**: Scraper scheduling, source management, and feature
  toggles MUST be configurable (environment variables, config files, database).
- **Versioned Contracts**: API responses and scraper output MUST follow versioned
  schemas. Breaking changes require new version endpoints.
- **Modular Design**: Clear separation between scraper logic, data storage, API layer,
  and presentation. Each layer independently replaceable.
- **Dependency Injection**: Avoid tight coupling. Use dependency injection for
  database, cache, external services to enable testing and swapping implementations.

**Rationale**: Requirements will evolve (new news sources, new output formats, new
clients). Building extensibility from day one prevents costly rewrites and enables
rapid feature development.

### IV. Maintainability Requirements

Code MUST be maintainable by future developers:

- **Principle of Least Surprise**: Code behavior should match developer expectations.
  No clever tricks, magic methods, or implicit behavior without clear documentation.
- **Refactoring Discipline**: Technical debt MUST be addressed within 2 sprints of
  identification. No "temporary" hacks that become permanent.
- **Logging & Observability**: Structured logging at appropriate levels (DEBUG for
  tracing, INFO for lifecycle, WARNING for recoverable issues, ERROR for failures).
  Include context (scraper ID, article count, execution time).
- **Self-Documenting Code**: Variable/function names describe purpose. Avoid
  abbreviations except industry-standard (URL, API, ID). Comments explain "why"
  not "what".
- **Dependency Management**: Pin all dependencies with exact versions. Document why
  each dependency exists. Minimize dependency count (avoid adding libraries for
  trivial functionality).

**Rationale**: Most code is read more than written. Maintainability directly impacts
development velocity, debugging time, and onboarding efficiency. Technical debt
compounds rapidly in scraping systems.

### V. Consistency & Performance

Deliver consistent user experience with predictable performance:

- **Response Time SLAs**: API queries MUST respond within 2 seconds for up to 1000
  results. Pagination required for larger result sets.
- **Scraper Performance**: Each scraper MUST complete within 60 seconds or fail with
  clear timeout error. Scrapers MUST run concurrently without blocking each other.
- **Data Consistency**: Duplicate detection MUST prevent storing the same article
  multiple times (uniqueness by URL or source+title hash).
- **Error Recovery**: Scraper failures MUST NOT crash the system. Log error, mark
  source as failed, continue with other scrapers. Retry logic with exponential backoff.
- **UI Consistency**: All views displaying news MUST use consistent grouping (by source),
  sorting (newest first default), and display format (title, URL, source, category, time).
- **Performance Monitoring**: Track and alert on key metrics (scraper success rate,
  API response time, database query time, duplicate rate).

**Rationale**: Users expect reliable, fast access to data. Scrapers will fail
(websites change, network issues) - graceful degradation is mandatory. Performance
issues compound as data grows; enforce limits early.

## Quality Gates

All features MUST pass these gates before deployment:

### Pre-Implementation Gates

- [ ] Feature specification approved and unambiguous (no [NEEDS CLARIFICATION])
- [ ] Implementation plan includes constitution compliance checks
- [ ] Test strategy defined (unit + integration test plan written)
- [ ] Performance targets identified and measurable

### Implementation Gates

- [ ] All tests written and passing (Red-Green-Refactor cycle followed)
- [ ] Code coverage meets minimum 80% threshold (100% for critical paths)
- [ ] Linting and formatting checks pass with zero warnings
- [ ] Type checking passes (mypy or equivalent) with no type errors
- [ ] All public APIs/functions have complete docstrings
- [ ] Code review completed with constitutional compliance verified

### Deployment Gates

- [ ] Integration tests pass in staging environment
- [ ] Performance benchmarks meet SLA targets
- [ ] Error handling tested (network failures, timeouts, invalid data)
- [ ] Logging verified (structured logs with appropriate levels)
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured for new functionality

## Development Standards

### Code Organization

- **Single Project Structure**: Use `src/` for source code, `tests/` for tests at
  repository root
- **Layered Architecture**:
  - `src/scrapers/`: Individual scraper implementations (inherit from base class)
  - `src/models/`: Data models (NewsArticle, ScraperRun, etc.)
  - `src/services/`: Business logic (duplicate detection, scheduling, data access)
  - `src/api/`: API endpoints (query, filter, status)
  - `src/web/`: Web interface (grouped display, UI components)
  - `src/lib/`: Shared utilities (logging, config, helpers)

### Testing Structure

- `tests/unit/`: Fast, isolated unit tests mirroring source structure
- `tests/integration/`: Slower integration tests for external dependencies
- `tests/contract/`: Scraper output schema validation tests
- Test file naming: `test_<module_name>.py` for each `<module_name>.py`

### Scraper Development Pattern

All scrapers MUST:
1. Inherit from base class defining standard interface
2. Implement required methods: `scrape()`, `parse()`, `validate()`
3. Include contract test verifying output schema
4. Handle errors gracefully (timeout, invalid HTML, network failure)
5. Include execution metadata (start time, end time, article count, status)

### Performance Standards

- Database queries MUST use indexes for common filters (source, category, date range)
- API responses MUST include pagination for queries returning >100 results
- Scraper concurrency MUST use thread/process pools (no sequential blocking execution)
- Caching SHOULD be used for frequently accessed data (source list, category mapping)

## Governance

### Amendment Process

1. **Proposal**: Document proposed change with rationale and impact analysis
2. **Review**: Team reviews impact on existing code and templates
3. **Migration Plan**: If breaking change, document migration steps and timeline
4. **Approval**: Requires consensus or designated approver sign-off
5. **Update**: Update constitution, increment version, update dependent templates
6. **Communication**: Announce change to all developers with migration guidance

### Version Semantics

- **MAJOR (X.0.0)**: Breaking principle removals, incompatible governance changes
- **MINOR (0.X.0)**: New principles added, expanded guidance, new quality gates
- **PATCH (0.0.X)**: Clarifications, typo fixes, wording improvements (no semantic change)

### Compliance Review

- **PR Review**: Every pull request MUST be reviewed for constitutional compliance
- **Quarterly Audit**: Review codebase quarterly for principle adherence
- **Violation Response**: Document violations, create remediation tasks, update
  constitution if principle proves impractical
- **Template Sync**: When constitution changes, verify all templates in
  `.specify/templates/` align with new principles

### Enforcement

- This constitution supersedes all other development practices and guidelines
- Code reviewers MUST reject changes violating core principles
- Technical debt MUST be tracked and prioritized for remediation
- Complexity additions MUST be justified against extensibility/maintainability principles
- Use `.specify/memory/constitution.md` as authoritative source for all development decisions

**Version**: 1.0.0 | **Ratified**: 2025-12-08 | **Last Amended**: 2025-12-08
