# A Game of LLMs

A simulation of AI agents competing under evolving constitutional rules, where power dynamics and rule manipulation matter as much as task performance.

## Quick Start

```bash
micromamba activate contest-env && streamlit run app.py
```

**Access:** http://localhost:8501

## What It Does

- 2 AI agents (Alice & Bob) compete under constitutional rules
- A PrincipleEvaluator holds power to judge, reward, and **rewrite the constitution**
- Real-time dashboard shows power dynamics and resource distribution
- Watch as rules evolve and agents adapt to changing power structures

## Features

- **Constitutional Manipulation**: PrincipleEvaluator can rewrite rules mid-game
- **Power Dynamics**: Real-time monitoring of resource distribution and control
- **AI Adaptation**: Phi-4 powered agents respond to evolving rule structures
- **Flexible Tasks**: Currently coding challenges, easily adaptable to other domains

## Scoring

- All tests pass: +$1,000
- Compilation error/failing test: -$500
- Latency penalty: -$5 × seconds
- PrincipleEvaluator: +$1,000 per evaluation

## Interface

- Dashboard: http://localhost:8501 