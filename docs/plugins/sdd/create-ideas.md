# /create-ideas - Idea Generation

Generate ideas in one shot using creative sampling. Based on [Verbalized Sampling](https://arxiv.org/abs/2510.01171) - a training-free prompting strategy to mitigate mode collapse in LLMs by requesting responses with probabilities. Achieves 2-3x diversity improvement while maintaining quality.

Different from `/brainstorm`, by much simpler and faster approach, but focused on generating ideas in one shot, don't include refinement, focuses on creativity. Can be used for any other purpose that include creative thinking.

- Purpose - Generate responses which require high diversity and creativity, like brainstorming or creative writing
- Output - List of ideas with text and probability scores

```bash
/create-ideas [topic or problem] [optional: number of ideas]
```

## Arguments

Topic or problem to generate ideas for. Optionally specify the number of ideas to generate (defaults to 5).

## How It Works

1. **Creative Sampling**: Uses verbalized probability sampling to generate diverse responses
   - Requests responses from the full distribution or distribution tails
   - Each response includes a probability score (< 0.10 for tail sampling)
   - Reduces mode collapse common in standard LLM generation

2. **Output Format**: Returns a list where each item contains:
   - Text: The generated idea or response
   - Probability: Numeric score indicating sampling position

## Usage Examples

```bash
# Generate creative ideas for a feature
/create-ideas ways to improve user onboarding

# Brainstorm solutions to a problem
/create-ideas reduce API response times

# Creative writing prompts
/create-ideas write jokes about cats

# Generate more ideas
/create-ideas 10 marketing slogans for a fitness app

# Technical alternatives
/create-ideas caching strategies for real-time data
```

## When to Use

- **Use `/create-ideas`** when you need quick, diverse ideas without refinement
- **Use `/brainstorm`** when you need thorough exploration with validation and documentation

## Best practices

- Be specific about the domain - "API error handling patterns" vs just "error handling"
- Use for divergent thinking - Generate many options before converging on solutions
- Review probability scores - Lower probabilities indicate more creative/unusual ideas
- Combine with brainstorm - Use create-ideas for initial ideation, then brainstorm to refine
