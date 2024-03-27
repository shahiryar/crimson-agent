# Rules
This document contains the all the rules that must be followed while creating an agent using Crimson.

These rules will help define how the front end is implemented and how the values and identifiers are defined for, say, Intents, Entities, Input and Output Contexts, and so on.

*Note: There is no Inherent Order to the rules*

## `CR001` Entity, Intents, Params, Contexts or any other User defined identifiers must not start as well as end with double hypens "__"
Tags: `User Defined Identifier`
Error: `Violation of Rule CR001`

Example of valid identifiers:
```
subscribe_intent
subscribe_context_follow_up
phone
phone_numer
name_
```
Examples of invalid context identifiers:
```
__welcome_context__
__subscribe_followup__
__context_label__
```
## `CR002`