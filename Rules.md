# Rules
This document contains the all the rules that must be followed while creating an agent using Crimson.

These rules will help define how the front end is implemented and how the values and identifiers are defined for, say, Intents, Entities, Input and Output Contexts, and so on.

*Note: There is no Inherent Order to the rules*

## `CR001` Input and Output Contexts identifiers must not start with and end with double hypens "__"
Tags: `Context Label`
Error: `Violation of Rule CR001`

Example of valid context identifiers:
```
subscribe_context
subscribe_context_follow_up
```
Examples of invalid context identifiers:
```
__welcome_context__
__subscribe_followup__
```
## `CR002`