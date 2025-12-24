# TextSpace Issue Workflow

## Overview

Structured workflow for handling GitHub issues from analysis through resolution, ensuring quality implementation and stakeholder approval.

## Workflow Steps

### 1. Analyze Issue
- **Read and understand** the issue requirements
- **Identify scope** and technical complexity
- **Assess impact** on existing functionality
- **Determine dependencies** and prerequisites
- **Estimate effort** and implementation approach

### 2. Propose Solution
- **Design approach** with technical details
- **Consider alternatives** and trade-offs
- **Identify potential risks** and mitigation strategies
- **Plan implementation steps** and testing approach
- **Document assumptions** and constraints

### 3. Comment on Issue
- **Post solution proposal** with technical details
- **Explain implementation approach** and rationale
- **Highlight any breaking changes** or considerations
- **Request feedback** from stakeholders
- **Wait for approval** before proceeding

### 4. Implement and Test
- **Code the solution** following proposed approach
- **Write tests** if required or requested
- **Test functionality** locally and on deployment
- **Verify edge cases** and error handling
- **Document changes** in commit messages

### 5. Request Approval to Close
- **Demonstrate working solution** with examples
- **Provide testing evidence** (screenshots, logs, etc.)
- **Confirm requirements met** against original issue
- **Request stakeholder review** and approval
- **Ask for explicit permission to close** the issue
- **NEVER auto-close GitHub issues** without user confirmation

### 6. Iteration Loop (if needed)
If approval is not granted:
- **Address feedback** and concerns raised
- **Refine implementation** based on comments
- **Re-test updated solution** thoroughly
- **Return to Step 5** with improved implementation
- **Repeat until approved** by stakeholders

## Critical Rule: Issue Closure Authority

**The prompt user (stakeholder) has final authority over issue closure, not the implementer.**

- ✅ **Correct**: "MOTD implemented and tested. Ready to close issue #3?"
- ❌ **Wrong**: Auto-closing issues after implementation
- ✅ **Wait for**: Explicit "yes, close it" confirmation
- ❌ **Never**: Assume completion means closure approval

## Best Practices

### Analysis Phase
- Ask clarifying questions early
- Consider user experience impact
- Review related issues and PRs
- Check for existing similar functionality

### Implementation Phase
- Follow established coding standards
- Use semantic versioning for releases
- Test on both local and production environments
- Document any configuration changes needed

### Communication
- Keep stakeholders informed of progress
- Be transparent about challenges or delays
- Provide clear examples and demonstrations
- Respond promptly to feedback and questions

### Quality Gates
- Code compiles without errors
- Functionality works as specified
- No regression in existing features
- Performance impact is acceptable
- Documentation is updated if needed

## Example Workflow

```
Issue: "Add tab completion for empty input"

1. ANALYZE: User wants help display when pressing TAB on empty line
2. PROPOSE: Return organized command help instead of completion list
3. COMMENT: "I'll modify the completion API to return help text for empty input..."
4. IMPLEMENT: Update server API and client JavaScript
5. TEST: Verify TAB on empty line shows organized help
6. REQUEST: "Tab completion now shows organized help. All requirements met. Ready to close?"
7. WAIT: For explicit stakeholder approval
8. CLOSE: Only after receiving "yes, close it" confirmation
```

## Issue Closure Protocol

**Required Comment Format:**
```
✅ [Feature] implemented and tested successfully. 

Requirements verification:
- ✅ Requirement 1: Evidence/example
- ✅ Requirement 2: Evidence/example  
- ✅ Requirement 3: Evidence/example

Testing completed:
- ✅ Local testing passed
- ✅ Production deployment verified
- ✅ No regressions detected

**Ready to close this issue?**
```

**Wait for explicit approval before closing.**

## Issue States

- **Open** - Issue identified, awaiting analysis
- **In Progress** - Analysis complete, implementation underway
- **Review** - Implementation complete, awaiting approval
- **Closed** - Approved and resolved by stakeholders

## Documentation Requirements

- Link to relevant commits and PRs
- Include before/after examples where applicable
- Update related documentation if functionality changes
- Tag releases with issue references for traceability

## Success Criteria

- ✅ Original issue requirements fully met
- ✅ No regression in existing functionality  
- ✅ **Explicit stakeholder approval obtained**
- ✅ Implementation tested and verified
- ✅ Documentation updated as needed
- ✅ **Issue closed only after user confirmation**

## Process Violations to Avoid

- ❌ **Auto-closing issues** after implementation
- ❌ **Assuming completion** means closure approval
- ❌ **Closing without explicit permission** from stakeholder
- ❌ **Skipping the approval request** step
- ❌ **Acting as both implementer and approver**
