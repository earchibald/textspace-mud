# TextSpace Issue Workflow

## Overview

Structured workflow for handling GitHub issues from analysis through resolution. The key principle: **implement after planning UNLESS the user explicitly restricts it.**

## Workflow Steps

### 1. Analyze Issue
- **Read and understand** the issue requirements
- **Identify scope** and technical complexity
- **Assess impact** on existing functionality
- **Determine dependencies** and prerequisites
- **Estimate effort** and implementation approach
- **Note any restrictions** from the user prompt

### 2. Propose Solution
- **Design approach** with technical details
- **Consider alternatives** and trade-offs
- **Identify potential risks** and mitigation strategies
- **Plan implementation steps** and testing approach
- **Document assumptions** and constraints

### 3. Comment on Issue with Proposal
- **Post solution proposal** with technical details
- **Explain implementation approach** and rationale
- **Highlight any breaking changes** or considerations
- **Check the user prompt for restrictions**:
  - If user says: "DON'T implement" → WAIT for approval before proceeding
  - If user says: "Implement this" → PROCEED immediately
  - If user says: "Ask before implementing" → WAIT for approval before proceeding
  - If no explicit restriction → PROCEED with implementation

### 4. Implement and Test
- **Code the solution** following proposed approach
- **Write tests** if required or requested
- **Test functionality** locally and on deployment
- **Verify edge cases** and error handling
- **Document changes** in commit messages
- **NOTE: No permission required after Step 3 UNLESS user explicitly restricted it**

### 5. Demonstrate Solution
- **Show working implementation** with examples
- **Provide testing evidence** (screenshots, logs, test results)
- **Confirm requirements met** against original issue
- **Provide links** to commits, PRs, and deployments
- **Comment on issue** with implementation summary

### 6. Request Closure Approval
- **Ask stakeholder**: "Ready to close this issue?"
- **Wait for explicit approval** before closing
- **Only close after** user confirms with "yes, close it" or equivalent

### 7. Iteration Loop (if feedback requires changes)
If review feedback requires changes:
- **Address feedback** and concerns raised
- **Refine implementation** based on comments
- **Re-test updated solution** thoroughly
- **Return to Step 5** with improved implementation
- **Repeat until approved** by stakeholders

## Critical Rules

### Rule 1: Implementation Authority
**Implementation proceeds after planning UNLESS the user explicitly restricts it in their prompt.**

| Scenario | Action |
|----------|--------|
| User prompt has no implementation restrictions | IMPLEMENT immediately |
| User says "implement this" | IMPLEMENT immediately |
| User says "don't implement" | WAIT for approval |
| User says "ask before implementing" | WAIT for approval |
| User says "this needs approval" | WAIT for approval |

### Rule 2: Closure Authority
**The prompt user (stakeholder) has final authority over issue closure.**

- ✅ **Correct**: Implement, demonstrate, then ask "Ready to close?"
- ✅ **Also Correct**: Wait for explicit closure approval
- ❌ **Wrong**: Auto-closing issues after implementation
- ❌ **Wrong**: Closing without asking for approval first

### Rule 3: Permission Matrix
```
User says nothing about implementation
  → Check issue description and context
  → If clear and unambiguous → IMPLEMENT
  → If unclear → ASK for clarification

User explicitly permits implementation
  → IMPLEMENT immediately without asking

User explicitly restricts implementation
  → WAIT for approval before implementing

Implementation complete
  → ALWAYS ask for closure approval
  → WAIT for explicit "yes" before closing
```

## Workflow Examples

### Example 1: Feature Request (No Implementation Restrictions)
```
Issue: "Add tab completion for empty input"
(User prompt has no restrictions like "don't implement" or "ask first")

1. ANALYZE: User wants help display when pressing TAB on empty line
2. PROPOSE: Comment with implementation plan - "I'll modify the API to return help text..."
3. IMPLEMENT: Build the feature immediately (no permission required)
   - Update server API
   - Update client JavaScript
   - Write tests
4. DEMONSTRATE: "Tab completion now shows help. All requirements met."
5. REQUEST CLOSURE: "Ready to close this issue?"
6. WAIT: For user confirmation
7. CLOSE: Only after user confirms
```

### Example 2: Complex Feature (With Restrictions)
```
Issue: "Implement new verb system"
User says: "Design this first and ask before implementing"

1. ANALYZE: Assess the requirements
2. PROPOSE: Detailed comment with architecture and design
3. WAIT: User reviews and provides feedback (restrictions honored)
4. IMPLEMENT: Only after user approves the design
5. DEMONSTRATE: Show working implementation
6. REQUEST CLOSURE: "Ready to close this issue?"
7. WAIT: For user confirmation
8. CLOSE: Only after user confirms
```

### Example 3: Security/Critical Fix (Explicit Request)
```
Issue: "Critical: Fix command injection vulnerability"
User says: "Implement immediately"

1. ANALYZE: Quick security assessment
2. PROPOSE: Brief comment with fix plan
3. IMPLEMENT: Start immediately (user explicitly requested it)
   - Apply security fix
   - Add tests for vulnerability
   - Deploy to production
4. DEMONSTRATE: "Security fix applied and deployed. All tests pass."
5. REQUEST CLOSURE: "Ready to close this issue?"
6. WAIT: For user confirmation
7. CLOSE: Only after user confirms
```

### Example 4: Ambiguous Issue (Ask for Clarification)
```
Issue: "Improve the parser"
(Vague and no implementation restrictions mentioned, but unclear what "improve" means)

1. ANALYZE: Requirement is unclear
2. PROPOSE: Ask clarifying questions in a comment:
   - "What specific parsing issues should be fixed?"
   - "What are the main pain points?"
   - "Can you provide examples?"
3. WAIT: For user to clarify
4. Once clarified, follow Example 1 or 2 based on restrictions
```

## Best Practices

### Analysis Phase
- Check the user prompt for explicit implementation restrictions
- Ask clarifying questions early if requirements are unclear
- Consider user experience impact
- Review related issues and PRs
- Document any assumptions

### Implementation Phase
- Follow established coding standards
- Use semantic versioning for releases
- Test on both local and development environments
- Document any configuration changes needed
- Commit messages should reference the issue number

### Communication
- **Key**: Check for user restrictions BEFORE proceeding
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
- Tests pass locally and in CI

## Issue States

- **Open** - Issue identified, awaiting analysis
- **In Progress** - Planning/implementation underway
- **Review** - Implementation complete, awaiting closure approval
- **Closed** - Approved and resolved by stakeholder

## Documentation Requirements

- Link to relevant commits and PRs
- Include before/after examples where applicable
- Update related documentation if functionality changes
- Tag releases with issue references for traceability
- Document any breaking changes

## Success Criteria

- ✅ Original issue requirements fully met
- ✅ Implementation respects user's stated restrictions
- ✅ No regression in existing functionality
- ✅ Implementation tested and verified
- ✅ Documentation updated as needed
- ✅ **Issue closed only after explicit user approval**

## Common Patterns

### Pattern 1: "Implement This Issue"
User explicitly asks to implement → PROCEED immediately without asking permission first.

### Pattern 2: "Design First, Then Ask"
User wants to review design before implementation → WAIT after Step 2, ask for approval before Step 4.

### Pattern 3: "Just Do It"
User wants immediate implementation with minimal discussion → PROCEED without waiting between steps.

### Pattern 4: "Uncertain What to Do"
Issue is ambiguous → ASK clarifying questions in Step 2, then proceed based on answer.

## Summary Table

| Step | Who Decides | What Happens |
|------|-------------|--------------|
| 1-2: Analyze & Design | AI Agent | Plan the solution |
| 3: Propose | AI Agent | Comment with plan |
| **4: Implement** | **Check user prompt** | **Implement if allowed, wait if restricted** |
| 5: Demonstrate | AI Agent | Show working solution |
| 6: Request Closure | AI Agent | Ask for approval |
| 7: Close | User/Stakeholder | Explicit approval required |

## Key Difference from Previous Workflow

**Before**: Always wait for permission before implementing
**Now**: Implement immediately unless user explicitly restricts it

This change respects the principle that implementation is generally safe after a good design review, and the user can always request design review first if needed.
