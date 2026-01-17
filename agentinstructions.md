# Agent Instructions: Stremio HACS Integration Development

> **Project**: Home Assistant HACS Integration for Stremio  
> **Purpose**: These instructions guide the agent through implementing a production-ready integration  
> **Author data**: for manifest or other project files use this author data: author: @tamaygz, project-url: https://github.com/tamaygz/hacs-stremio, integration-name: hacs-stremio
> **Last Updated**: 2026-01-17

---

## 🎯 Primary Directive

You are implementing a **production-quality Home Assistant HACS integration** for Stremio. This is not a prototype or proof-of-concept—every line of code must meet professional standards suitable for public release and community use.

**Zero tolerance for**:
- ❌ Shortcuts or simplified implementations
- ❌ TODO comments or placeholder code
- ❌ Copy-paste without understanding
- ❌ Skipping error handling or edge cases
- ❌ Missing tests or documentation
- ❌ Code duplication when abstraction is appropriate

**Commitment to**:
- ✅ Complete, working implementations
- ✅ Comprehensive error handling
- ✅ Full test coverage
- ✅ Clear, maintained documentation
- ✅ Clean, idiomatic code following best practices
- ✅ Thoughtful architecture and design patterns

---

## 📋 Task Management Workflow

### 1. Always Start with the Task List

**Primary Reference**: [project.tasklist.md](project.tasklist.md)

Before starting any work session:
1. **Read** the entire current phase in `project.tasklist.md`
2. **Identify** the next ⬜ Not Started task in sequential order
3. **Check dependencies** - ensure all prerequisite tasks are ✅ Completed
4. **Update status** to 🟦 In Progress before beginning work

### 2. Use Sequential Thinking for Planning

**CRITICAL**: Before implementing ANY task, use the `mcp_mcp-sequentia_sequentialthinking_tools` to:
- Break down the task into logical steps
- Identify potential challenges or edge cases
- Plan the order of operations
- Consider what tools and resources you'll need
- Think through testing strategy

Example invocation:
```json
{
  "available_mcp_tools": ["mcp_brave-search_brave_web_search", "read_file", "create_file"],
  "thought": "I need to implement the config flow. First, I should research HA config flow patterns...",
  "thought_number": 1,
  "total_thoughts": 5,
  "next_thought_needed": true
}
```

### 3. Research Before Implementing

**Use websearch tools extensively** to find:
- Official Home Assistant developer documentation
- API documentation for external libraries (stremio-api, pyatv, etc.)
- Best practices and patterns from established HACS integrations
- Code examples from similar integrations
- Common pitfalls and solutions

**Recommended searches**:
- "Home Assistant [component] best practices 2026"
- "[library name] Python API documentation"
- "Home Assistant [feature] implementation example"
- "[integration pattern] error handling best practices"

**Tools to use**:
- `mcp_brave-search_brave_web_search` - For general web searches
- `mcp_ddg-search_search` - For alternative search results
- `mcp_fetch_fetch` - To retrieve full documentation pages

### 4. Reference Project Specifications

**Secondary Reference**: [project.specs.md](project.specs.md)

When task details are unclear:
1. **Check** `project.specs.md` for feature specifications
2. **Look for** architecture diagrams and component descriptions
3. **Review** API requirements and data structures
4. **Confirm** your understanding aligns with project goals

### 5. Implement with Quality

For each task implementation:

#### Code Quality Standards
- **Type hints**: Add type annotations to ALL functions and methods
- **Docstrings**: Document all public classes, methods, and functions (Google/NumPy style)
- **Error handling**: Wrap external calls in try-except with specific exception types
- **Logging**: Use `self._logger` or `_LOGGER` for debugging and error tracking
- **Constants**: Define all magic numbers/strings in `const.py`
- **Validation**: Validate all user inputs and API responses

#### Architectural Patterns
- **DRY Principle**: Create shared utilities when logic is repeated 2+ times
- **Single Responsibility**: Each class/function should have one clear purpose
- **Dependency Injection**: Pass dependencies as parameters, don't hardcode
- **Coordinator Pattern**: Use `DataUpdateCoordinator` for all API polling
- **Async/Await**: All I/O operations must be async
- **Entity Platform**: Follow HA entity platform patterns precisely

#### Code Organization
- **Project Structure**:
  ```
  custom_components/stremio/
  ├── __init__.py           # Integration setup
  ├── manifest.json         # Integration metadata
  ├── const.py              # Constants
  ├── config_flow.py        # Configuration UI
  ├── coordinator.py        # Data coordinator
  ├── stremio_client.py     # API client wrapper
  ├── sensor.py             # Sensor platform
  ├── binary_sensor.py      # Binary sensor platform
  ├── media_player.py       # Media player platform
  ├── services.py           # Custom services
  ├── media_source.py       # Media source integration
  ├── apple_tv_handover.py  # Apple TV feature
  ├── www/                  # Frontend resources
  └── translations/         # Localization files
  ```

- **Documentation Structure**:
  ```
  /docs/
  ├── setup.md              # Installation guide
  ├── configuration.md      # Configuration options
  ├── services.md           # Service documentation
  ├── events.md             # Event documentation
  ├── ui.md                 # Custom cards guide
  ├── api.md                # API reference
  ├── development.md        # Developer guide
  └── troubleshooting.md    # Common issues
  ```

- **Test Structure**:
  ```
  /tests/
  ├── __init__.py
  ├── conftest.py           # Test fixtures
  ├── test_config_flow.py   # Config flow tests
  ├── test_coordinator.py   # Coordinator tests
  ├── test_sensor.py        # Sensor tests
  ├── test_services.py      # Service tests
  └── fixtures/             # Mock data
  ```

### 6. Test Thoroughly

**Testing Requirements**:
- **Unit tests**: Test each component in isolation with mocked dependencies
- **Integration tests**: Test component interactions and data flow
- **Edge cases**: Test error conditions, empty data, malformed inputs
- **Coverage**: Aim for 80%+ code coverage minimum

**Testing Workflow**:
1. Write tests **before or during** implementation (TDD preferred)
2. Use `pytest-homeassistant-custom-component` fixtures
3. Mock external API calls with realistic response data
4. Test both success and failure paths
5. Run tests after every implementation: `pytest tests/`
6. Check coverage: `pytest --cov=custom_components.stremio tests/`

**Example Test Pattern**:
```python
async def test_config_flow_successful_auth(hass):
    """Test successful authentication flow."""
    with patch("custom_components.stremio.stremio_client.StremioClient.login") as mock_login:
        mock_login.return_value = {"success": True, "user": "test@example.com"}
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        # Assert results...
```

### 7. Document Everything

**Documentation Requirements**:
- **User docs**: Clear, step-by-step guides with examples
- **Code docs**: Docstrings on all public interfaces
- **API docs**: Document all services, entities, events
- **Examples**: Provide copy-paste ready YAML/configuration

**Documentation Checklist** (before marking task complete):
- [ ] All new classes have docstrings
- [ ] All public methods have docstrings with param/return descriptions
- [ ] User-facing features documented in `/docs/`
- [ ] README.md updated if new features affect quick start
- [ ] CHANGELOG.md updated with new features/changes
- [ ] Example configurations provided where applicable

### 8. Update Task Status

After completing implementation, testing, and documentation:

1. **Update** `project.tasklist.md`:
   - Change ⬜ to ✅ for completed task
   - Add completion timestamp
   - Update phase completion percentage
   - Update overall progress percentage

2. **Verify** all task outputs:
   - Check that expected outputs listed in task are delivered
   - Confirm no broken dependencies for subsequent tasks

3. **Commit** changes with descriptive message:
   ```
   feat(phase-X): Complete Task X.Y.Z - [Brief Description]
   
   - Implemented [feature]
   - Added tests with XX% coverage
   - Documented in docs/[file].md
   - Updated task list
   
   Task: [Task ID from project.tasklist.md]
   ```

---

## 🔍 Research & Best Practices Protocol

### When to Search for Best Practices

**Always search before**:
- Implementing a new platform (sensor, binary_sensor, media_player, etc.)
- Working with a new library (stremio-api, pyatv, lit-element, etc.)
- Implementing a design pattern (coordinator, config flow, entity, etc.)
- Writing complex error handling or retry logic
- Creating custom UI components

### What to Search For

**Home Assistant Specifics**:
- "Home Assistant [entity type] implementation best practices"
- "Home Assistant DataUpdateCoordinator error handling"
- "Home Assistant config flow validation patterns"
- "Home Assistant custom card development guide"
- "Home Assistant integration testing with pytest"

**External Libraries**:
- "[library name] Python API documentation"
- "[library name] async usage examples"
- "[library name] error handling best practices"
- "[library name] authentication patterns"

**Architecture & Patterns**:
- "Python async best practices 2026"
- "Dependency injection patterns Python"
- "Factory pattern Python async"
- "Observer pattern Home Assistant"

### How to Apply Research

1. **Read** official documentation thoroughly
2. **Study** code examples from similar integrations
3. **Understand** the pattern before implementing
4. **Adapt** patterns to fit project needs (don't copy blindly)
5. **Document** why you chose a particular approach
6. **Reference** sources in code comments for complex patterns

---

## 🛠️ Tool Usage Guidelines

### Use Tools Extensively

**Don't guess or assume—use tools to verify**:
- `read_file` - Read existing code before modifying
- `grep_search` - Find patterns and examples in codebase
- `semantic_search` - Discover related code and docs
- `file_search` - Locate files by pattern
- `list_dir` - Understand directory structure
- `get_errors` - Check for linting/type errors after changes

### Parallel Operations

**When possible, parallelize independent operations**:
```python
# Good - parallel file reads
read_file(config_flow.py) || read_file(coordinator.py)

# Bad - sequential when not needed
read_file(config_flow.py) → read_file(coordinator.py)
```

### Verification Loop

**After every implementation**:
1. `get_errors` - Check for syntax/type errors
2. `run_in_terminal("pytest tests/test_[feature].py")` - Run tests
3. `run_in_terminal("mypy custom_components/stremio/")` - Type check
4. `run_in_terminal("pylint custom_components/stremio/")` - Lint check

---

## 🏗️ Architectural Guidance

### Abstraction Principles

**Create abstractions when**:
- Same logic appears in 2+ places
- Multiple implementations share common structure
- External dependencies need to be isolated for testing
- Complex operations need to be simplified for users

**Example**: API Client Abstraction
```python
# Good - abstracted client
class StremioClient:
    """Wrapper for stremio-api with error handling and retries."""
    
    async def get_library(self) -> List[LibraryItem]:
        """Fetch library with automatic retry logic."""
        return await self._retry_on_failure(self._api.get_library)

# Usage in coordinator
library = await self._client.get_library()  # Clean, testable
```

### Error Handling Patterns

**Comprehensive error handling**:
```python
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError

async def _async_update_data(self):
    """Fetch data from API."""
    try:
        return await self._client.fetch_data()
    except AuthenticationError as err:
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except RateLimitError as err:
        # Handle rate limiting with backoff
        self._logger.warning("Rate limited, backing off: %s", err)
        raise UpdateFailed(f"Rate limited: {err}") from err
    except ConnectionError as err:
        raise UpdateFailed(f"Connection error: {err}") from err
    except Exception as err:
        self._logger.exception("Unexpected error fetching data")
        raise UpdateFailed(f"Unexpected error: {err}") from err
```

### Generalization Strategy

**Identify patterns and generalize**:

**Example**: Multiple similar sensors
```python
# Good - generalized base class
class StremioSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Stremio sensors."""
    
    def __init__(self, coordinator, sensor_type: str):
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"Stremio {SENSOR_TYPES[sensor_type]['name']}"
        self._attr_icon = SENSOR_TYPES[sensor_type]['icon']

# Create sensors easily
sensors = [
    StremioSensorBase(coordinator, "current_media"),
    StremioSensorBase(coordinator, "last_watched"),
    # ... more sensors
]
```

---

## ✅ Task Completion Checklist

Before marking any task as ✅ Completed, verify:

### Code Quality
- [ ] All functions have type hints
- [ ] All public interfaces have docstrings
- [ ] No hardcoded values (use constants)
- [ ] Error handling covers all failure modes
- [ ] Logging added for debugging
- [ ] No code duplication (abstracted where appropriate)
- [ ] Follows async/await patterns consistently
- [ ] No blocking I/O operations

### Testing
- [ ] Unit tests written and passing
- [ ] Integration tests passing (if applicable)
- [ ] Edge cases covered
- [ ] Mocks used for external dependencies
- [ ] Test coverage ≥80% for new code
- [ ] All tests run successfully: `pytest tests/`

### Code Standards
- [ ] No linting errors: `pylint custom_components/stremio/`
- [ ] No type errors: `mypy custom_components/stremio/`
- [ ] Formatted with black: `black custom_components/stremio/`
- [ ] No security vulnerabilities in dependencies

### Documentation
- [ ] Code documented (docstrings)
- [ ] User docs updated in `/docs/`
- [ ] README.md updated (if needed)
- [ ] CHANGELOG.md updated with changes
- [ ] Examples provided (if user-facing feature)

### Integration
- [ ] Dependencies added to manifest.json
- [ ] Translations added to strings.json
- [ ] Services registered in services.yaml (if applicable)
- [ ] No breaking changes to existing features
- [ ] Backward compatible (or documented migration path)

### Task List Management
- [ ] Task marked ✅ in project.tasklist.md
- [ ] Completion timestamp added
- [ ] Progress percentages updated
- [ ] Next task dependencies verified ready

---

## 🚫 Anti-Patterns to Avoid

### ❌ Don't Do This

1. **Implementing without planning**
   ```python
   # Bad - jumping straight to code
   def handle_request():
       # TODO: implement this
       pass
   ```

2. **Skipping error handling**
   ```python
   # Bad - no error handling
   data = await api.fetch()  # What if this fails?
   ```

3. **Hardcoding values**
   ```python
   # Bad - magic numbers
   if update_count > 5:
       do_something()
   ```

4. **Leaving TODOs**
   ```python
   # Bad - incomplete implementation
   def complex_feature():
       # TODO: handle edge case
       # TODO: add logging
       pass
   ```

5. **Copy-paste without understanding**
   ```python
   # Bad - copied code without adapting
   # This code doesn't match our architecture but it works...
   ```

### ✅ Do This Instead

1. **Plan with sequential thinking first**
   ```python
   # Good - planned and documented
   async def handle_request(self, request: Request) -> Response:
       """Handle incoming request with validation and error handling.
       
       Args:
           request: The incoming request object
           
       Returns:
           Response object with status and data
           
       Raises:
           ValidationError: If request is invalid
           APIError: If external API fails
       """
       await self._validate_request(request)
       try:
           return await self._process_request(request)
       except APIError as err:
           self._logger.error("API error: %s", err)
           raise
   ```

2. **Comprehensive error handling**
   ```python
   # Good - all paths handled
   try:
       data = await self._api.fetch()
   except AuthError as err:
       raise ConfigEntryAuthFailed from err
   except TimeoutError as err:
       raise UpdateFailed(f"Timeout: {err}") from err
   except Exception as err:
       self._logger.exception("Unexpected error")
       raise UpdateFailed from err
   ```

3. **Use constants**
   ```python
   # Good - defined constant
   MAX_RETRIES = 5
   if update_count > MAX_RETRIES:
       do_something()
   ```

4. **Complete implementations**
   ```python
   # Good - fully implemented
   async def complex_feature(self) -> FeatureResult:
       """Implement complex feature with all edge cases handled."""
       self._logger.debug("Starting complex feature")
       
       try:
           result = await self._process()
           self._handle_edge_case(result)
           return result
       except SpecificError as err:
           self._logger.error("Edge case occurred: %s", err)
           raise
   ```

5. **Understand and adapt patterns**
   ```python
   # Good - adapted pattern to our needs
   class StremioCoordinator(DataUpdateCoordinator):
       """Coordinator specifically designed for Stremio API polling.
       
       Implements the HA DataUpdateCoordinator pattern with Stremio-specific
       error handling and rate limiting (source: HA dev docs).
       """
   ```

---

## 🎓 Learning Resources

### Essential Documentation
- **Home Assistant Developer Docs**: https://developers.home-assistant.io/
- **HACS Documentation**: https://hacs.xyz/docs/publish/integration
- **stremio-api Library**: https://github.com/[find-via-search]
- **pyatv Documentation**: https://pyatv.dev/
- **lit-element Guide**: https://lit.dev/docs/

### Code Examples
- **HACS Integration Blueprint**: https://github.com/jpawlowski/hacs.integration_blueprint
- **HA Core Integrations**: https://github.com/home-assistant/core/tree/dev/homeassistant/components
- **pytest-homeassistant**: https://github.com/MatthewFlamm/pytest-homeassistant-custom-component

### Search First
When documentation is unclear or you need examples:
1. Use `mcp_brave-search_brave_web_search` or `mcp_ddg-search_search`
2. Search for official docs first, then community examples
3. Look for recent examples (2024-2026) for up-to-date patterns
4. Cross-reference multiple sources for accuracy

---

## 📊 Progress Tracking

### Regular Updates

**Update project.tasklist.md after every task**:
1. Change task status indicator (⬜ → 🟦 → ✅)
2. Update phase completion counts
3. Update overall progress percentage
4. Add timestamps for completed tasks

**Weekly Progress Reviews**:
- Review completed tasks for quality
- Check if any patterns for refactoring emerge
- Update documentation for changes
- Verify test coverage remains high

### Status Indicators Usage
- ⬜ **Not Started**: Task not yet begun
- 🟦 **In Progress**: Currently working (max 1-2 at a time)
- ✅ **Completed**: Task finished, tested, documented
- ⏸️ **Blocked**: Waiting on dependencies or decisions
- 🔄 **Review**: Ready for review or validation
- ❌ **Deferred**: Postponed to future release

---

## 🎯 Success Criteria

This project is successful when:

### Functionality
- ✅ All 113 tasks in project.tasklist.md are completed
- ✅ Integration installs cleanly via HACS
- ✅ Config flow works without errors
- ✅ All entities update correctly
- ✅ All services function as documented
- ✅ Custom cards display and function properly
- ✅ Apple TV handover works reliably

### Quality
- ✅ Test coverage ≥80% across all modules
- ✅ Zero pylint errors (minimum score 9.0)
- ✅ Zero mypy type errors
- ✅ All code formatted with black
- ✅ No hardcoded values or magic numbers
- ✅ No TODO comments in production code

### Documentation
- ✅ Complete user guides in `/docs/`
- ✅ All services documented with examples
- ✅ Developer guide enables new contributors
- ✅ Troubleshooting guide covers common issues
- ✅ README.md is professional and complete

### Release
- ✅ HACS submission accepted
- ✅ GitHub release v1.0.0 published
- ✅ CI/CD workflows passing
- ✅ CHANGELOG.md complete
- ✅ Community announcement made

---

## 💡 Pro Tips

1. **Small Commits**: Commit after each completed sub-task for easy rollback
2. **Test Early**: Write tests alongside code, not after
3. **Document as You Go**: Don't leave documentation for the end
4. **Ask for Clarification**: If specs are unclear, refer to project.specs.md
5. **Refactor Fearlessly**: If you see a better pattern, refactor (with tests)
6. **Use Templates**: Reference similar HA integrations as templates
7. **Automate**: Use CI/CD to catch issues early
8. **Think Like a User**: Test the actual user experience, not just code paths

---

## 🔄 Iterative Improvement

This integration will evolve. As you work:

1. **Identify Pain Points**: Note areas that could be improved
2. **Suggest Enhancements**: Add to "Future Enhancements" in task list
3. **Refactor When Needed**: Don't let technical debt accumulate
4. **Update These Instructions**: Improve this guide as you learn

---

## 📞 When Stuck

If you encounter a blocker:

1. **Search** for official documentation and examples
2. **Review** similar integrations in HA core
3. **Check** project.specs.md for architectural guidance
4. **Research** best practices for the specific problem
5. **Document** the blocker and decision made
6. **Update** task list if approach needs to change

Remember: **Quality over speed**. Take the time to do it right the first time.

---

## 🏁 Final Note

You are building a tool that will be used by the Home Assistant community. Every line of code you write affects real users' smart home experiences. Take pride in your work, follow best practices, and deliver something you'd be happy to use yourself.

**Excellence is not optional—it's the standard.**

---

*Last Updated: 2026-01-17 | Version: 1.0.0*
