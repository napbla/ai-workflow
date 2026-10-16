# migrate

Reserved for semantic migration of existing repositories to the target `ai-workflow` protocol.

Expected model:

```text
existing repository + target spec
            ↓
          LLM
            ↓
     migration plan
            ↓
  ambiguity escalation
            ↓
          apply
            ↓
         validate
```

This module should understand project meaning, not rely on a fixed legacy directory layout. It must not redefine the protocol; it consumes `../spec/`.

No migrator is implemented yet.
