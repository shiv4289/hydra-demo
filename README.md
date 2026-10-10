# hydra-demo

A HydraFusion-style multi-model **broker** demo, built with GitHub Spec Kit to learn
Spec-Driven Development.

- New to SDD? Read **[PLAYBOOK.md](PLAYBOOK.md)** and work through it on `main`.
- Want the finished thing? `git checkout 001-hydra-broker` and see its README.

The broker looks like one OpenAI-compatible model. The `model` name picks a strategy:

| model | strategy | analogy |
|---|---|---|
| `hydra-route` | classify difficulty → cheapest capable model | hospital triage nurse |
| `hydra-cascade` | cheap model first, escalate if not good enough | junior dev, senior reviews only when unsure |
| `hydra-fusion` | ask several in parallel, aggregator synthesizes | panel of experts + an editor |
