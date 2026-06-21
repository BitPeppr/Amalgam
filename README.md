# Amalgam

If you're anything like me, towards the end of your projects, you're always querying multiple (5+) llm models at the same time, hoping to catch the last of the tiny issues, and trying to get the best out of every llm. But having seven opencode instances in numerous ghostty windows is messy, screen-constrained, and for my humble laptop, resource intensive. Amalgam aims to solve this by quering multiple llms at the same time (with multiple instances of the same model at different temperatures) and then merging the results together, giving you the best of all worlds in one place. Highly customisable, with cli flags covering temperatures, number of models, timeout, preview lengths, and more. Enjoy!

## Installation

```bash
pip install amalgam
```

## Usage

```bash
amalgam --key <your key> --timeout 120 --max_temperature 1 'What is life?'
```
